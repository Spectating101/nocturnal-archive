"""
Finance Filings API Routes
EDGAR SEC filing search, fetch, and analysis
"""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import structlog

from src.engine.retrievers.finance.edgar import EdgarRetriever, FilingInfo, FilingContent
from src.utils.error_handling import create_problem_response, get_error_type
from src.jobs.queue import enqueue_synthesis, get_job_status

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/finance", tags=["Finance Filings"])

class FilingSearchRequest(BaseModel):
    ticker: Optional[str] = Field(None, description="Company ticker symbol (e.g., AAPL)")
    cik: Optional[str] = Field(None, description="Company CIK number")
    form: str = Field("10-K", description="Form type (10-K, 10-Q, 8-K)")
    year_range: Tuple[int, int] = Field((2020, 2024), description="Year range (start, end)")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")

class FilingFetchRequest(BaseModel):
    accession: str = Field(..., description="Filing accession number")

class FilingExtractRequest(BaseModel):
    accession: str = Field(..., description="Filing accession number")
    sections: List[str] = Field(["mda", "risk"], description="Sections to extract")
    tables: bool = Field(True, description="Whether to extract tables")

class FilingSynthesizeRequest(BaseModel):
    accession: str = Field(..., description="Filing accession number")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    claims: List[Dict[str, Any]] = Field(default_factory=list, description="Claims to verify")
    grounded: bool = Field(True, description="Whether to ground claims against data")

