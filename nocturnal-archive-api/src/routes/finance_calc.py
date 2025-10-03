"""
Finance Calculations API Routes
Endpoints for metric calculations, explanations, and verification
"""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog

from src.calc.engine import CalculationEngine
from src.calc.registry import KPIRegistry
from src.calc.facts_store import get_facts_store
from src.facts.store import FactsStore
from src.utils.error_handling import create_problem_response, get_error_type
from datetime import datetime

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/finance/calc", tags=["Finance Calculations"])

# Global instances (would be injected in production)
kpi_registry = KPIRegistry()
facts_store = FactsStore()
calc_engine = CalculationEngine(facts_store, kpi_registry)

class CalcRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    expr: str = Field(..., description="Expression to evaluate")
    period: str = Field("latest", description="Period (e.g., '2024-Q4', 'latest')")
    freq: str = Field("Q", description="Frequency ('Q' for quarterly, 'A' for annual)")
    ttm: bool = Field(False, description="Calculate trailing twelve months")

class VerifyRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    expr: str = Field(..., description="Expression to verify")
    assert_value: str = Field(..., description="Expected value (e.g., '≈ 0.41')")
    tolerance: float = Field(0.01, description="Tolerance for comparison")
    period: str = Field("latest", description="Period to verify")
    freq: str = Field("Q", description="Frequency")

