"""Citation formatting routes."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from uuid import uuid4

from src.models.request import FormatRequest
from src.services.citation_formatter import CitationFormatter

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/format")
async def format_papers(request: FormatRequest):
    """Format a collection of papers using the requested citation style."""
    formatter = CitationFormatter()

    try:
        formatted = await formatter.format_papers(
            paper_ids=request.paper_ids,
            style=request.style,
            options=request.options,
        )
    except ValueError as exc:
        logger.warning("format_request_invalid", error=str(exc), style=request.style)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {
        "formatted": formatted,
        "format": request.style,
        "count": len(request.paper_ids),
        "trace_id": f"format-{uuid4().hex}",
    }
    logger.info(
        "format_request_success",
        style=request.style,
        paper_count=len(request.paper_ids),
        trace_id=response["trace_id"],
    )
    return response
