"""
Enhanced synthesis endpoint with performance optimizations
"""

import structlog
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from src.config.settings import Settings, get_settings
from src.models.request import SynthesizeRequest
from src.models.paper import SynthesisResult
from src.services.performance_integration import performance_integration
from src.utils.async_utils import resolve_awaitable
from src.engine.research_engine import sophisticated_engine

logger = structlog.get_logger(__name__)
router = APIRouter()


def _coerce_mapping(value):
    if isinstance(value, dict):
        return dict(value)
    data = {}
    for attr in (
        "summary",
        "key_findings",
        "citations_used",
        "word_count",
        "metadata",
        "routing_metadata",
        "relevance_score",
        "trace_id",
    ):
        if hasattr(value, attr):
            data[attr] = getattr(value, attr)
    if hasattr(value, "__dict__"):
        for key, val in value.__dict__.items():
            if not key.startswith("_") and key not in data:
                data[key] = val
    return data


@router.post("/synthesize", response_model=SynthesisResult)
async def synthesize_papers(
    request: SynthesizeRequest,
    enhance: bool = Query(True, description="Enable performance enhancements"),
    extract_insights: bool = Query(True, description="Extract research insights"),
    settings: Settings = Depends(get_settings)
):
    """Synthesize research findings across multiple papers with performance optimizations"""

    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Enhanced synthesis request received",
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus,
            style=request.style,
            enhance=enhance,
            extract_insights=extract_insights,
            trace_id=trace_id
        )
        
        if not sophisticated_engine.enhanced_synthesizer:
            logger.error("Advanced synthesis engine unavailable", trace_id=trace_id)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "advanced_engine_unavailable",
                    "message": "Sophisticated synthesis engine is not available",
                    "trace_id": trace_id,
                },
            )

        logger.info("Using sophisticated synthesis engine", trace_id=trace_id)
        advanced_result = await sophisticated_engine.synthesize_advanced(
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            style=request.style,
            context={
                "focus": request.focus,
                "custom_prompt": request.custom_prompt,
                "original_query": request.original_query,
                "trace_id": trace_id,
            },
        )

        advanced_data = _coerce_mapping(advanced_result)
        if "error" in advanced_data:
            logger.error(
                "Advanced synthesis failed",
                error=advanced_data.get("error"),
                trace_id=trace_id,
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "synthesis_failed",
                    "message": advanced_data.get("error", "Advanced synthesis failed"),
                    "trace_id": trace_id,
                },
            )

        routing_md = advanced_data.get("routing_metadata", {}) or {}
        result = SynthesisResult(
            summary=advanced_data.get("summary", ""),
            key_findings=advanced_data.get("key_findings", []),
            citations_used=advanced_data.get("citations_used", {}),
            word_count=advanced_data.get("word_count")
            or len(advanced_data.get("summary", "").split()),
            trace_id=advanced_data.get("trace_id", trace_id),
            model_used=(routing_md.get("routing_decision") or {}).get("model"),
            complexity=(routing_md.get("routing_decision") or {}).get("complexity"),
            token_usage=routing_md.get("usage"),
            metadata=advanced_data.get("metadata", {}),
            relevance_score=advanced_data.get("relevance_score"),
        )
        
        # Apply performance enhancements if requested (attach in a separate field not in model)
        enhanced_metadata = dict(result.metadata or {})
        if enhance:
            logger.info("Applying synthesis enhancements", trace_id=trace_id)
            papers_data = [
                {"id": pid, "title": f"Paper {pid}", "abstract": "Sample abstract"}
                for pid in request.paper_ids
            ]
            enhancement = _coerce_mapping(
                await resolve_awaitable(
                    performance_integration.enhance_synthesis(papers_data, result.summary)
                )
            ) or {}
            enhanced_metadata.update(enhancement)
        
        # Extract insights if requested (attach outside model)
        if extract_insights:
            logger.info("Extracting synthesis insights", trace_id=trace_id)
            papers_data = [{"id": pid, "title": f"Paper {pid}", "abstract": "Sample abstract"} for pid in request.paper_ids]
            insights = await resolve_awaitable(
                performance_integration.extract_research_insights(papers_data)
            )
            enhanced_metadata['insights'] = insights
        
        logger.info(
            "Enhanced synthesis completed",
            paper_count=len(request.paper_ids),
            word_count=result.word_count,
            enhanced=enhance,
            insights_extracted=extract_insights,
            trace_id=trace_id
        )
        
        # Optional relevance check
        relevance = None
        if request.original_query and isinstance(result.summary, str):
            terms = set(request.original_query.lower().split())
            blob = result.summary.lower()
            matches = sum(1 for t in terms if t in blob)
            relevance = (matches / max(1, len(terms)))

        # Return model plus optional metadata wrapper
        # routing_md already set above from advanced_result or basic
        if enhanced_metadata is None:
            enhanced_metadata = {}
        enhanced_metadata["routing_metadata"] = routing_md
        enhanced_metadata["synthesis_mode"] = enhanced_metadata.get("synthesis_mode", "smart")

        # Also expose top-level quick-inspect fields
        routing_decision = routing_md.get("routing_decision", {}) if isinstance(routing_md, dict) else {}
        model_used = routing_decision.get("model", "unknown")
        complexity = routing_decision.get("complexity", "unknown")
        usage = routing_md.get("usage", {}) if isinstance(routing_md, dict) else {}

        return {
            "summary": result.summary,
            "key_findings": result.key_findings,
            "citations_used": result.citations_used,
            "word_count": result.word_count,
            "trace_id": result.trace_id,
            "model_used": model_used,
            "complexity": complexity,
            "token_usage": usage,
            "metadata": enhanced_metadata or {},
            **({"relevance_score": relevance} if relevance is not None else {})
        }
    
    except Exception as e:
        logger.error(
            "Enhanced synthesis failed",
            error=str(e),
            paper_ids=request.paper_ids,
            exc_info=True
        )
        # RFC 7807 style problem response
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://nocturnal.dev/problems/synthesis_failed",
                "title": "Synthesis failed",
                "status": 500,
                "detail": "Failed to synthesize papers",
                "instance": "/api/synthesize",
                "request_id": trace_id,
                "error": str(e)
            }
        )