@router.get("/{ticker}/{metric}")
async def calculate_metric(
    ticker: str,
    metric: str,
    period: str = Query("latest", description="Period (e.g., '2024-Q4', 'latest')"),
    freq: str = Query("Q", description="Frequency ('Q' for quarterly, 'A' for annual)"),
    ttm: bool = Query(False, description="Calculate trailing twelve months"),
    segment: Optional[str] = Query(None, description="Business segment filter"),
    request: Request = None
):
    """
    Calculate a specific metric for a company
    
    Returns the calculated value with full breakdown and citations.
    """
    try:
        logger.info(
            "Finance metric calculation request",
            ticker=ticker,
            metric=metric,
            period=period,
            freq=freq,
            ttm=ttm,
            segment=segment,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Calculate metric
        result = await calc_engine.calculate_metric(
            ticker=ticker,
            metric=metric,
            period=period,
            freq=freq,
            ttm=ttm,
            segment=segment
        )
        
        # Build response
        response_data = {
            "ticker": result.ticker,
            "metric": result.metric,
            "period": result.period,
            "freq": result.freq,
            "value": result.value,
            "output_type": result.output_type.value,
            "formula": result.formula,
            "inputs": {
                input_name: {
                    "value": fact.value,
                    "unit": fact.unit,
                    "period": fact.period,
                    "concept": fact.concept,
                    "citation": {
                        "source_url": fact.url,
                        "accession": fact.accession,
                        "fragment_id": fact.fragment_id,
                        "dimensions": fact.dimensions
                    }
                }
                for input_name, fact in result.inputs.items()
            },
            "citations": result.citations,
            "quality_flags": result.quality_flags,
            "metadata": result.metadata
        }
        
        logger.info(
            "Finance metric calculation completed",
            ticker=ticker,
            metric=metric,
            value=result.value,
            flags_count=len(result.quality_flags),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except ValueError as e:
        logger.warning(
            "Finance metric calculation failed - validation error",
            ticker=ticker,
            metric=metric,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )

        # Parse error and provide helpful guidance
        error_msg = str(e)
        detail = error_msg
        extra_info = {}

        if "not found" in error_msg.lower() or "unknown metric" in error_msg.lower():
            detail = f"Metric '{metric}' not available for {ticker}. {error_msg}"
            extra_info["available_metrics"] = kpi_registry.list_metrics()[:15]
            extra_info["hint"] = "Choose from the available metrics list or try a custom expression via /explain"
            extra_info["example"] = f"/v1/finance/calc/{ticker}/revenue"
        elif "concept" in error_msg.lower():
            detail = f"Data concept issue: {error_msg}"
            extra_info["hint"] = f"SEC may not have this data for {ticker}. Try Yahoo Finance or recent filings."

        return create_problem_response(
            request, 422,
            "validation-error",
            "Calculation failed",
            detail,
            extra_info if extra_info else None
        )
        
    except Exception as e:
        logger.error(
            "Finance metric calculation failed",
            ticker=ticker,
            metric=metric,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
            request, 500,
            "internal-error",
            "Calculation failed",
            f"Internal error: {str(e)}"
        )

@router.get("/series/{ticker}/{metric}")
async def calculate_series(
    ticker: str,
    metric: str,
    freq: str = Query("Q", description="Frequency ('Q' for quarterly, 'A' for annual)"),
    limit: int = Query(12, ge=1, le=50, description="Maximum number of periods"),
    ttm: bool = Query(False, description="Calculate trailing twelve months"),
    segment: Optional[str] = Query(None, description="Business segment filter"),
    request: Request = None
):
    """
    Calculate a series of metric values over time
    
    Returns an array of calculated values with citations for each period.
    """
    try:
        logger.info(
            "Finance series calculation request",
            ticker=ticker,
            metric=metric,
            freq=freq,
            limit=limit,
            ttm=ttm,
            segment=segment,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Get facts store for real data
        facts_store = get_facts_store()
        
        # Get series data
        series_data = await facts_store.get_series(ticker, metric, freq, limit)
        
        if not series_data:
            return create_problem_response(
                request, 404,
                "not-found",
                "Metric not found",
                f"Unknown metric: {metric}"
            )
        
        # Build response
        response_data = {
            "ticker": ticker,
            "metric": metric,
            "freq": freq,
            "ttm": ttm,
            "series": series_data
        }
        
        logger.info(
            "Finance series calculation completed",
            ticker=ticker,
            metric=metric,
            periods_calculated=len(series_data),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Finance series calculation failed",
            ticker=ticker,
            metric=metric,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
            request, 500,
            "internal-error",
            "Series calculation failed",
            f"Internal error: {str(e)}"
        )

@router.post("/explain")
async def explain_expression(req: CalcRequest, request: Request):
    """
    Explain a custom expression with full breakdown

    Shows how "A = B - C" is calculated with citations for each input.
    Uses CalculationEngine for proper period matching.
    """
    try:
        logger.info(
            "Finance expression explanation request",
            ticker=req.ticker,
            expr=req.expr,
            period=req.period,
            freq=req.freq,
            ttm=req.ttm,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )

        # Use CalculationEngine which has period matching logic
        result = await calc_engine.explain_expression(
            ticker=req.ticker,
            expr=req.expr,
            period=req.period,
            freq=req.freq,
            ttm=req.ttm
        )


        # Format response with citations and breakdown
        input_terms = [
            {
                "concept": fact.concept,
                "value": fact.value,
                "accession": fact.accession,
                "unit": fact.unit,
                "scale": "U",
                "fx_used": None,
                "amended": False,
                "as_reported": True,
                "data_source": "sec_edgar"
            }
            for fact in result.inputs.values()
        ]

        response_data = {
            "ticker": result.ticker,
            "expr": result.formula,
            "period": result.period,
            "freq": result.freq,
            "value": result.value,
            "data_source": "sec_edgar",
            "formula": result.formula,
            "left": {
                "concept": "result",
                "value": result.value,
                "unit": "USD"
            },
            "right": {
                "terms": input_terms
            },
            "citations": [
                {
                    "concept": citation.get("concept", ""),
                    "value": citation.get("value", 0),
                    "unit": citation.get("unit", "USD"),
                    "period": citation.get("period", ""),
                    "source_url": citation.get("source_url", ""),
                    "accession": citation.get("accession", ""),
                    "fragment_id": citation.get("fragment_id"),
                    "dimensions": citation.get("dimensions", {})
                }
                for citation in result.citations
            ],
            "metadata": result.metadata
        }

        logger.info(
            "Finance expression explanation completed",
            ticker=req.ticker,
            expr=req.expr,
            value=result.value,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )

        return response_data
        
    except ValueError as e:
        # Parse common errors and provide helpful messages
        error_msg = str(e)
        detail = error_msg
        extra_info = {}

        if "Unsafe expression" in error_msg:
            detail = f"Expression validation failed. Check for typos in: '{req.expr}'"
            extra_info["hint"] = "Ensure all variable names are spelled correctly (revenue, costOfRevenue, etc.)"
        elif "not found" in error_msg.lower() or "unknown" in error_msg.lower():
            detail = f"Metric or concept not available for {req.ticker}. {error_msg}"
            extra_info["available_metrics"] = kpi_registry.list_metrics()[:10]
            extra_info["hint"] = "Try alternative metrics from the list above"
        elif "period" in error_msg.lower():
            detail = f"Period/date issue: {error_msg}"
            extra_info["hint"] = "Try 'latest' period or specific format like '2025-Q2'"

        return create_problem_response(
            request, 422,
            "validation-error",
            "Expression evaluation failed",
            detail,
            extra_info if extra_info else None
        )
        
    except Exception as e:
        logger.error(
            "Finance expression explanation failed",
            ticker=req.ticker,
            expr=req.expr,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
            request, 500,
            "internal-error",
            "Expression explanation failed",
            f"Internal error: {str(e)}"
        )

@router.post("/verify-expression")
async def verify_expression(req: VerifyRequest, request: Request):
    """
    Verify an expression against an expected value
    
    Checks if "A ≈ B" with specified tolerance and returns verification result.
    """
    try:
        logger.info(
            "Finance expression verification request",
            ticker=req.ticker,
            expr=req.expr,
            assert_value=req.assert_value,
            tolerance=req.tolerance,
            period=req.period,
            freq=req.freq,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Calculate actual value
        result = await calc_engine.explain_expression(
            ticker=req.ticker,
            expr=req.expr,
            period=req.period,
            freq=req.freq,
            ttm=False
        )
        
        # Parse expected value
        expected_value = float(req.assert_value.replace("≈", "").replace("=", "").strip())
        
        # Check tolerance
        difference = abs(result.value - expected_value)
        verified = difference <= req.tolerance
        
        response_data = {
            "verified": verified,
            "observed": result.value,
            "expected": expected_value,
            "difference": difference,
            "tolerance": req.tolerance,
            "expression": result.formula,
            "citations": result.citations,
            "quality_flags": result.quality_flags
        }
        
        logger.info(
            "Finance expression verification completed",
            ticker=req.ticker,
            expr=req.expr,
            verified=verified,
            observed=result.value,
            expected=expected_value,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except ValueError as e:
        return create_problem_response(
            request, 422,
            "validation-error",
            "Verification failed",
            str(e)
        )
        
    except Exception as e:
        logger.error(
            "Finance expression verification failed",
            ticker=req.ticker,
            expr=req.expr,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
            request, 500,
            "internal-error",
            "Expression verification failed",
            f"Internal error: {str(e)}"
        )

@router.get("/registry/metrics")
async def list_metrics():
    """List all available metrics in the KPI registry"""
    metrics = kpi_registry.list_metrics()
    return {
        "metrics": metrics,
        "count": len(metrics),
        "registry_info": kpi_registry.get_registry_summary()
    }

@router.get("/registry/inputs")
async def list_inputs():
    """List all available inputs in the KPI registry"""
    inputs = kpi_registry.list_inputs()
    return {
        "inputs": inputs,
        "count": len(inputs),
        "registry_info": kpi_registry.get_registry_summary()
    }

@router.get("/registry/functions")
async def list_functions():
    """List all available functions in the KPI registry"""
    functions = kpi_registry.list_functions()
    return {
        "functions": functions,
        "count": len(functions),
        "registry_info": kpi_registry.get_registry_summary()
    }

