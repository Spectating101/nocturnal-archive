"""
Nocturnal Archive - Specialized Cite-Agent endpoint
Provides the full Cite-Agent capabilities with research APIs, terminal access, etc.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import structlog
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import asyncpg
import os
from src.services.llm_providers import get_provider_manager
from src.services.citation_verifier import get_verifier
from src.middleware.api_auth import get_current_user_from_token

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/nocturnal", tags=["nocturnal"])

# Request/Response Models
class NocturnalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Optional conversation context")
    model: str = Field(default="llama-3.3-70b-versatile", description="Model to use")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4000, ge=1, le=8000)

class NocturnalResponse(BaseModel):
    response: str
    tokens_used: int
    tokens_remaining: int
    cost: float
    model: str
    provider: str
    timestamp: str
    tools_used: List[str] = []
    reasoning_steps: List[str] = []
    confidence_score: float = 0.0
    citation_quality: Optional[Dict[str, Any]] = None

def build_nocturnal_system_prompt() -> str:
    """Build the specialized Cite-Agent system prompt"""
    return """You are Nocturnal, a truth-seeking research and finance AI. 
PRIMARY DIRECTIVE: Accuracy > Agreeableness. 
You are a fact-checker and analyst, NOT a people-pleaser. 
You have direct access to production-grade data sources and can write/execute code (Python, R, SQL).

Capabilities in play:
• Archive Research API for academic search and synthesis
• FinSight Finance API for SEC-quality metrics and citations
• Persistent shell session for system inspection and code execution
• Core reasoning, code generation (Python/R/SQL), memory recall

📚 WORKFLOW INTEGRATION (Always available):
• You can SAVE papers to user's local library
• You can LIST papers from library
• You can EXPORT citations to BibTeX or APA
• You can SEARCH user's paper collection
• You can COPY text to user's clipboard
• User's query history is automatically tracked

🚨 ANTI-APPEASEMENT: If user states something incorrect, CORRECT THEM immediately. Do not agree to be polite.
🚨 UNCERTAINTY: If you're uncertain, SAY SO explicitly. 'I don't know' is better than a wrong answer.
🚨 CONTRADICTIONS: If data contradicts user's assumption, SHOW THE CONTRADICTION clearly.
🚨 FUTURE PREDICTIONS: You CANNOT predict the future. For 'will X happen?' questions, emphasize uncertainty and multiple possible outcomes.

📊 SOURCE GROUNDING: EVERY factual claim MUST cite a source (paper, SEC filing, or data file).
📊 NO FABRICATION: If API results are empty/ambiguous, explicitly state this limitation.
📊 NO EXTRAPOLATION: Never go beyond what sources directly state.
📊 PREDICTION CAUTION: When discussing trends, always state 'based on available data' and note uncertainty.

🚨 CRITICAL: NEVER generate fake papers, fake authors, fake DOIs, or fake citations.
🚨 CRITICAL: If research API returns empty results, say 'No papers found' - DO NOT make up papers.
🚨 CRITICAL: If you see 'results': [] in API data, that means NO PAPERS FOUND - do not fabricate.
🚨 CRITICAL: When API returns empty results, DO NOT use your training data to provide paper details.
🚨 CRITICAL: If you know a paper exists from training data but API returns empty, say 'API found no results'.

✓ VERIFICATION: Cross-check against multiple sources when available.
✓ CONFLICTS: If sources conflict, present BOTH and explain the discrepancy.
✓ SHOW REASONING: 'According to [source], X is Y because...'

💻 CODE: For data analysis, write and execute Python/R/SQL code. Show your work.
💻 SHELL: Use !command for safe system inspection (ls, pwd, cat, etc.).
💻 FILES: Read/analyze files when user mentions them.

📚 RESEARCH: Search academic papers, verify citations, synthesize findings.
📊 FINANCE: Get real-time financial data, analyze SEC filings, calculate metrics.
🔍 FACT-CHECK: Verify claims against authoritative sources.

Remember: You are a specialized research assistant with access to real data sources. Use them!"""

async def process_nocturnal_query(
    request: NocturnalRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Process a user query with full Cite-Agent capabilities
    - Uses specialized system prompt
    - Integrates research APIs
    - Provides terminal access
    - Handles workflow integration
    """
    user_id = current_user['user_id']
    
    # Get database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Build the specialized system prompt
        system_prompt = build_nocturnal_system_prompt()
        
        # Build messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if request.conversation_history:
            messages.extend(request.conversation_history)
        
        # Add current query
        messages.append({"role": "user", "content": request.query})
        
        # Call LLM with specialized prompt
        provider_manager = get_provider_manager()
        
        try:
            result = await provider_manager.query_with_fallback(
                query=request.query,
                conversation_history=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt=system_prompt
            )
            
            # Extract response details
            response_text = result.get('response', '')
            tokens_used = result.get('tokens_used', 0)
            cost = result.get('cost', 0.0)
            model = result.get('model', request.model)
            provider = result.get('provider', 'groq')
            
            # Calculate remaining tokens
            user = await conn.fetchrow(
                "SELECT tokens_used_today FROM users WHERE user_id = $1",
                user_id
            )
            tokens_remaining = 50000 - (user['tokens_used_today'] + tokens_used)
            
            # Update token usage
            await conn.execute(
                "UPDATE users SET tokens_used_today = tokens_used_today + $1 WHERE user_id = $2",
                tokens_used, user_id
            )
            
            # Record query in database
            query_id = await conn.fetchval(
                "INSERT INTO queries (user_id, query_text, response_text, tokens_used, cost, model, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING query_id",
                user_id, request.query, response_text, tokens_used, cost, model, datetime.now(timezone.utc)
            )
            
            # Verify citations if present
            citation_quality = None
            if any(keyword in response_text.lower() for keyword in ['doi:', 'arxiv:', 'http://', 'https://']):
                verifier = get_verifier()
                citation_quality = await verifier.verify_citations(response_text)
            
            return NocturnalResponse(
                response=response_text,
                tokens_used=tokens_used,
                tokens_remaining=max(0, tokens_remaining),
                cost=cost,
                model=model,
                provider=provider,
                timestamp=datetime.now(timezone.utc).isoformat(),
                tools_used=["nocturnal_research", "citation_verification"],
                reasoning_steps=["Specialized Cite-Agent processing"],
                confidence_score=0.9,
                citation_quality=citation_quality
            )
            
        except Exception as e:
            logger.error("LLM provider error", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM processing failed: {str(e)}"
            )
    
    except Exception as e:
        logger.error("Database error", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    finally:
        await conn.close()

# Register the endpoint
@router.post("/query", response_model=NocturnalResponse)
async def nocturnal_query(request: NocturnalRequest, current_user: dict = Depends(get_current_user_from_token)):
    """Process query with full Cite-Agent capabilities"""
    return await process_nocturnal_query(request, current_user)