"""
Search endpoint
"""

import structlog
import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.config.settings import Settings, get_settings
from src.models.request import SearchRequest
from src.models.paper import SearchResult, Paper, Author
from src.services.paper_search import PaperSearcher

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResult)
async def search_papers(
    request: SearchRequest,
    settings: Settings = Depends(get_settings)
):
    """Search academic papers from trusted sources"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Search request received",
            query=request.query,
            limit=request.limit,
            sources=request.sources,
            trace_id=trace_id
        )
        
        # Initialize paper searcher
        searcher = PaperSearcher(settings.openalex_api_key)
        
        # Perform search
        papers = await searcher.search_papers(
            query=request.query,
            limit=request.limit,
            sources=request.sources,
            filters=request.filters
        )
        
        # Generate query ID
        query_id = f"q_{uuid.uuid4().hex[:8]}"
        
        logger.info(
            "Search completed",
            query_id=query_id,
            results_count=len(papers),
            trace_id=trace_id
        )
        
        return SearchResult(
            papers=papers,
            count=len(papers),
            query_id=query_id,
            trace_id=trace_id
        )
    
    except Exception as e:
        logger.error(
            "Search failed",
            error=str(e),
            query=request.query,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": "Failed to search papers",
                "trace_id": trace_id
            }
        )
