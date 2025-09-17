"""
Format endpoint
"""

import structlog
import uuid
from fastapi import APIRouter, Depends, HTTPException

from src.config.settings import Settings, get_settings
from src.models.request import FormatRequest
from src.models.response import FormatResponse
from src.services.citation_formatter import CitationFormatter

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/format", response_model=FormatResponse)
async def format_citations(
    request: FormatRequest,
    settings: Settings = Depends(get_settings)
):
    """Format citations in various styles"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Format request received",
            paper_ids=request.paper_ids,
            style=request.style,
            trace_id=trace_id
        )
        
        # Initialize citation formatter
        formatter = CitationFormatter()
        
        # Format citations
        formatted_citations = await formatter.format_papers(
            paper_ids=request.paper_ids,
            style=request.style,
            options=request.options
        )
        
        logger.info(
            "Format completed",
            count=len(request.paper_ids),
            style=request.style,
            trace_id=trace_id
        )
        
        return FormatResponse(
            formatted=formatted_citations,
            format=request.style,
            count=len(request.paper_ids),
            trace_id=trace_id
        )
    
    except Exception as e:
        logger.error(
            "Format failed",
            error=str(e),
            paper_ids=request.paper_ids,
            style=request.style,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "format_failed",
                "message": "Failed to format citations",
                "trace_id": trace_id
            }
        )