@router.post("/filings/search")
async def search_filings(req: FilingSearchRequest, request: Request):
    """
    Search SEC filings in EDGAR database
    
    Search for SEC filings by company ticker/CIK, form type, and date range.
    Returns basic filing information including accession numbers and URLs.
    """
    try:
        logger.info(
            "Finance filing search request received",
            ticker=req.ticker,
            cik=req.cik,
            form=req.form,
            year_range=req.year_range,
            limit=req.limit,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Validate input
        if not req.ticker and not req.cik:
            error_info = get_error_type("validation-error")
            return create_problem_response(
                request, 422,
                "validation-error",
                "Validation error",
                "Either ticker or cik must be provided"
            )
        
        # Search filings
        async with EdgarRetriever() as retriever:
            filings = await retriever.search_filings(
                ticker=req.ticker,
                cik=req.cik,
                form=req.form,
                year_range=req.year_range,
                limit=req.limit
            )
        
        # Convert to response format
        results = []
        for filing in filings:
            results.append({
                "accession": filing.accession,
                "form": filing.form,
                "filing_date": filing.filing_date.isoformat(),
                "url": filing.url,
                "company_name": filing.company_name,
                "ticker": filing.ticker,
                "cik": filing.cik
            })
        
        logger.info(
            "Finance filing search completed",
            results_count=len(results),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return {
            "filings": results,
            "count": len(results),
            "query": {
                "ticker": req.ticker,
                "cik": req.cik,
                "form": req.form,
                "year_range": req.year_range
            }
        }
        
    except Exception as e:
        logger.error(
            "Finance filing search failed",
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error",
            "Search failed",
            f"Failed to search filings: {str(e)}"
        )

@router.post("/filings/fetch")
async def fetch_filing(req: FilingFetchRequest, request: Request):
    """
    Fetch and parse a specific SEC filing
    
    Downloads and parses a SEC filing by accession number.
    Returns raw HTML content and extracted sections/tables.
    """
    try:
        logger.info(
            "Finance filing fetch request received",
            accession=req.accession,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Fetch filing
        async with EdgarRetriever() as retriever:
            content = await retriever.fetch_filing(req.accession)
        
        # Convert to response format
        response = {
            "accession": content.accession,
            "sections": content.sections,
            "tables": content.tables,
            "metadata": content.metadata,
            "content_length": len(content.raw_html)
        }
        
        logger.info(
            "Finance filing fetch completed",
            accession=req.accession,
            sections_found=len(content.sections),
            tables_found=len(content.tables),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Finance filing fetch failed",
            error=str(e),
            accession=req.accession,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error",
            "Fetch failed",
            f"Failed to fetch filing: {str(e)}"
        )

@router.post("/extract")
async def extract_filing_data(req: FilingExtractRequest, request: Request):
    """
    Extract specific sections and tables from a SEC filing
    
    Extracts specified sections (e.g., MD&A, Risk Factors) and tables
    from a SEC filing for further analysis.
    """
    try:
        logger.info(
            "Finance filing extract request received",
            accession=req.accession,
            sections=req.sections,
            extract_tables=req.tables,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Fetch filing
        async with EdgarRetriever() as retriever:
            content = await retriever.fetch_filing(req.accession)
        
        # Extract requested sections
        extracted_sections = {}
        for section in req.sections:
            if section in content.sections:
                extracted_sections[section] = content.sections[section]
            else:
                extracted_sections[section] = f"Section '{section}' not found in filing"
        
        # Extract tables if requested
        extracted_tables = []
        if req.tables:
            extracted_tables = content.tables
        
        response = {
            "accession": req.accession,
            "sections": extracted_sections,
            "tables": extracted_tables,
            "metadata": {
                "sections_requested": req.sections,
                "sections_found": len([s for s in extracted_sections.values() if not s.startswith("Section")]),
                "tables_found": len(extracted_tables),
                "extracted_at": content.metadata.get('parsed_at', 'unknown')
            }
        }
        
        logger.info(
            "Finance filing extract completed",
            accession=req.accession,
            sections_found=len(extracted_sections),
            tables_found=len(extracted_tables),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Finance filing extract failed",
            error=str(e),
            accession=req.accession,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error",
            "Extract failed",
            f"Failed to extract filing data: {str(e)}"
        )

@router.post("/synthesize")
async def synthesize_filing(req: FilingSynthesizeRequest, request: Request, response: Response):
    """
    Synthesize SEC filing with numeric grounding
    
    Analyzes a SEC filing and synthesizes key insights with optional
    numeric claim verification against external data sources.
    
    For large synthesis jobs, returns 202 with job_id for async processing.
    """
    try:
        logger.info(
            "Finance filing synthesize request received",
            accession=req.accession,
            claims_count=len(req.claims),
            grounded=req.grounded,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Check if this should be async (large context or many claims)
        should_async = len(req.claims) > 5 or req.grounded
        
        if should_async:
            try:
                # Enqueue for async processing
                payload = {
                    "accession": req.accession,
                    "context": req.context,
                    "claims": req.claims,
                    "grounded": req.grounded,
                    "api_key": getattr(request.state, "api_key", "unknown"),
                    "trace_id": getattr(request.state, "trace_id", "unknown")
                }
                
                job_id = enqueue_synthesis(payload)
                
                response.status_code = 202
                response.headers["Retry-After"] = "30"
                
                return {
                    "job_id": job_id,
                    "status": "queued",
                    "message": "Synthesis job queued for processing",
                    "check_status_url": f"/v1/api/jobs/{job_id}"
                }
                
            except RuntimeError as e:
                if "queue_full" in str(e):
                    response.status_code = 429
                    response.headers["Retry-After"] = "60"
                    return create_problem_response(
                        request, 429,
                        "queue-full",
                        "Job queue full",
                        "The job queue is currently full. Please try again later."
                    )
                elif "too_many_inflight" in str(e):
                    response.status_code = 429
                    response.headers["Retry-After"] = "30"
                    return create_problem_response(
                        request, 429,
                        "too-many-inflight",
                        "Too many requests in progress",
                        "You have reached the per-key concurrency limit. Please retry later."
                    )
                else:
                    raise
        
        # Synchronous processing for small jobs
        async with EdgarRetriever() as retriever:
            content = await retriever.fetch_filing(req.accession)
        
        # TODO: Implement LLM synthesis with grounding
        # For now, return a placeholder response
        summary = f"Analysis of {req.accession}: Found {len(content.sections)} sections and {len(content.tables)} tables."
        
        if req.grounded and req.claims:
            # TODO: Implement numeric grounding verification
            summary += f" Verified {len(req.claims)} numeric claims against external data."
        
        response_data = {
            "accession": req.accession,
            "summary": summary,
            "sections_analyzed": list(content.sections.keys()),
            "tables_analyzed": len(content.tables),
            "claims_verified": len(req.claims) if req.grounded else 0,
            "metadata": content.metadata
        }
        
        logger.info(
            "Finance filing synthesize completed",
            accession=req.accession,
            summary_length=len(summary),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Finance filing synthesize failed",
            error=str(e),
            accession=req.accession,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        error_info = get_error_type("validation-error")
        return create_problem_response(
            request, 500,
            "validation-error",
            "Synthesis failed",
            f"Failed to synthesize filing: {str(e)}"
        )

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, request: Request):
    """
    Get status of an async synthesis job
    """
    try:
        status = get_job_status(job_id)
        return status
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        return create_problem_response(
            request, 500,
            "validation-error",
            "Job status failed",
            f"Failed to get job status: {str(e)}"
        )

@router.get("/filings/forms")
async def get_available_forms():
    """
    Get list of available SEC form types
    """
    return {
        "forms": [
            {"type": "10-K", "description": "Annual Report"},
            {"type": "10-Q", "description": "Quarterly Report"},
            {"type": "8-K", "description": "Current Report"},
            {"type": "DEF 14A", "description": "Proxy Statement"},
            {"type": "S-1", "description": "Registration Statement"},
            {"type": "S-3", "description": "Registration Statement (Shelf)"},
            {"type": "S-4", "description": "Registration Statement (Merger)"},
            {"type": "13F", "description": "Institutional Holdings"},
            {"type": "13D", "description": "Beneficial Ownership"},
            {"type": "13G", "description": "Beneficial Ownership (Passive)"}
        ]
    }
