"""
Enhanced synthesis endpoint with performance optimizations
"""

import structlog
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from src.config.settings import Settings, get_settings
from src.models.request import SynthesizeRequest
from src.models.paper import SynthesisResult
from src.services.synthesizer import Synthesizer
from src.services.performance_integration import performance_integration
from src.utils.async_utils import resolve_awaitable
from src.engine.research_engine import sophisticated_engine

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/synthesize", response_model=SynthesisResult)
async def synthesize_papers(
    request: SynthesizeRequest,
    enhance: bool = Query(True, description="Enable performance enhancements"),
    extract_insights: bool = Query(True, description="Extract research insights"),
    settings: Settings = Depends(get_settings)
):
    """Synthesize research findings across multiple papers with performance optimizations"""
    
    def _coerce_mapping(value):
        if isinstance(value, dict):
            return value
        data = {}
        for attr in ("summary", "key_findings", "citations_used", "word_count", "metadata", "routing_metadata"):
            if hasattr(value, attr):
                data[attr] = getattr(value, attr)
        if hasattr(value, "__dict__"):
            for key, val in value.__dict__.items():
                if not key.startswith("_") and key not in data:
                    data[key] = val
        return data

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
        
        # Try sophisticated synthesis first, fallback to basic synthesis
        routing_md = {}
        if sophisticated_engine.enhanced_synthesizer:
            logger.info("Using sophisticated synthesis engine", trace_id=trace_id)
            advanced_result = await sophisticated_engine.synthesize_advanced(
                paper_ids=request.paper_ids,
                max_words=request.max_words,
                style=request.style,
                context={"focus": request.focus, "custom_prompt": request.custom_prompt}
            )
            
            if isinstance(advanced_result, dict) and "error" not in advanced_result:
                # Convert advanced result to our format
                routing_md = advanced_result.get("routing_metadata", {}) if isinstance(advanced_result, dict) else {}
                result = SynthesisResult(
                    summary=advanced_result.get("summary", ""),
                    paper_ids=request.paper_ids,
                    max_words=request.max_words,
                    focus=request.focus,
                    style=request.style,
                    metadata=advanced_result.get("metadata", {}),
                    citations_used=advanced_result.get("citations_used", {}),
                    key_findings=advanced_result.get("key_findings", []),
                    trace_id=trace_id
                )
            else:
                logger.warning("Advanced synthesis failed, falling back to basic synthesis", 
                             error=advanced_result.get("error"), trace_id=trace_id)
                # Fallback to basic synthesis
                synthesizer = Synthesizer()
                basic = await resolve_awaitable(
                    synthesizer.synthesize_papers(
                    paper_ids=request.paper_ids,
                    max_words=request.max_words,
                    focus=request.focus,
                    style=request.style,
                    papers=request.papers
                    )
                )
                basic_data = _coerce_mapping(basic)
                routing_md = basic_data.get("routing_metadata", {})
                result = SynthesisResult(
                    summary=basic_data.get("summary", ""),
                    key_findings=basic_data.get("key_findings", []),
                    citations_used=basic_data.get("citations_used", {}),
                    word_count=basic_data.get("word_count", 0),
                    trace_id=trace_id
                )
        else:
            logger.info("Using basic synthesis engine", trace_id=trace_id)
            # Use basic synthesis
            synthesizer = Synthesizer()
            basic = await resolve_awaitable(
                synthesizer.synthesize_papers(
                paper_ids=request.paper_ids,
                max_words=request.max_words,
                focus=request.focus,
                style=request.style,
                papers=request.papers
                )
            )
            basic_data = _coerce_mapping(basic)
            routing_md = basic_data.get("routing_metadata", {})
            result = SynthesisResult(
                summary=basic_data.get("summary", ""),
                key_findings=basic_data.get("key_findings", []),
                citations_used=basic_data.get("citations_used", {}),
                word_count=basic_data.get("word_count", 0),
                trace_id=trace_id
            )
        
        # Add trace ID to result
        result.trace_id = trace_id
        
        # Apply performance enhancements if requested (attach in a separate field not in model)
        enhanced_metadata = {}
        if enhance:
            logger.info("Applying synthesis enhancements", trace_id=trace_id)
            papers_data = [{"id": pid, "title": f"Paper {pid}", "abstract": "Sample abstract"} for pid in request.paper_ids]
            enhanced_metadata = _coerce_mapping(
                await resolve_awaitable(
                    performance_integration.enhance_synthesis(papers_data, result.summary)
                )
            ) or {}
        
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
        
        # Use strict synthesis (requires heavy model)
        synthesizer = Synthesizer()
        result = await synthesizer.synthesize_papers_strict(
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus,
            style=request.style
        )
        
        # Check if synthesis failed due to model requirements
        if "error" in result and "heavy model" in result["error"]:
            logger.warning(
                "Strict synthesis failed - no heavy model available",
                trace_id=trace_id,
                error=result["error"]
            )
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://nocturnal.dev/problems/insufficient_model_capability",
                    "title": "Insufficient model capability",
                    "status": 503,
                    "detail": result["error"],
                    "instance": "/api/synthesize/strict",
                    "request_id": trace_id,
                    "fallback_suggestion": result.get("fallback_suggestion", "Try the regular /synthesize endpoint")
                }
            )
        
        # If strict could not secure heavy model, return 503
        routing_md = result.get("routing_metadata", {}) if isinstance(result, dict) else {}
        routing_decision = routing_md.get("routing_decision", {}) if isinstance(routing_md, dict) else {}
        if routing_decision.get("complexity") and routing_decision.get("complexity") != "heavy":
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://nocturnal.dev/problems/insufficient_model_capability",
                    "title": "Insufficient model capability",
                    "status": 503,
                    "detail": "Strict synthesis requires a heavy model (70B+).",
                    "instance": "/api/synthesize/strict",
                    "request_id": trace_id,
                    "fallback_suggestion": "Use /api/synthesize or reduce max_words/paper_count"
                }
            )

        # Convert to SynthesisResult
        synthesis_result = SynthesisResult(
            summary=result.get("summary", ""),
            key_findings=result.get("key_findings", []),
            citations_used=result.get("citations_used", {}),
            word_count=result.get("word_count", 0),
            trace_id=trace_id
        )
        
        # Add routing metadata
        enhanced_metadata = {
            "synthesis_mode": "strict",
            "routing_metadata": result.get("routing_metadata", {}),
            "papers_synthesized": result.get("papers_synthesized", 0)
        }
        
        logger.info(
            "Strict synthesis completed",
            paper_count=len(request.paper_ids),
            word_count=synthesis_result.word_count,
            model_used=result.get("routing_metadata", {}).get("routing_decision", {}).get("model", "unknown"),
            trace_id=trace_id
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
            "metadata": enhanced_metadata
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
