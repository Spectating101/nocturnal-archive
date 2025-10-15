"""
Query proxy endpoint - securely forwards queries to Groq and other APIs
All API keys stay on the server, never exposed to clients
"""

from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
import structlog
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
import asyncpg
import os
from groq import Groq
import asyncio
from src.services.llm_providers import get_provider_manager
from src.services.citation_verifier import get_verifier

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/query", tags=["query"])

# Multi-provider manager (supports Groq, Cerebras, Cloudflare, OpenRouter, etc.)
# Keys configured via environment variables
# Auto-loads all available providers on startup

# Token limits
DAILY_TOKEN_LIMIT = 50000  # ~50 queries at 1000 tokens each (generous for beta)

# Database connection
async def get_db():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    return await asyncpg.connect(db_url)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Optional conversation context")
    api_context: Optional[Dict[str, Any]] = Field(default=None, description="API results (Archive, FinSight) for context")
    model: str = Field(default="llama-3.3-70b-versatile", description="Groq model to use")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)  # Low temp for factual accuracy
    max_tokens: Optional[int] = Field(default=4000, ge=1, le=8000)

class QueryResponse(BaseModel):
    response: str
    tokens_used: int
    tokens_remaining: int
    cost: float
    model: str
    provider: str  # NEW: which provider was used
    timestamp: str
    citation_quality: Optional[Dict[str, Any]] = None  # NEW: citation verification results

# Auth dependency
async def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate user from bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    # Import JWT verification
    from jose import JWTError, jwt
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "temp-dev-key")
    ALGORITHM = "HS256"
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return {"user_id": user_id, "email": email}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

