"""
Finance API routes for numeric-grounded synthesis
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

from src.finance.grounding import ground_claims, Evidence, NumericClaim, TimeSeries

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
    evidence = []
    
    if req.grounded:
        # Verify all claims against time series data
        ev, all_ok = ground_claims(
            [NumericClaim(**c.model_dump()) for c in req.claims],
            [TimeSeries(**s.model_dump()) for s in req.context.series]
        )
        evidence = ev
        
        if not all_ok:
            from src.utils.error_handling import create_problem_response, get_error_type
            error_info = get_error_type("claims-not-grounded")
            return create_problem_response(
                request, 422,
                "claims-not-grounded", error_info["title"], error_info["detail"],
                evidence=[e.model_dump() for e in ev]
            )
    
    # TODO: Call LLM for synthesis with verified claims
    # For now, return a placeholder response
    summary = f"Financial analysis based on {len(req.context.series)} time series with {len(req.claims)} verified claims."
    
    return {
        "summary": summary,
        "evidence": [e.model_dump() for e in evidence],
        "grounded": req.grounded,
        "claims_verified": len([e for e in evidence if e.supported]),
        "total_claims": len(evidence)
    }

@router.post("/verify-claims")
async def verify_claims_only(req: FinanceSynthRequest):
    """
    Verify claims without synthesis - useful for testing
    """
    ev, all_ok = ground_claims(
        [NumericClaim(**c.model_dump()) for c in req.claims],
        [TimeSeries(**s.model_dump()) for s in req.context.series]
    )
    
    return {
        "all_verified": all_ok,
        "evidence": [e.model_dump() for e in ev],
        "verified_count": len([e for e in ev if e.supported]),
        "total_claims": len(ev)
    }
