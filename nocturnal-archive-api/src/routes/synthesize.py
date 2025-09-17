"""
Synthesize endpoint
"""

import structlog
import uuid
from fastapi import APIRouter, Depends, HTTPException

from src.config.settings import Settings, get_settings
from src.models.request import SynthesizeRequest
from src.models.paper import SynthesisResult
from src.services.synthesizer import Synthesizer

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/synthesize", response_model=SynthesisResult)
async def synthesize_papers(
    request: SynthesizeRequest,
    settings: Settings = Depends(get_settings)
):
    """Synthesize research findings across multiple papers"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Synthesize request received",
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus,
            style=request.style,
            trace_id=trace_id
        )
        
        # Initialize synthesizer
        synthesizer = Synthesizer(settings.openai_api_key)
        
        # Perform synthesis
        result = await synthesizer.synthesize_papers(
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus,
            style=request.style,
            custom_prompt=request.custom_prompt
        )
        
        # Add trace ID to result
        result.trace_id = trace_id
        
        logger.info(
            "Synthesis completed",
            paper_count=len(request.paper_ids),
            word_count=result.word_count,
            trace_id=trace_id
        )
        
        return result
    
    except Exception as e:
        logger.error(
            "Synthesis failed",
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
