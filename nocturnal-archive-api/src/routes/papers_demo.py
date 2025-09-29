"""
Frozen Papers API - Public Demo Only
This is the stable, public demo version of the Papers API.
For commercial use, see FinSight vertical.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import structlog

from src.models.paper import SearchResult, Paper
from src.services.paper_search import PaperSearcher
from src.services.synthesizer import Synthesizer
from src.utils.error_handling import create_problem_response, get_error_type

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/api/papers", tags=["Papers Demo"])

# Initialize services
paper_searcher = PaperSearcher()
synthesizer = None  # Will be initialized with API key when needed

class PapersSearchRequest(BaseModel):
    query: str
    limit: int = Query(10, ge=1, le=50, description="Number of results to return (max 50 for demo)")
    sources: List[str] = ["openalex"]
    year_from: Optional[int] = None
    year_to: Optional[int] = None

class PapersSynthesizeRequest(BaseModel):
    paper_ids: List[str]
    max_words: int = Query(200, ge=50, le=500, description="Maximum words in summary (max 500 for demo)")
    style: str = Query("bullet_points", description="Summary style")

@router.post("/search", response_model=SearchResult)
async def search_papers(req: PapersSearchRequest, request: Request):
    """
    Search academic papers (Demo Version)
    
    This is the public demo version of the Papers API.
    For commercial use with higher limits and advanced features, 
    see the FinSight vertical.
    
    **Demo Limitations:**
    - Maximum 50 results per request
    - Basic search only (no advanced features)
    - Rate limited to 100 requests per month for free users
    """
    try:
        logger.info(
            "Papers demo search request received",
            query=req.query,
            limit=req.limit,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Demo rate limiting check
        if req.limit > 50:
            error_info = get_error_type("validation-error")
            return create_problem_response(
                request, 422,
                "validation-error", 
                "Demo limit exceeded", 
                "Demo version limited to 50 results per request. Upgrade to FinSight for higher limits.",
                limit=50
            )
        
        # Perform search
        results = await paper_searcher.search_papers(
            query=req.query,
            limit=req.limit,
            sources=req.sources,
            year_from=req.year_from,
            year_to=req.year_to
        )
        
        logger.info(
            "Papers demo search completed",
            results_count=len(results.papers),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Papers demo search failed",
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error", 
            "Search failed", 
            f"Search failed: {str(e)}"
        )

@router.post("/synthesize")
async def synthesize_papers(req: PapersSynthesizeRequest, request: Request):
    """
    Synthesize academic papers (Demo Version)
    
    This is the public demo version of the synthesis API.
    For commercial use with higher limits and advanced features, 
    see the FinSight vertical.
    
    **Demo Limitations:**
    - Maximum 500 words per summary
    - Basic synthesis only (no advanced features)
    - Rate limited to 100 requests per month for free users
    """
    try:
        logger.info(
            "Papers demo synthesis request received",
            paper_count=len(req.paper_ids),
            max_words=req.max_words,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Demo rate limiting check
        if req.max_words > 500:
            error_info = get_error_type("validation-error")
            return create_problem_response(
                request, 422,
                "validation-error", 
                "Demo limit exceeded", 
                "Demo version limited to 500 words per summary. Upgrade to FinSight for higher limits.",
                max_words=500
            )
        
        if len(req.paper_ids) > 10:
            error_info = get_error_type("validation-error")
            return create_problem_response(
                request, 422,
                "validation-error", 
                "Demo limit exceeded", 
                "Demo version limited to 10 papers per synthesis. Upgrade to FinSight for higher limits.",
                max_papers=10
            )
        
        # Initialize synthesizer if needed
        if synthesizer is None:
            from src.core.config import settings
            synthesizer = Synthesizer(settings.openai_api_key)
        
        # Perform synthesis
        result = await synthesizer.synthesize_papers(
            paper_ids=req.paper_ids,
            max_words=req.max_words,
            style=req.style
        )
        
        logger.info(
            "Papers demo synthesis completed",
            word_count=len(result.summary.split()),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Papers demo synthesis failed",
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error", 
            "Synthesis failed", 
            f"Synthesis failed: {str(e)}"
        )

@router.get("/demo-info")
async def demo_info():
    """
    Get demo information and limitations
    """
    return {
        "service": "Papers API Demo",
        "version": "1.0.0",
        "status": "public_demo",
        "limitations": {
            "search": {
                "max_results": 50,
                "rate_limit": "100 requests per month"
            },
            "synthesis": {
                "max_words": 500,
                "max_papers": 10,
                "rate_limit": "100 requests per month"
            }
        },
        "upgrade": {
            "commercial_version": "FinSight",
            "description": "For higher limits and advanced features, see the FinSight vertical",
            "contact": "contact@nocturnal.dev"
        }
    }
