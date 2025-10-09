"""
Finance API routes for numeric-grounded synthesis
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import structlog

from src.finance.grounding import ground_claims, Evidence, NumericClaim, TimeSeries

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/api/finance", tags=["Finance"])

class FinanceContext(BaseModel):
    series: List[TimeSeries]

class FinanceSynthRequest(BaseModel):
    context: FinanceContext
    claims: List[NumericClaim]
    grounded: bool = True
    max_words: int = 400
    style: str = "markdown"

@router.post("/synthesize")
async def synthesize_finance(req: FinanceSynthRequest, request: Request):
    """
    Synthesize finance data with numeric grounding
    
    - grounded=true: Every numeric claim must be verified against data
    - grounded=false: Allow unverified claims (not recommended for production)
    """
    logger.info(
        "Finance synthesis request",
        claims_count=len(req.claims),
        series_count=len(req.context.series),
        grounded=req.grounded,
        trace_id=getattr(request.state, "trace_id", "unknown")
    )
    
    evidence = []
    
    if req.grounded:
        # Verify all claims against time series data
        ev, all_ok = ground_claims(req.claims, req.context.series)
        evidence = ev
        
        if not all_ok:
            unverified = [e for e in ev if not e.supported]
            logger.warning(
                "Claims not grounded",
                unverified_count=len(unverified),
                total_claims=len(ev),
                trace_id=getattr(request.state, "trace_id", "unknown")
            )
            
            return {
                "error": "claims-not-grounded",
                "title": "Numeric claims verification failed",
                "detail": f"{len(unverified)} of {len(ev)} claims could not be verified against provided data",
                "evidence": [e.model_dump() for e in ev],
                "unverified_claims": [e.claim_id for e in unverified]
            }
    
    # All claims verified - generate synthesis
    summary = f"Financial analysis based on {len(req.context.series)} time series with {len(req.claims)} verified claims."
    
    # TODO: Call LLM for synthesis with verified claims
    # For now, return a structured response
    verified_count = len([e for e in evidence if e.supported]) if evidence else 0
    
    logger.info(
        "Finance synthesis completed",
        verified_claims=verified_count,
        total_claims=len(req.claims),
        trace_id=getattr(request.state, "trace_id", "unknown")
    )
    
    return {
        "summary": summary,
        "evidence": [e.model_dump() for e in evidence],
        "grounded": req.grounded,
        "claims_verified": verified_count,
        "total_claims": len(evidence),
        "timestamp": getattr(request.state, "trace_id", "unknown")
    }

@router.post("/verify-claims")
async def verify_claims_only(req: FinanceSynthRequest, request: Request):
    """
    Verify claims without synthesis - useful for testing
    """
    logger.info(
        "Claims verification request",
        claims_count=len(req.claims),
        series_count=len(req.context.series),
        trace_id=getattr(request.state, "trace_id", "unknown")
    )
    
    ev, all_ok = ground_claims(req.claims, req.context.series)
    
    verified_count = len([e for e in ev if e.supported])
    unverified = [e for e in ev if not e.supported]
    
    logger.info(
        "Claims verification completed",
        all_verified=all_ok,
        verified_count=verified_count,
        total_claims=len(ev),
        trace_id=getattr(request.state, "trace_id", "unknown")
    )
    
    return {
        "all_verified": all_ok,
        "evidence": [e.model_dump() for e in ev],
        "verified_count": verified_count,
        "total_claims": len(ev),
        "unverified_claims": [{"claim_id": e.claim_id, "reason": e.details.get("reason")} for e in unverified]
    }

@router.get("/info")
async def finance_info():
    """Get information about finance synthesis capabilities"""
    return {
        "service": "Finance Synthesis",
        "version": "1.0.0",
        "capabilities": {
            "grounding": "Numeric claim verification against time series data",
            "operators": ["=", "<", "<=", ">", ">=", "change", "yoy", "qoq"],
            "frequencies": ["D", "W", "M", "Q", "A"],
            "features": [
                "Hallucination prevention",
                "Source tracing",
                "Evidence-based claims",
                "YoY and QoQ calculations",
                "Tolerance-based matching"
            ]
        },
        "usage": {
            "synthesize": "POST /v1/api/finance/synthesize - Generate grounded synthesis",
            "verify": "POST /v1/api/finance/verify-claims - Verify claims only"
        }
    }
