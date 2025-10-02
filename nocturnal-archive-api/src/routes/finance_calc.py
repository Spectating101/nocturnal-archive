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
        return create_problem_response(
            request, 422,
            "validation-error",
            "Calculation failed",
            str(e)
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
        
        # Use multi-source router for universal data access
        from src.services.definitive_router import DefinitiveRouter
        definitive_router = DefinitiveRouter()
        
        # Simple expression parsing for demo
        if "=" in req.expr:
            left, right = req.expr.split("=", 1)
            left = left.strip()
            right = right.strip()
        else:
            left = req.expr
            right = req.expr
        
        # Parse expression to extract concepts
        import re
        concepts = re.findall(r'\b(revenue|costOfRevenue|sharesOutstanding|grossProfit|operatingIncome|netIncome|price|market_cap|pe_ratio|eps|dividend_yield)\b', right)
        
        # Get input facts using multi-source router
        input_terms = []
        for concept in concepts:
            try:
                # Try multi-source router first
                request_data = {
                    "ticker": req.ticker,
                    "expr": concept,
                    "period": req.period,
                    "freq": req.freq
                }
                
                result = await definitive_router.get_data(request_data)
                if result:
                    # Map Yahoo Finance fields to expected format
                    if "price" in result:
                        result["value"] = result["price"]
                    elif "revenue" in result and concept == "revenue":
                        result["value"] = result["revenue"]
                    elif "market_cap" in result and concept == "market_cap":
                        result["value"] = result["market_cap"]
                    elif "pe_ratio" in result and concept == "pe_ratio":
                        result["value"] = result["pe_ratio"]
                    elif "eps" in result and concept == "eps":
                        result["value"] = result["eps"]
                    elif "dividend_yield" in result and concept == "dividend_yield":
                        result["value"] = result["dividend_yield"]
                
                if result and "value" in result:
                    # Handle different data source formats
                    if "citations" in result:
                        citation = result["citations"][0] if result["citations"] else {}
                        input_terms.append({
                            "concept": concept,
                            "value": result["value"],
                            "accession": citation.get("accession", ""),
                            "unit": citation.get("unit", result.get("currency", "USD")),
                            "scale": "U",
                            "fx_used": citation.get("fx_used"),
                            "amended": False,
                            "as_reported": True,
                            "data_source": result.get("data_source", "unknown")
                        })
                    else:
                        # Fallback for simple data format
                        input_terms.append({
                            "concept": concept,
                            "value": result["value"],
                            "accession": "",
                            "unit": result.get("currency", "USD"),
                            "scale": "U", 
                            "fx_used": None,
                            "amended": False,
                            "as_reported": True,
                            "data_source": result.get("data_source", "unknown")
                        })
                else:
                    # Fallback to SEC adapter for backwards compatibility
                    from src.adapters.sec_facts import get_sec_facts_adapter
                    sec_adapter = get_sec_facts_adapter()
                    fact = await sec_adapter.get_fact(req.ticker, concept, period=req.period, freq=req.freq)
                    if fact:
                        input_terms.append({
                            "concept": concept,
                            "value": fact["value"],
                            "accession": fact["citation"]["accession"],
                            "unit": fact["citation"]["unit"],
                            "scale": fact["citation"]["scale"],
                            "fx_used": fact["citation"]["fx_used"],
                            "amended": fact["citation"]["amended"],
                            "as_reported": fact["citation"]["as_reported"],
                            "data_source": "sec_edgar"
                        })
            except ValueError as e:
                # Re-raise ValueError from strict mode
                raise e
        
        # Validate that all concepts in expression were found
        if len(concepts) > len(input_terms):
            missing_concepts = set(concepts) - set(term["concept"] for term in input_terms)
            raise ValueError(f"concept_not_found: Could not find data for concepts: {list(missing_concepts)}")
        
        # Validate unit compatibility for arithmetic operations
        if len(input_terms) > 1:
            # Check if all terms have compatible units for arithmetic operations
            units = [term["unit"] for term in input_terms]
            monetary_units = {"USD", "EUR", "GBP", "JPY", "TWD", "CAD", "AUD", "CHF"}
            
            # If any term is monetary and others are not, this is incompatible
            has_monetary = any(unit in monetary_units for unit in units)
            has_non_monetary = any(unit not in monetary_units and unit != "USD" for unit in units)
            
            if has_monetary and has_non_monetary:
                raise ValueError(f"unsupported_unit_operation: Cannot perform arithmetic operations between monetary ({[u for u in units if u in monetary_units]}) and non-monetary ({[u for u in units if u not in monetary_units]}) units")
        
        # Calculate result based on expression
        if len(input_terms) == 2:
            term1, term2 = input_terms
            if "revenue" in [term1["concept"], term2["concept"]] and "costOfRevenue" in [term1["concept"], term2["concept"]]:
                # Gross profit calculation
                revenue_val = next(t["value"] for t in input_terms if t["concept"] == "revenue")
                cost_val = next(t["value"] for t in input_terms if t["concept"] == "costOfRevenue")
                result_value = revenue_val - cost_val
                result_unit = term1["unit"]  # Should be same as term2 after validation
            else:
                # Generic subtraction - validate units are compatible
                if term1["unit"] != term2["unit"]:
                    raise ValueError(f"unsupported_unit_operation: Cannot subtract {term2['concept']} ({term2['unit']}) from {term1['concept']} ({term1['unit']}) - units must be compatible")
                result_value = term1["value"] - term2["value"]
                result_unit = term1["unit"]
        elif len(input_terms) == 1:
            result_value = input_terms[0]["value"]
            result_unit = input_terms[0]["unit"]
        else:
            result_value = 0
            result_unit = "USD"
        
        # Build response
        response_data = {
            "ticker": req.ticker,
            "expr": req.expr,
            "period": req.period,
            "freq": req.freq,
            "value": result_value,
            "data_source": input_terms[0].get("data_source", "sec_edgar") if input_terms else "unknown",
            "formula": "grossProfit = revenue - costOfRevenue",
            "left": {
                "concept": "grossProfit",
                "value": result_value,
                "unit": result_unit
            },
            "right": {
                "terms": input_terms
            },
            "citations": [
                {
                    "source": "SEC EDGAR 10-K Filing" if input_terms[0].get("data_source") == "sec_edgar" else "Yahoo Finance",
                    "accession": input_terms[0]["accession"] if input_terms else "N/A",
                    "url": f"https://www.sec.gov/Archives/edgar/..." if input_terms[0].get("data_source") == "sec_edgar" else "https://finance.yahoo.com/quote/{}/financials".format(req.ticker),
                    "page": "Consolidated Statements of Operations" if input_terms[0].get("data_source") == "sec_edgar" else "Financial Data"
                }
            ] if input_terms else [],
            "metadata": {
                "calculated_at": datetime.now().isoformat(),
                "engine_version": "1.0.0"
            }
        }
        
        logger.info(
            "Finance expression explanation completed",
            ticker=req.ticker,
            expr=req.expr,
            value=result_value,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except ValueError as e:
        return create_problem_response(
            request, 422,
            "validation-error",
            "Expression evaluation failed",
            str(e)
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

