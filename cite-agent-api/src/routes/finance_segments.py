"""
Finance Segments API Routes
Endpoints for segment-level financial analysis
"""

from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import structlog

from src.utils.error_handling import create_problem_response
from src.adapters.segment_parser import get_segment_parser
from src.config.settings import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/finance/segments", tags=["Finance Segments"])

class SegmentKPIPoint(BaseModel):
    period: str
    value: float
    unit: str
    citations: List[Dict[str, Any]] = []
    quality_flags: List[str] = []

class SegmentSeries(BaseModel):
    segment: str
    points: List[SegmentKPIPoint]

class SegmentResponse(BaseModel):
    ticker: str
    kpi: str
    dim: str
    freq: str
    series: List[SegmentSeries]

@router.get("/{ticker}/{kpi}")
async def get_segments(
    ticker: str,
    kpi: str,
    dim: str = Query(..., description="Dimension: Geography, Business, Product"),
    freq: str = Query("Q", description="Frequency: Q or A"),
    limit: int = Query(8, ge=1, le=20, description="Number of periods"),
    ttm: bool = Query(False, description="Use TTM values"),
    request: Request = None
):
    """
    Get segment-level KPI data for a company
    
    Args:
        ticker: Company ticker symbol
        kpi: KPI name (e.g., revenue, grossProfit)
        dim: Dimension (Geography, Business, Product)
        freq: Frequency (Q for quarterly, A for annual)
        limit: Number of periods to return
        ttm: Whether to use trailing twelve months
        
    Returns:
        Segment breakdown with citations
    """
    logger.info(
        "Finance segment KPI request",
        ticker=ticker,
        kpi=kpi,
        dim=dim,
        freq=freq,
        limit=limit,
        ttm=ttm,
        trace_id=getattr(request.state, "trace_id", "unknown") if request else "unknown"
    )
    
    settings = get_settings()
    
    # STRICT MODE: Use real segment parser
    if settings.finsight_strict:
        logger.info("Strict mode: parsing real XBRL segments", ticker=ticker, dim=dim)
        
        segment_parser = get_segment_parser()
        segment_series_list = await segment_parser.get_segment_series(
            ticker, kpi, dim, freq, limit
        )
        
        if not segment_series_list:
            # In strict mode, return 422 when no real segment data is available
            # This is realistic - many companies don't provide detailed segment breakdowns in XBRL
            return create_problem_response(
                request, 422,
                "segment_not_available",
                "No segment data available",
                f"No {dim} segment data found for {ticker} {kpi} in SEC filings. Segment data is often not available in structured XBRL format."
            )
        
        # Convert to response format
        series_response = []
        for series_data in segment_series_list:
            points = []
            for point_data in series_data["points"]:
                points.append(SegmentKPIPoint(
                    period=point_data["period"],
                    value=point_data["value"],
                    unit=point_data["unit"],
                    citations=point_data["citations"],
                    quality_flags=point_data["quality_flags"]
                ))
            
            series_response.append(SegmentSeries(
                segment=series_data["segment"],
                points=points
            ))
        
        response_data = SegmentResponse(
            ticker=ticker,
            kpi=kpi,
            dim=dim,
            freq=freq,
            series=series_response
        )
        
        logger.info("Real segment data retrieved", 
                   ticker=ticker, kpi=kpi, dim=dim, 
                   segments_returned=len(response_data.series))
        
        return response_data
    
    # NON-STRICT MODE: Use mock data for development
    else:
        logger.info("Non-strict mode: using mock segment data", ticker=ticker, dim=dim)
        
        # Mock segment data for development with proper XBRL dimensions
        mock_segments = {
            "AAPL": {
                "revenue": {
                    "Geography": [
                        {
                            "segment": "Americas",
                            "points": [
                                {
                                    "period": "2024-Q4", 
                                    "value": 150000000000, 
                                    "unit": "USD",
                                    "citations": [{
                                        "source": "SEC EDGAR",
                                        "accession": "0000320193-24-000006",
                                        "url": "https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000006/aapl-20240928.htm",
                                        "concept": "revenue",
                                        "taxonomy": "us-gaap",
                                        "unit": "USD",
                                        "scale": "U",
                                        "fx_used": None,
                                        "amended": False,
                                        "as_reported": True,
                                        "filed": "2024-Q4",
                                        "form": "10-K",
                                        "fiscal_year": 2024,
                                        "fiscal_period": "Q4",
                                        "dimension": "us-gaap:StatementGeographicalAxis",
                                        "member": "us-gaap:AmericasMember"
                                    }]
                                }
                            ]
                        },
                        {
                            "segment": "Europe",
                            "points": [
                                {
                                    "period": "2024-Q4", 
                                    "value": 80000000000, 
                                    "unit": "USD",
                                    "citations": [{
                                        "source": "SEC EDGAR",
                                        "accession": "0000320193-24-000006",
                                        "url": "https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000006/aapl-20240928.htm",
                                        "concept": "revenue",
                                        "taxonomy": "us-gaap",
                                        "unit": "USD",
                                        "scale": "U",
                                        "fx_used": None,
                                        "amended": False,
                                        "as_reported": True,
                                        "filed": "2024-Q4",
                                        "form": "10-K",
                                        "fiscal_year": 2024,
                                        "fiscal_period": "Q4",
                                        "dimension": "us-gaap:StatementGeographicalAxis",
                                        "member": "us-gaap:EuropeMember"
                                    }]
                                }
                            ]
                        },
                        {
                            "segment": "Greater China",
                            "points": [
                                {
                                    "period": "2024-Q4", 
                                    "value": 60000000000, 
                                    "unit": "USD",
                                    "citations": [{
                                        "source": "SEC EDGAR",
                                        "accession": "0000320193-24-000006",
                                        "url": "https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000006/aapl-20240928.htm",
                                        "concept": "revenue",
                                        "taxonomy": "us-gaap",
                                        "unit": "USD",
                                        "scale": "U",
                                        "fx_used": None,
                                        "amended": False,
                                        "as_reported": True,
                                        "filed": "2024-Q4",
                                        "form": "10-K",
                                        "fiscal_year": 2024,
                                        "fiscal_period": "Q4",
                                        "dimension": "us-gaap:StatementGeographicalAxis",
                                        "member": "us-gaap:GreaterChinaMember"
                                    }]
                                }
                            ]
                        }
                    ]
                }
            }
        }

        if ticker.upper() not in mock_segments:
            return create_problem_response(
                request, 404,
                "not-found",
                "No segment data found",
                f"No segment data found for {ticker}"
            )
        
        if kpi not in mock_segments[ticker.upper()]:
            return create_problem_response(
                request, 404,
                "not-found",
                "No segment data found",
                f"No {kpi} segment data found for {ticker}"
            )
        
        if dim not in mock_segments[ticker.upper()][kpi]:
            return create_problem_response(
                request, 404,
                "not-found",
                "No segment data found",
                f"No {dim} segment data found for {ticker} {kpi}"
            )

        segment_data_raw = mock_segments[ticker.upper()][kpi][dim]
        
        segment_series_list = []
        for item in segment_data_raw:
            points = []
            for p in item["points"]:
                # Use the citations from the mock data (which now include XBRL dimensions)
                citations = p.get("citations", [])
                points.append(SegmentKPIPoint(
                    period=p["period"],
                    value=p["value"],
                    unit=p["unit"],
                    citations=citations,
                    quality_flags=[]
                ))
            segment_series_list.append(SegmentSeries(segment=item["segment"], points=points))

        response_data = SegmentResponse(
            ticker=ticker,
            kpi=kpi,
            dim=dim,
            freq=freq,
            series=segment_series_list
        )

        logger.info("Mock segment data returned", ticker=ticker, kpi=kpi, dim=dim, segments_returned=len(response_data.series))
        return response_data