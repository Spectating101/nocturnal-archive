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
from src.models.request import SearchFilters
from src.services.paper_search import PaperSearcher

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/api/papers", tags=["Papers Demo"])


class PapersSearchRequest(BaseModel):
    query: str
    limit: int = Query(10, ge=1, le=50, description="Number of results to return (max 50 for demo)")
    sources: List[str] = ["semantic_scholar", "openalex"]
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
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "validation-error",
                    "title": "Demo limit exceeded",
                    "detail": "Demo version limited to 50 results per request. Upgrade to FinSight for higher limits.",
                    "limit": 50
                }
            )
        
        # Build filters
        filters = None
        if req.year_from or req.year_to:
            filters = SearchFilters(
                year_min=req.year_from,
                year_max=req.year_to
            )
        
        # Perform search
        searcher = PaperSearcher()
        results = await searcher.search_papers(
            query=req.query,
            limit=req.limit,
            sources=req.sources,
            filters=filters
        )
        
        # Convert dict response to SearchResult
        if isinstance(results, dict):
            papers_data = results.get("papers", [])
            papers = [Paper(**p) if isinstance(p, dict) else p for p in papers_data]
            result = SearchResult(
                papers=papers,
                count=len(papers),
                query_id=f"demo_{req.query[:20]}"
            )
        else:
            result = results
        
        logger.info(
            "Papers demo search completed",
            results_count=len(result.papers) if hasattr(result, 'papers') else 0,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Papers demo search failed",
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": f"Search failed: {str(e)}"
            }
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
        
        # Demo rate limiting checks
        if req.max_words > 500:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "validation-error",
                    "title": "Demo limit exceeded",
                    "detail": "Demo version limited to 500 words per summary. Upgrade to FinSight for higher limits.",
                    "max_words": 500
                }
            )
        
        if len(req.paper_ids) > 10:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "validation-error",
                    "title": "Demo limit exceeded",
                    "detail": "Demo version limited to 10 papers per synthesis. Upgrade to FinSight for higher limits.",
                    "max_papers": 10
                }
            )
        
        # Import synthesizer
        try:
            from src.services.synthesizer import Synthesizer
            from src.config.settings import get_settings
            
            settings = get_settings()
            synthesizer = Synthesizer()
            
            # Perform synthesis
            result = await synthesizer.synthesize_papers(
                paper_ids=req.paper_ids,
                max_words=req.max_words,
                style=req.style
            )
            
            logger.info(
                "Papers demo synthesis completed",
                trace_id=getattr(request.state, "trace_id", "unknown")
            )
            
            return result
            
        except ImportError:
            # Fallback if synthesizer not available
            return {
                "summary": "Synthesis service temporarily unavailable. Please try again later.",
                "paper_ids": req.paper_ids,
                "max_words": req.max_words,
                "style": req.style,
                "status": "unavailable"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Papers demo synthesis failed",
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "synthesis_failed",
                "message": f"Synthesis failed: {str(e)}"
            }
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