@router.post("/synthesize/strict", response_model=SynthesisResult)
async def synthesize_papers_strict(
    request: SynthesizeRequest,
    settings: Settings = Depends(get_settings)
):
    """Strict synthesis requiring heavy model capability (70B+ models)"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Strict synthesis request received",
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus,
            style=request.style,
            trace_id=trace_id
        )
        
        if not sophisticated_engine.enhanced_synthesizer:
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://nocturnal.dev/problems/advanced_engine_unavailable",
                    "title": "Advanced engine unavailable",
                    "status": 503,
                    "detail": "Sophisticated synthesis engine is not available",
                    "instance": "/api/synthesize/strict",
                    "request_id": trace_id,
                },
            )

        result = await sophisticated_engine.synthesize_strict(
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            style=request.style,
            context={"focus": request.focus, "trace_id": trace_id},
        )

        result_data = _coerce_mapping(result)
        if "error" in result_data:
            logger.warning(
                "Strict synthesis failed",
                trace_id=trace_id,
                error=result_data.get("error"),
            )
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://nocturnal.dev/problems/insufficient_model_capability",
                    "title": "Insufficient model capability",
                    "status": 503,
                    "detail": result_data.get("error", "Strict synthesis is unavailable"),
                    "instance": "/api/synthesize/strict",
                    "request_id": trace_id,
                    "fallback_suggestion": "Use /api/synthesize or reduce max_words/paper_count",
                },
            )

        routing_md = result_data.get("routing_metadata", {}) if isinstance(result_data, dict) else {}
        routing_decision = routing_md.get("routing_decision", {}) if isinstance(routing_md, dict) else {}

        synthesis_result = SynthesisResult(
            summary=result_data.get("summary", ""),
            key_findings=result_data.get("key_findings", []),
            citations_used=result_data.get("citations_used", {}),
            word_count=result_data.get("word_count", 0),
            trace_id=result_data.get("trace_id", trace_id),
            model_used=routing_decision.get("model"),
            complexity=routing_decision.get("complexity"),
            token_usage=routing_md.get("usage"),
            metadata=result_data.get("metadata", {}),
        )

        enhanced_metadata = dict(synthesis_result.metadata or {})
        enhanced_metadata.update(
            {
                "synthesis_mode": "strict",
                "routing_metadata": routing_md,
                "papers_synthesized": result_data.get("papers_synthesized", len(request.paper_ids)),
            }
        )

        logger.info(
            "Strict synthesis completed",
            paper_count=len(request.paper_ids),
            word_count=synthesis_result.word_count,
            model_used=routing_decision.get("model", "unknown"),
            trace_id=trace_id,
        )

        return {
            "summary": synthesis_result.summary,
            "key_findings": synthesis_result.key_findings,
            "citations_used": synthesis_result.citations_used,
            "word_count": synthesis_result.word_count,
            "trace_id": synthesis_result.trace_id,
            "model_used": routing_decision.get("model", "unknown"),
            "complexity": routing_decision.get("complexity", "unknown"),
            "token_usage": routing_md.get("usage", {}),
            "metadata": enhanced_metadata,
        }
    
    except Exception as e:
        logger.error(
            "Strict synthesis failed",
            error=str(e),
            paper_ids=request.paper_ids,
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://nocturnal.dev/problems/strict_synthesis_failed",
                "title": "Strict synthesis failed",
                "status": 500,
                "detail": "Failed to synthesize papers with strict model requirements",
                "instance": "/api/synthesize/strict",
                "request_id": trace_id,
                "error": str(e)
            }
        )


@router.post("/synthesize/stream")
async def synthesize_papers_stream(
    request: SynthesizeRequest,
    enhance: bool = Query(True, description="Enable performance enhancements"),
    settings: Settings = Depends(get_settings)
):
    """Stream synthesis results in real-time"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Streaming synthesis request received",
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            enhance=enhance,
            trace_id=trace_id
        )
        
        # This would implement streaming synthesis
        # For now, return a placeholder response
        return {
            "message": "Streaming synthesis feature coming soon",
            "trace_id": trace_id,
            "status": "development"
        }
    
    except Exception as e:
        logger.error(f"Streaming synthesis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "streaming_synthesis_failed",
                "message": "Failed to stream synthesis"
            }
        )


@router.get("/synthesize/status/{synthesis_id}")
async def get_synthesis_status(
    synthesis_id: str,
    settings: Settings = Depends(get_settings)
):
    """Get status of a synthesis job"""
    
    try:
        # This would check the status of a synthesis job
        # For now, return a placeholder response
        return {
            "synthesis_id": synthesis_id,
            "status": "completed",
            "progress": 100,
            "message": "Status tracking feature coming soon"
        }
    
    except Exception as e:
        logger.error(f"Failed to get synthesis status for {synthesis_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "status_failed",
                "message": "Failed to retrieve synthesis status"
            }
        )
