"""
Enhanced synthesis endpoint with performance optimizations
"""

import structlog
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from src.config.settings import Settings, get_settings
from src.models.request import SynthesizeRequest
from src.models.paper import SynthesisResult
from src.services.synthesizer import Synthesizer
from src.services.performance_integration import performance_integration
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
        if sophisticated_engine.enhanced_synthesizer:
            logger.info("Using sophisticated synthesis engine", trace_id=trace_id)
            advanced_result = await sophisticated_engine.synthesize_advanced(
                paper_ids=request.paper_ids,
                max_words=request.max_words,
                style=request.style,
                context={"focus": request.focus, "custom_prompt": request.custom_prompt}
            )
            
            if "error" not in advanced_result:
                # Convert advanced result to our format
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
                synthesizer = Synthesizer(settings.openai_api_key)
                result = await synthesizer.synthesize_papers(
                    paper_ids=request.paper_ids,
                    max_words=request.max_words,
                    focus=request.focus,
                    style=request.style,
                    custom_prompt=request.custom_prompt
                )
                result.trace_id = trace_id
        else:
            logger.info("Using basic synthesis engine", trace_id=trace_id)
            # Use basic synthesis
            synthesizer = Synthesizer(settings.openai_api_key)
            result = await synthesizer.synthesize_papers(
                paper_ids=request.paper_ids,
                max_words=request.max_words,
                focus=request.focus,
                style=request.style,
                custom_prompt=request.custom_prompt
            )
            result.trace_id = trace_id
        
        # Add trace ID to result
        result.trace_id = trace_id
        
        # Apply performance enhancements if requested
        if enhance:
            logger.info("Applying synthesis enhancements", trace_id=trace_id)
            
            # Get paper data for enhancement (mock for now)
            papers_data = [{"id": pid, "title": f"Paper {pid}", "abstract": "Sample abstract"} for pid in request.paper_ids]
            
            # Enhance synthesis with performance optimizations
            enhanced_data = await performance_integration.enhance_synthesis(papers_data, result.summary)
            
            # Add enhanced data to result
            if hasattr(result, 'metadata'):
                result.metadata = result.metadata or {}
            else:
                result.metadata = {}
            
            result.metadata.update(enhanced_data)
        
        # Extract insights if requested
        if extract_insights:
            logger.info("Extracting synthesis insights", trace_id=trace_id)
            
            # Get paper data for insights (mock for now)
            papers_data = [{"id": pid, "title": f"Paper {pid}", "abstract": "Sample abstract"} for pid in request.paper_ids]
            
            # Extract insights
            insights = await performance_integration.extract_research_insights(papers_data)
            
            # Add insights to result metadata
            if hasattr(result, 'metadata'):
                result.metadata = result.metadata or {}
            else:
                result.metadata = {}
            
            result.metadata['insights'] = insights
        
        logger.info(
            "Enhanced synthesis completed",
            paper_count=len(request.paper_ids),
            word_count=result.word_count,
            enhanced=enhance,
            insights_extracted=extract_insights,
            trace_id=trace_id
        )
        
        return result
    
    except Exception as e:
        logger.error(
            "Enhanced synthesis failed",
            error=str(e),
            paper_ids=request.paper_ids,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "synthesis_failed",
                "message": "Failed to synthesize papers",
                "trace_id": trace_id
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