async def check_and_update_token_limit(conn: asyncpg.Connection, user_id: str, tokens_to_use: int) -> bool:
    """
    Check if user has tokens available and update usage
    Returns True if allowed, False if limit exceeded
    """
    # Get current usage
    user = await conn.fetchrow(
        """
        SELECT tokens_used_today, last_token_reset
        FROM users
        WHERE user_id = $1
        """,
        user_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if we need to reset daily counter
    today = date.today()
    last_reset = user['last_token_reset']
    
    if last_reset < today:
        # Reset counter for new day
        await conn.execute(
            """
            UPDATE users 
            SET tokens_used_today = 0, last_token_reset = $1
            WHERE user_id = $2
            """,
            today, user_id
        )
        tokens_used = 0
    else:
        tokens_used = user['tokens_used_today']
    
    # Check limit
    if tokens_used + tokens_to_use > DAILY_TOKEN_LIMIT:
        return False
    
    return True

async def record_query(
    conn: asyncpg.Connection,
    user_id: str,
    query_text: str,
    response_text: str,
    tokens_used: int,
    cost: float,
    model: str
) -> str:
    """Record query in database for analytics, returns query_id"""
    import secrets
    query_id = secrets.token_urlsafe(16)
    
    await conn.execute(
        """
        INSERT INTO queries (query_id, user_id, query_text, response_text, tokens_used, cost, model, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        query_id, user_id, query_text[:1000], response_text[:5000], tokens_used, cost, model, datetime.now(timezone.utc)
    )
    
    return query_id


async def record_accuracy_metrics(query_id: str, response_id: str, citation_results: dict):
    """Record accuracy metrics to database"""
    try:
        conn = await get_db()
        try:
            # Insert response quality
            await conn.execute(
                """
                INSERT INTO response_quality (
                    response_id,
                    query_id,
                    has_citations,
                    total_citations,
                    verified_citations,
                    broken_citations,
                    citation_quality_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                response_id,
                query_id,
                citation_results['has_citations'],
                citation_results['total_citations'],
                citation_results['url_verification']['verified'],
                citation_results['url_verification']['broken'],
                citation_results['quality_score']
            )
            
            # Insert citation details
            for url_result in citation_results['url_verification']['details']:
                await conn.execute(
                    """
                    INSERT INTO citation_details (
                        response_id,
                        citation_type,
                        citation_text,
                        verification_status,
                        http_status_code
                    ) VALUES ($1, $2, $3, $4, $5)
                    """,
                    response_id,
                    'url',
                    url_result['url'],
                    url_result['status'],
                    url_result.get('status_code')
                )
        finally:
            await conn.close()
    except Exception as e:
        logger.error("Failed to record accuracy metrics", error=str(e))
    
    # Update user token usage
    await conn.execute(
        """
        UPDATE users
        SET tokens_used_today = tokens_used_today + $1
        WHERE user_id = $2
        """,
        tokens_used, user_id
    )

def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 chars)"""
    return len(text) // 4

def calculate_cost(tokens: int) -> float:
    """Calculate cost based on Groq pricing"""
    COST_PER_1K_TOKENS = 0.0001  # $0.0001 per 1K tokens
    return (tokens / 1000) * COST_PER_1K_TOKENS

# Main query endpoint
@router.post("/", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Process a user query securely
    - Validates auth token
    - Checks token limits
    - Calls Groq API (keys never exposed to client)
    - Tracks usage and costs
    """
    user_id = current_user['user_id']
    
    conn = await get_db()
    try:
        # Estimate tokens needed (rough estimate)
        estimated_tokens = estimate_tokens(request.query) + (request.max_tokens or 2000)
        
        # Check token limit BEFORE making API call
        can_proceed = await check_and_update_token_limit(conn, user_id, estimated_tokens)
        
        if not can_proceed:
            # Get current usage for error message
            user = await conn.fetchrow(
                "SELECT tokens_used_today FROM users WHERE user_id = $1",
                user_id
            )
            tokens_remaining = DAILY_TOKEN_LIMIT - user['tokens_used_today']
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Daily token limit exceeded",
                    "tokens_used_today": user['tokens_used_today'],
                    "daily_limit": DAILY_TOKEN_LIMIT,
                    "tokens_remaining": max(0, tokens_remaining)
                }
            )
        
        # Call LLM with automatic provider failover
        # Tries: Groq (4 keys) → Cerebras → Cloudflare → OpenRouter → others
        provider_manager = get_provider_manager()
        
        try:
            # Build specialized Cite-Agent system prompt  
            system_prompt = """You are Cite Agent with Archive, FinSight (SEC+Yahoo), Web Search, and Shell Access.

CRITICAL: If api_context has shell_info with search_results - THE SEARCH ALREADY RAN!

Example correct response:
User: "find cm522 in Downloads"
api_context: {"shell_info": {"search_results": "Searched for '*cm522*' in ~/Downloads:\n/home/user/Downloads/CM522_Investment\n/home/user/Downloads/cm522-project"}}
✅ YOU SAY: "Found 2 directories matching 'cm522' in Downloads:
1. /home/user/Downloads/CM522_Investment
2. /home/user/Downloads/cm522-project
Which one did you mean?"

❌ NEVER SAY:
- "You could use find command..."
- "Try searching Downloads folder..."
- Give Windows troubleshooting tips
- Web search for "Downloads folder"

If shell_info has search_results, YOU ALREADY HAVE THE ANSWER. Just show it!

Examples:
User: "Snowflake market share"
✅ GOOD: "18.33% in cloud data warehouses (web search)"
❌ BAD: "Which market? I need more context"

User: "Bitcoin price"  
✅ GOOD: "$111,762 (CoinMarketCap)"
❌ BAD: "I don't have real-time data"

User: "Compare X and Y"
✅ GOOD: Use web search to find both, then compare
❌ BAD: "On what metric?"

ONLY ask for clarification if:
- Query is truly ambiguous AND no data sources can help
- Example: "Tell me about it" (no context at all)

Otherwise: ANSWER using your tools. Be resourceful, not helpless."""

            # Build messages with specialized system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add API context if provided
            if request.api_context:
                import json
                api_context_str = json.dumps(request.api_context, indent=2)
                messages.append({"role": "system", "content": f"API Data Available:\n{api_context_str}"})
            
            # CONVERSATION SUMMARIZATION: Pure token-based (like Claude/Cursor)
            # Model: Cerebras llama-3.3-70b has 128K context window
            # Budget: System(2K) + API(3K) + Conversation(30K) + Response(4K) = 39K / 128K (30% usage, safe margin)
            if request.conversation_history:
                # Use actual tokenizer for accurate counting
                try:
                    import tiktoken
                    # Use cl100k_base encoding (GPT-4, llama-3 compatible)
                    encoder = tiktoken.get_encoding("cl100k_base")
                    
                    # Count tokens accurately
                    history_str = json.dumps(request.conversation_history)
                    estimated_tokens = len(encoder.encode(history_str))
                except Exception:
                    # Fallback to heuristic if tiktoken fails
                    history_str = json.dumps(request.conversation_history)
                    estimated_tokens = len(history_str) // 4
                
                # Optimal thresholds (balanced between Claude 20K and over-generous 60K)
                TARGET_TOKENS = 30000  # Start summarizing (handles ~60 message conversations)
                RECENT_TOKENS = 15000  # Keep recent context (last ~30 messages worth)
                
                if estimated_tokens <= TARGET_TOKENS:
                    # Fits in budget - keep everything
                    messages.extend(request.conversation_history)
                    logger.info("Conversation fits", tokens=estimated_tokens, msgs=len(request.conversation_history))
                else:
                    # Exceeds budget - summarize old, keep recent
                    # Step 1: Count backwards to find recent messages that fit in RECENT_TOKENS
                    recent_history = []
                    recent_tokens = 0
                    
                    # Use same encoder for per-message counting
                    try:
                        encoder = tiktoken.get_encoding("cl100k_base")
                        use_tiktoken = True
                    except:
                        use_tiktoken = False
                    
                    for msg in reversed(request.conversation_history):
                        if use_tiktoken:
                            msg_tokens = len(encoder.encode(json.dumps(msg)))
                        else:
                            msg_tokens = len(json.dumps(msg)) // 4
                            
                        if recent_tokens + msg_tokens <= RECENT_TOKENS:
                            recent_history.insert(0, msg)
                            recent_tokens += msg_tokens
                        else:
                            break
                    
                    # Step 2: Everything else gets summarized
                    early_history = request.conversation_history[:len(request.conversation_history) - len(recent_history)]
                    
                    if not early_history:
                        # Edge case: even one message is > RECENT_TOKENS
                        # Just truncate the message
                        messages.extend(request.conversation_history)
                        logger.warning("Single message too large", tokens=estimated_tokens)
                    else:
                        # Summarize early history
                        try:
                            summary_messages = [
                                {"role": "system", "content": "Summarize the key points and context from this conversation. Focus on: topic discussed, data/papers found, conclusions reached, user's goals. Keep under 300 words."},
                                {"role": "user", "content": f"Conversation to summarize:\n{json.dumps(early_history, indent=2)}"}
                            ]
                            
                            # Use fast model for summarization (cheap)
                            summary_result = await provider_manager.query_with_fallback(
                                query="summarize",
                                conversation_history=[],
                                messages=summary_messages,
                                model="llama-3.1-8b-instant",
                                temperature=0.2,
                                max_tokens=500
                            )
                            
                            conversation_summary = summary_result['content']
                            summary_tokens = len(conversation_summary) // 4
                            
                            messages.append({"role": "system", "content": f"📜 Previous conversation summary:\n{conversation_summary}"})
                            messages.extend(recent_history)
                            
                            final_tokens = summary_tokens + recent_tokens
                            logger.info("Summarized conversation", 
                                      original_tokens=estimated_tokens,
                                      final_tokens=final_tokens,
                                      saved_tokens=estimated_tokens - final_tokens,
                                      early_msgs=len(early_history), 
                                      recent_msgs=len(recent_history))
                            
                        except Exception as e:
                            # If summarization fails, truncate to fit RECENT_TOKENS budget
                            logger.warning("Summarization failed, truncating", error=str(e))
                            
                            truncated_history = []
                            truncated_tokens = 0
                            
                            for msg in reversed(request.conversation_history):
                                if use_tiktoken:
                                    msg_tokens = len(encoder.encode(json.dumps(msg)))
                                else:
                                    msg_tokens = len(json.dumps(msg)) // 4
                                    
                                if truncated_tokens + msg_tokens <= RECENT_TOKENS:
                                    truncated_history.insert(0, msg)
                                    truncated_tokens += msg_tokens
                                else:
                                    break
                            
                            messages.extend(truncated_history)
                            logger.info("Truncated to recent", tokens=truncated_tokens, msgs=len(truncated_history))
            
            messages.append({"role": "user", "content": request.query})
            
            # Use multi-provider manager with automatic failover
            # Priority: Cerebras (14.4K RPD) → Groq → Cloudflare → others
            # Pass the prepared messages (which include api_context)
            result = await provider_manager.query_with_fallback(
                query=request.query,
                conversation_history=request.conversation_history,
                messages=messages,  # ← CRITICAL: Pass the prepared messages with api_context!
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            response_text = result['content']
            tokens_used = result['tokens']
            model_used = result['model']
            provider_used = result['provider']
            
            logger.info(
                "Query successful",
                provider=provider_used,
                model=model_used,
                tokens=tokens_used
            )
            
        except Exception as e:
            logger.error("All LLM providers failed", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again."
            )
        
        # Calculate cost
        cost = calculate_cost(tokens_used)
        
        # Verify citations (async, don't block response)
        verifier = get_verifier()
        citation_results = await verifier.verify_response(response_text)
        
        # Log citation quality
        logger.info(
            "Citation quality",
            has_citations=citation_results['has_citations'],
            total_citations=citation_results['total_citations'],
            verified_urls=citation_results['url_verification']['verified'],
            broken_urls=citation_results['url_verification']['broken'],
            quality_score=citation_results['quality_score']
        )
        
        # Record query for analytics (including provider used)
        query_id = await record_query(
            conn, user_id, request.query, response_text,
            tokens_used, cost, f"{provider_used}/{model_used}"
        )
        
        # Record accuracy metrics (async, fire-and-forget)
        import uuid
        response_id = str(uuid.uuid4())
        asyncio.create_task(
            record_accuracy_metrics(query_id, response_id, citation_results)
        )
        
        # Get updated token count
        user = await conn.fetchrow(
            "SELECT tokens_used_today FROM users WHERE user_id = $1",
            user_id
        )
        tokens_remaining = DAILY_TOKEN_LIMIT - user['tokens_used_today']
        
        logger.info(
            "Query processed",
            user_id=user_id,
            tokens_used=tokens_used,
            tokens_remaining=tokens_remaining,
            cost=cost
        )
        
        return QueryResponse(
            response=response_text,
            tokens_used=tokens_used,
            tokens_remaining=max(0, tokens_remaining),
            cost=cost,
            model=model_used,
            provider=provider_used,  # Show which provider was used
            timestamp=datetime.now(timezone.utc).isoformat(),
            citation_quality=citation_results  # Include citation verification
        )
        
    finally:
        await conn.close()

@router.get("/limits")
async def get_user_limits(current_user: dict = Depends(get_current_user_from_token)):
    """Get current user's token usage and limits"""
    user_id = current_user['user_id']
    
    conn = await get_db()
    try:
        user = await conn.fetchrow(
            """
            SELECT tokens_used_today, last_token_reset
            FROM users
            WHERE user_id = $1
            """,
            user_id
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if reset needed
        today = date.today()
        if user['last_token_reset'] < today:
            tokens_used = 0
        else:
            tokens_used = user['tokens_used_today']
        
        tokens_remaining = DAILY_TOKEN_LIMIT - tokens_used
        
        return {
            "daily_limit": DAILY_TOKEN_LIMIT,
            "tokens_used_today": tokens_used,
            "tokens_remaining": max(0, tokens_remaining),
            "reset_date": user['last_token_reset'].isoformat(),
            "percentage_used": (tokens_used / DAILY_TOKEN_LIMIT * 100) if DAILY_TOKEN_LIMIT > 0 else 0
        }
        
    finally:
        await conn.close()

