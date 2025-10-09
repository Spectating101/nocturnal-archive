"""
Finance Reports API Routes
PDF snapshot generation for FinSight financial reports
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import structlog
import io
from datetime import datetime

from src.utils.pdf_reporter import get_pdf_reporter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/finance/reports", tags=["Finance Reports"])

class ReportRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    period: str = Field("latest", description="Period (e.g., '2024-Q4', 'latest')")
    freq: str = Field("Q", description="Frequency ('Q' for quarterly, 'A' for annual)")
    format: str = Field("pdf", description="Report format ('pdf', 'html')")
    include_segments: bool = Field(True, description="Include segment breakdown")
    include_ttm: bool = Field(True, description="Include TTM calculations")

@router.get("/{ticker}/{period}.pdf")
async def generate_pdf_report(
    ticker: str,
    period: str,
    freq: str = "Q",
    include_segments: bool = True,
    include_ttm: bool = True,
    request: Request = None
):
    """
    Generate a PDF snapshot report for a company
    
    Returns a one-page PDF with KPI table, sparklines, and footnoted citations.
    """
    try:
        logger.info(
            "PDF report generation requested",
            ticker=ticker,
            period=period,
            freq=freq,
            include_segments=include_segments,
            include_ttm=include_ttm,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Generate report data
        report_data = await _generate_report_data(
            ticker, period, freq, include_segments, include_ttm
        )
        
        # Generate PDF content
        pdf_content = await _generate_pdf_content(report_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={ticker}_{period}_report.pdf",
                "X-Report-Generated": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(
            "PDF report generation failed",
            ticker=ticker,
            period=period,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Return error as JSON
        return {
            "error": "report_generation_failed",
            "detail": str(e),
            "ticker": ticker,
            "period": period
        }

@router.post("/generate")
async def generate_report(req: ReportRequest, request: Request):
    """
    Generate a financial report in specified format
    
    Supports PDF and HTML formats with customizable options.
    """
    try:
        logger.info(
            "Custom report generation requested",
            ticker=req.ticker,
            period=req.period,
            freq=req.freq,
            format=req.format,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Generate report data
        report_data = await _generate_report_data(
            req.ticker, req.period, req.freq, req.include_segments, req.include_ttm
        )
        
        if req.format == "pdf":
            # Generate PDF content
            pdf_content = await _generate_pdf_content(report_data)
            
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={req.ticker}_{req.period}_report.pdf"
                }
            )
            
        elif req.format == "html":
            # Generate HTML content
            html_content = _generate_html_content(report_data)
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename={req.ticker}_{req.period}_report.html"
                }
            )
        
        else:
            return {
                "error": "unsupported_format",
                "detail": f"Format '{req.format}' not supported. Use 'pdf' or 'html'.",
                "supported_formats": ["pdf", "html"]
            }
        
    except Exception as e:
        logger.error(
            "Custom report generation failed",
            ticker=req.ticker,
            format=req.format,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return {
            "error": "report_generation_failed",
            "detail": str(e),
            "ticker": req.ticker,
            "format": req.format
        }

async def _generate_report_data(
    ticker: str,
    period: str,
    freq: str,
    include_segments: bool,
    include_ttm: bool
) -> Dict[str, Any]:
    """Generate comprehensive report data"""
    
    # This would integrate with your existing calc engine and facts store
    # For now, return a structured template
    
    report_data = {
        "ticker": ticker.upper(),
        "period": period,
        "freq": freq,
        "generated_at": datetime.now().isoformat(),
        "company_info": {
            "name": f"{ticker} Inc.",
            "sector": "Technology",
            "market_cap": "N/A",
            "currency": "USD"
        },
        "key_metrics": {
            "revenue": {
                "value": 119575000000,
                "unit": "USD",
                "period": period,
                "citation": {
                    "source": "SEC EDGAR",
                    "accession": "0000320193-24-000006",
                    "url": "https://www.sec.gov/Archives/edgar/..."
                }
            },
            "gross_margin": {
                "value": 0.4123,
                "unit": "percent",
                "formula": "(revenue - costOfRevenue) / revenue",
                "citation": {
                    "source": "FinSight Calculation",
                    "inputs": ["revenue", "costOfRevenue"]
                }
            },
            "ebitda_margin": {
                "value": 0.3547,
                "unit": "percent",
                "formula": "(operatingIncome + depreciationAndAmortization) / revenue",
                "citation": {
                    "source": "FinSight Calculation",
                    "inputs": ["operatingIncome", "depreciationAndAmortization", "revenue"]
                }
            },
            "fcf": {
                "value": 38800000000,
                "unit": "USD",
                "formula": "cfo + cfi",
                "citation": {
                    "source": "FinSight Calculation",
                    "inputs": ["cfo", "cfi"]
                }
            }
        },
        "segments": [] if not include_segments else [
            {
                "name": "Americas",
                "revenue": 50414000000,
                "percentage": 42.2
            },
            {
                "name": "Europe",
                "revenue": 24189000000,
                "percentage": 20.2
            },
            {
                "name": "Greater China",
                "revenue": 20819000000,
                "percentage": 17.4
            }
        ],
        "ttm_analysis": [] if not include_ttm else [
            {
                "metric": "revenue_ttm",
                "value": 383285000000,
                "growth_yoy": 0.033
            },
            {
                "metric": "ebitda_margin_ttm",
                "value": 0.3521,
                "trend": "stable"
            }
        ],
        "citations": [
            {
                "id": 1,
                "source": "SEC EDGAR 10-K Filing",
                "accession": "0000320193-24-000006",
                "url": "https://www.sec.gov/Archives/edgar/...",
                "page": "Consolidated Statements of Operations"
            },
            {
                "id": 2,
                "source": "FinSight Calculation Engine",
                "formula": "Gross Margin = (Revenue - Cost of Revenue) / Revenue",
                "inputs": ["Revenue", "Cost of Revenue"]
            }
        ]
    }
    
    return report_data

async def _generate_pdf_content(report_data: Dict[str, Any]) -> bytes:
    """Generate PDF content from report data using real PDF generator"""
    
    # Use the real PDF reporter
    pdf_reporter = get_pdf_reporter()
    return await pdf_reporter.generate_report(
        report_data['ticker'],
        report_data['period'],
        report_data['freq']
    )

def _generate_html_content(report_data: Dict[str, Any]) -> str:
    """Generate HTML content from report data"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report_data['ticker']} Financial Report - {report_data['period']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .metric {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .segments {{ margin: 20px 0; }}
        .citations {{ margin-top: 40px; font-size: 12px; color: #666; }}
        .citation {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report_data['ticker']} Financial Report</h1>
        <p>Period: {report_data['period']} | Generated: {report_data['generated_at']}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Revenue</h3>
            <p><strong>${report_data['key_metrics']['revenue']['value']:,.0f}</strong></p>
            <small>Source: SEC EDGAR <sup>1</sup></small>
        </div>
        <div class="metric">
            <h3>Gross Margin</h3>
            <p><strong>{report_data['key_metrics']['gross_margin']['value']*100:.1f}%</strong></p>
            <small>Formula: {report_data['key_metrics']['gross_margin']['formula']} <sup>2</sup></small>
        </div>
        <div class="metric">
            <h3>EBITDA Margin</h3>
            <p><strong>{report_data['key_metrics']['ebitda_margin']['value']*100:.1f}%</strong></p>
            <small>Formula: {report_data['key_metrics']['ebitda_margin']['formula']} <sup>2</sup></small>
        </div>
        <div class="metric">
            <h3>Free Cash Flow</h3>
            <p><strong>${report_data['key_metrics']['fcf']['value']:,.0f}</strong></p>
            <small>Formula: {report_data['key_metrics']['fcf']['formula']} <sup>2</sup></small>
        </div>
    </div>
    
    {f'''
    <div class="segments">
        <h3>Revenue by Geography</h3>
        <ul>
        {''.join([f'<li>{seg["name"]}: ${seg["revenue"]:,.0f} ({seg["percentage"]:.1f}%)</li>' for seg in report_data["segments"]])}
        </ul>
    </div>
    ''' if report_data['segments'] else ''}
    
    <div class="citations">
        <h3>Citations</h3>
        {''.join([f'<div class="citation"><sup>{i+1}</sup> {citation["source"]} - {citation.get("accession", citation.get("formula", ""))}</div>' for i, citation in enumerate(report_data['citations'])])}
    </div>
</body>
</html>
"""
    
    return html_content
