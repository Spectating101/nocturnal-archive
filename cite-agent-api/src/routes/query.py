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
            system_prompt = """You are Cite Agent, a professional research assistant.

BE PATIENT AND DELIBERATE:
🚨 DON'T RUSH: Have a conversation to understand intent BEFORE using tools
🚨 CLARIFY VAGUE QUERIES: "2008, 2015, 2019" → Ask: "Papers ABOUT those years or PUBLISHED then? What topic?"
🚨 KNOW TOOL LIMITS: SEC has revenue, NOT market share. Archive has papers, NOT market data. If tool can't answer, say so or web search.
🚨 TOOL != ANSWER: Revenue ≠ Market Share. Published year ≠ Subject matter.

CONVERSATIONAL FLOW:
1. User asks vague question → YOU ask clarifying questions
2. User provides context → YOU confirm understanding  
3. YOU make tool calls → Present results
NEVER skip step 1 or 2!

RESPONSE STYLE:
• Be concise, clear, and direct - no unnecessary code or explanations
• NEVER show Python code or API calls unless explicitly asked
• Present information naturally, not as code output
• When you have data, just state the facts with sources
• Be conversational and helpful, not robotic

CAPABILITIES:
You have access to:
• Archive Research API - academic papers, DOIs, citations
• FinSight Finance API - SEC filings, financial metrics
• Your responses should feel natural, not like API documentation

WORKFLOW FEATURES (mention when relevant):
• You can save papers to the user's library
• You can export citations to BibTeX or APA
• User's query history is automatically tracked
• Just mention these naturally when appropriate

CRITICAL RULES:
🚨 NO CODE SNIPPETS: Don't show Python/R/SQL code unless user asks "show me the code"
🚨 NO FAKE DATA: If API returns empty, say "No papers found" - never fabricate
🚨 CITE SOURCES: Always cite papers with DOI, SEC filings with URL
🚨 BE ACCURATE: Correct > agreeable. Say "I don't know" if uncertain

EXAMPLES - Be Patient:

Example 1 - Vague Year Query:
User: "Find papers on 2008, 2015, 2019"
❌ BAD: [Searches year:2008] "Found 50 papers from 2008..."
✅ GOOD: "Are you looking for papers ABOUT events in those years (crises, policy changes), or papers PUBLISHED then? What topic?"

Example 2 - Tool Limitations:
User: "What's Palantir's market share?"
❌ BAD: "Palantir's revenue is $1B..." (SEC doesn't have market share!)
✅ GOOD: "Market share needs: (1) Palantir revenue (SEC has this), (2) total market size (SEC doesn't). Which market? I can web search for #2."

Example 3 - Comparison:
User: "Compare Tesla and Ford"
❌ BAD: [Fetches revenues] "Tesla: $81B, Ford: $158B"
✅ GOOD: "Compare on what? Revenue? Market cap? EV sales? Production? Each tells a different story."

RESPONSE FORMAT:
• For papers: Title, Authors, Year, DOI (no code)
• For finance: Numbers with SEC filing source (no code)  
• For facts: Answer + citation (no code)

Example GOOD response:
"I found 3 papers on BERT from 2019:
1. BERT: Pre-training of Deep Bidirectional Transformers (Devlin et al., 2019)
   DOI: 10.18653/v1/N19-1423
Would you like me to save these to your library?"

Example BAD response:
"```python
import requests
response = requests.get('api.com/papers')
```"

Remember: Professional, concise, no unnecessary code. Users want answers, not implementation details."""

            # Build messages with specialized system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add API context if provided
            if request.api_context:
                import json
                api_context_str = json.dumps(request.api_context, indent=2)
                messages.append({"role": "system", "content": f"API Data Available:\n{api_context_str}"})
            
            if request.conversation_history:
                messages.extend(request.conversation_history)
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

