"""
Finance KPIs API Routes
Endpoints for retrieving financial KPIs and statements
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog

from src.facts.store import FactsStore
from src.calc.registry import KPIRegistry
from src.utils.error_handling import create_problem_response, get_error_type
from src.adapters.sec_facts import get_sec_facts_adapter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/kpis", tags=["Finance KPIs"])

# Global instances (would be injected in production)
kpi_registry = KPIRegistry()
facts_store = FactsStore()

class KPISearchRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    kpi: str = Field(..., description="KPI name (e.g., 'revenue', 'grossMargin')")
    freq: str = Field("Q", description="Frequency ('Q' for quarterly, 'A' for annual)")
    limit: int = Field(12, ge=1, le=50, description="Maximum number of periods")
    ttm: bool = Field(False, description="Calculate trailing twelve months")

@router.get("/registry/available")
async def get_available_kpis():
    """Get list of all available KPIs"""
    metrics = kpi_registry.list_metrics()
    inputs = kpi_registry.list_inputs()
    
    aliases = {
        "revenue": "revenueTotal",
        "sales": "revenueTotal",
        "turnover": "revenueTotal",
        "cogs": "costOfRevenue",
        "costofgoods": "costOfRevenue",
        "grossmargin": "grossMargin",
        "netincome": "netIncome",
        "eps": "epsDiluted",
    }
    
    # Handle both dict and list return types
    if isinstance(metrics, dict):
        kpi_list = list(metrics.keys())
    else:
        kpi_list = metrics
    
    if isinstance(inputs, dict):
        input_list = list(inputs.keys())
    else:
        input_list = inputs
    
    return {
        "kpis": kpi_list,
        "inputs": input_list,
        "aliases": aliases,
        "total_kpis": len(kpi_list),
        "total_inputs": len(input_list)
    }

@router.get("/{ticker}/{kpi}")
async def get_kpi(
    ticker: str,
    kpi: str,
    freq: str = Query("Q", description="Frequency ('Q' for quarterly, 'A' for annual)"),
    limit: int = Query(12, ge=1, le=50, description="Maximum number of periods"),
    ttm: bool = Query(False, description="Calculate trailing twelve months"),
    segment: Optional[str] = Query(None, description="Business segment filter"),
    request: Request = None
):
    """
    Get KPI values for a company over time
    
    Returns historical values with citations for each data point.
    """
    try:
        logger.info(
            "Finance KPI request",
            ticker=ticker,
            kpi=kpi,
            freq=freq,
            limit=limit,
            ttm=ttm,
            segment=segment,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Normalize KPI name and apply common aliases
        alias_map = {
            "revenue": "revenueTotal",
            "sales": "revenueTotal",
            "turnover": "revenueTotal",
            "cogs": "costOfRevenue",
            "costofgoods": "costOfRevenue",
            "grossmargin": "grossMargin",
            "netincome": "netIncome",
            "eps": "epsDiluted",
        }
        normalized_kpi = kpi.replace(" ", "").replace("_", "")
        normalized_kpi = normalized_kpi[0].lower() + normalized_kpi[1:] if normalized_kpi else normalized_kpi
        effective_kpi = alias_map.get(normalized_kpi, kpi)

        # Check if KPI exists in registry
        kpi_def = kpi_registry.get_metric(effective_kpi)

        # Helper: SEC adapter fallback using internal concept names supported by adapter
        async def _adapter_series_fallback(concept_key: str) -> Optional[Dict[str, Any]]:
            adapter = get_sec_facts_adapter()
            # The adapter understands keys like 'revenue', 'costOfRevenue', 'grossProfit', 'netIncome'
            series = await adapter.get_series(ticker, concept_key, freq=freq, limit=limit)
            if not series:
                return None
            data_points = [
                {
                    "period": p.get("period"),
                    "value": p.get("value"),
                    "unit": p.get("unit", "USD"),
                    "concept": concept_key,
                    "citation": p.get("citation", {}),
                    "quality_flags": []
                }
                for p in series
            ]
            return {
                "ticker": ticker,
                "kpi": concept_key,
                "freq": freq,
                "limit": limit,
                "ttm": ttm,
                "concept_used": concept_key,
                "data": data_points,
                "metadata": {
                    "total_periods": len(data_points),
                    "date_range": {
                        "start": data_points[-1]["period"] if data_points else None,
                        "end": data_points[0]["period"] if data_points else None
                    },
                    "kpi_definition": kpi_def or {"source": "adapter_fallback"}
                }
            }

        # If KPI not in registry, try adapter fallback for common concepts
        if not kpi_def:
            adapter_supported = {"revenue", "costOfRevenue", "grossProfit", "operatingIncome", "netIncome"}
            # Map normalized alias 'revenue' to adapter key 'revenue'
            adapter_key = normalized_kpi if normalized_kpi in adapter_supported else None
            if adapter_key is None and effective_kpi in adapter_supported:
                adapter_key = effective_kpi
            if adapter_key:
                fallback_response = await _adapter_series_fallback(adapter_key)
                if fallback_response:
                    return fallback_response
            return create_problem_response(
                f"Unknown KPI: {kpi}"
            ,
                404,
                "not-found"
            )
        
        # Get facts series for the KPI (registry-backed)
        input_defs = kpi_registry.get_metric_inputs(effective_kpi)
        if not input_defs:
            return create_problem_response(
                f"KPI '{kpi}' has no defined inputs"
            ,
                422,
                "validation-error"
            )
        
        # Get the primary input concept
        primary_input = list(input_defs.keys())[0]
        input_def = input_defs[primary_input]
        concepts = input_def.get("concepts", [])
        prefer_concept = input_def.get("prefer")
        
        # Try to get facts for the preferred concept first
        target_concept = prefer_concept or concepts[0] if concepts else None
        if not target_concept:
            return create_problem_response(
                f"Input '{primary_input}' has no concepts defined"
            ,
                422,
                "validation-error"
            )
        
        # Get facts series
        facts = await facts_store.get_facts_series(
            ticker=ticker,
            concept=target_concept,
            freq=freq,
            limit=limit,
            segment=segment
        )
        
        # If store is empty for this path, try adapter fallback using a close concept key if possible
        if not facts:
            adapter_key_map: Dict[str, str] = {
                "revenueTotal": "revenue",
                "costOfRevenue": "costOfRevenue",
                "grossProfit": "grossProfit",
                "operatingIncome": "operatingIncome",
                "netIncome": "netIncome",
            }
            adapter_key = adapter_key_map.get(effective_kpi)
            if adapter_key:
                fallback_response = await _adapter_series_fallback(adapter_key)
                if fallback_response:
                    return fallback_response
            return create_problem_response(
                f"No {freq} data found for {ticker} {kpi} ({target_concept})",
                404,
                "not-found"
            )
        
        # Build response from FactsStore
        kpi_data = []
        for fact in facts:
            kpi_point = {
                "period": fact.period,
                "value": fact.value,
                "unit": fact.unit,
                "concept": fact.concept,
                "citation": {
                    "source_url": fact.url,
                    "accession": fact.accession,
                    "fragment_id": fact.fragment_id,
                    "dimensions": fact.dimensions
                },
                "quality_flags": fact.quality_flags
            }
            kpi_data.append(kpi_point)
        
        response_data = {
            "ticker": ticker,
            "kpi": effective_kpi,
            "freq": freq,
            "limit": limit,
            "ttm": ttm,
            "concept_used": target_concept,
            "data": kpi_data,
            "metadata": {
                "total_periods": len(kpi_data),
                "date_range": {
                    "start": kpi_data[-1]["period"] if kpi_data else None,
                    "end": kpi_data[0]["period"] if kpi_data else None
                },
                "kpi_definition": kpi_def
            }
        }
        
        logger.info(
            "Finance KPI request completed",
            ticker=ticker,
            kpi=kpi,
            periods_returned=len(kpi_data),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Finance KPI request failed",
            ticker=ticker,
            kpi=kpi,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
                f"Internal error: {str(e,
                500,
                "internal-error"
            )}"
        )

@router.get("/{ticker}/statements/{statement_type}")
async def get_financial_statement(
    ticker: str,
    statement_type: str,
    period: str = Query("latest", description="Period (e.g., '2024-Q4', 'latest')"),
    freq: str = Query("Q", description="Frequency ('Q' for quarterly, 'A' for annual)"),
    request: Request = None
):
    """
    Get financial statement data for a company
    
    Returns structured financial statement with all line items and citations.
    """
    try:
        logger.info(
            "Finance statement request",
            ticker=ticker,
            statement_type=statement_type,
            period=period,
            freq=freq,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Define statement line items by type
        statement_items = {
            "income": [
                "revenue", "costOfRevenue", "grossProfit", "operatingIncome",
                "netIncome", "epsBasic", "epsDiluted"
            ],
            "balance": [
                "currentAssets", "totalAssets", "currentLiabilities",
                "shareholdersEquity", "workingCapital", "currentRatio"
            ],
            "cashflow": [
                "cfo", "cfi", "cff", "fcf"
            ]
        }
        
        if statement_type not in statement_items:
            return create_problem_response(
                f"Statement type must be one of: {', '.join(statement_items.keys())}",
                422,
                "validation-error"
            )
        
        # Get company metadata
        company_metadata = facts_store.get_company_metadata(ticker)
        if not company_metadata:
            return create_problem_response(
                f"No data found for company: {ticker}"
            ,
                404,
                "not-found"
            )
        
        # Get statement line items
        statement_data = []
        for item in statement_items[statement_type]:
            # Get KPI definition
            kpi_def = kpi_registry.get_metric(item)
            if not kpi_def:
                continue
            
            # Get facts for this item
            input_defs = kpi_registry.get_metric_inputs(item)
            if not input_defs:
                continue
            
            # Get primary input concept
            primary_input = list(input_defs.keys())[0]
            input_def = input_defs[primary_input]
            concepts = input_def.get("concepts", [])
            prefer_concept = input_def.get("prefer")
            target_concept = prefer_concept or concepts[0] if concepts else None
            
            if target_concept:
                fact = await facts_store.get_fact(
                    ticker=ticker,
                    concept=target_concept,
                    period=period,
                    freq=freq
                )
                
                if fact:
                    statement_data.append({
                        "line_item": item,
                        "concept": target_concept,
                        "value": fact.value,
                        "unit": fact.unit,
                        "period": fact.period,
                        "citation": {
                            "source_url": fact.url,
                            "accession": fact.accession,
                            "fragment_id": fact.fragment_id,
                            "dimensions": fact.dimensions
                        },
                        "quality_flags": fact.quality_flags
                    })
        
        response_data = {
            "ticker": ticker,
            "company_name": company_metadata.get("company_name", ""),
            "statement_type": statement_type,
            "period": period,
            "freq": freq,
            "line_items": statement_data,
            "metadata": {
                "total_items": len(statement_data),
                "company_info": company_metadata,
                "statement_definition": {
                    "type": statement_type,
                    "items": statement_items[statement_type]
                }
            }
        }
        
        logger.info(
            "Finance statement request completed",
            ticker=ticker,
            statement_type=statement_type,
            items_returned=len(statement_data),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Finance statement request failed",
            ticker=ticker,
            statement_type=statement_type,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
                f"Internal error: {str(e,
                500,
                "internal-error"
            )}"
        )

@router.get("/{ticker}/segments/{kpi}")
async def get_segment_kpi(
    ticker: str,
    kpi: str,
    freq: str = Query("Q", description="Frequency ('Q' for quarterly, 'A' for annual)"),
    limit: int = Query(12, ge=1, le=50, description="Maximum number of periods"),
    request: Request = None
):
    """
    Get KPI values by business segment
    
    Returns KPI values broken down by business segment with segment-level citations.
    """
    try:
        logger.info(
            "Finance segment KPI request",
            ticker=ticker,
            kpi=kpi,
            freq=freq,
            limit=limit,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Get KPI definition
        kpi_def = kpi_registry.get_metric(kpi)
        if not kpi_def:
            return create_problem_response(
                f"Unknown KPI: {kpi}"
            ,
                404,
                "not-found"
            )
        
        # Get input concepts
        input_defs = kpi_registry.get_metric_inputs(kpi)
        if not input_defs:
            return create_problem_response(
                f"KPI '{kpi}' has no defined inputs"
            ,
                422,
                "validation-error"
            )
        
        # Get primary input concept
        primary_input = list(input_defs.keys())[0]
        input_def = input_defs[primary_input]
        concepts = input_def.get("concepts", [])
        prefer_concept = input_def.get("prefer")
        target_concept = prefer_concept or concepts[0] if concepts else None
        
        if not target_concept:
            return create_problem_response(
                f"Input '{primary_input}' has no concepts defined"
            ,
                422,
                "validation-error"
            )
        
        # Get facts with segment dimensions
        facts = await facts_store.get_facts_series(
            ticker=ticker,
            concept=target_concept,
            freq=freq,
            limit=limit
        )
        
        # Group by segment
        segments = {}
        for fact in facts:
            segment = fact.dimensions.get("BusinessSegment", "Consolidated")
            if segment not in segments:
                segments[segment] = []
            segments[segment].append(fact)
        
        # Build segment data
        segment_data = {}
        for segment, segment_facts in segments.items():
            segment_facts.sort(key=lambda x: x.period, reverse=True)
            
            segment_data[segment] = [
                {
                    "period": fact.period,
                    "value": fact.value,
                    "unit": fact.unit,
                    "citation": {
                        "source_url": fact.url,
                        "accession": fact.accession,
                        "fragment_id": fact.fragment_id,
                        "dimensions": fact.dimensions
                    },
                    "quality_flags": fact.quality_flags
                }
                for fact in segment_facts[:limit]
            ]
        
        response_data = {
            "ticker": ticker,
            "kpi": kpi,
            "freq": freq,
            "limit": limit,
            "concept_used": target_concept,
            "segments": segment_data,
            "metadata": {
                "total_segments": len(segments),
                "segment_names": list(segments.keys()),
                "kpi_definition": kpi_def
            }
        }
        
        logger.info(
            "Finance segment KPI request completed",
            ticker=ticker,
            kpi=kpi,
            segments_returned=len(segments),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Finance segment KPI request failed",
            ticker=ticker,
            kpi=kpi,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        return create_problem_response(
                f"Internal error: {str(e,
                500,
                "internal-error"
            )}"
        )


