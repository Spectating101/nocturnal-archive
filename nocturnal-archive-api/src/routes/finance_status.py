"""
Finance Status API Routes
Health check endpoint for FinSight data sources
"""

from fastapi import APIRouter, Request
from typing import Dict, Any, List
import structlog
import asyncio
import aiohttp
import time

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/finance/status", tags=["Finance Status"])

@router.get("/")
async def get_finance_status_with_slash(request: Request):
    """
    Get comprehensive status of all FinSight data sources
    
    Returns health status, latency, and operational metrics for each source.
    """
    try:
        logger.info(
            "Finance status check requested",
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # Check each data source
        sources_status = await _check_all_sources()
        
        # Calculate overall health
        total_sources = len(sources_status)
        healthy_sources = len([s for s in sources_status if s["status"] == "healthy"])
        health_percentage = (healthy_sources / total_sources * 100) if total_sources > 0 else 0
        
        overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
        
        response = {
            "overall_status": overall_status,
            "health_percentage": round(health_percentage, 1),
            "total_sources": total_sources,
            "healthy_sources": healthy_sources,
            "sources": sources_status,
            "timestamp": time.time(),
            "metadata": {
                "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "api_version": "1.0.0"
            }
        }
        
        logger.info(
            "Finance status check completed",
            overall_status=overall_status,
            health_percentage=health_percentage,
            healthy_sources=healthy_sources,
            total_sources=total_sources,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return response
        
    except Exception as e:
        logger.error("Finance status check failed", error=str(e))
        
        return {
            "overall_status": "error",
            "health_percentage": 0,
            "error": str(e),
            "timestamp": time.time()
        }

async def _check_all_sources() -> List[Dict[str, Any]]:
    """Check health of all FinSight data sources"""
    
    sources_to_check = [
        {
            "id": "sec_submissions",
            "name": "SEC EDGAR Submissions",
            "url": "https://data.sec.gov/submissions/",
            "critical": True,
            "description": "US company filings metadata"
        },
        {
            "id": "sec_companyfacts", 
            "name": "SEC EDGAR Company Facts",
            "url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
            "critical": True,
            "description": "US XBRL financial facts"
        },
        {
            "id": "fred",
            "name": "Federal Reserve Economic Data",
            "url": "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&file_type=json&limit=1",
            "critical": False,
            "description": "US economic indicators"
        },
        {
            "id": "bls",
            "name": "Bureau of Labor Statistics",
            "url": "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            "critical": False,
            "description": "US labor market data"
        },
        {
            "id": "ecb_fx",
            "name": "European Central Bank FX",
            "url": "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1&format=csvdata",
            "critical": False,
            "description": "ECB reference exchange rates"
        },
        {
            "id": "openfigi",
            "name": "OpenFIGI",
            "url": "https://api.openfigi.com/v3/mapping",
            "critical": False,
            "description": "Financial instrument identifiers"
        }
    ]
    
    async with aiohttp.ClientSession(
        headers={"User-Agent": "FinSight Health Check (contact@nocturnal.dev)"},
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        # Check all sources concurrently
        tasks = [_check_source(session, source) for source in sources_to_check]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        sources_status = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sources_status.append({
                    "id": sources_to_check[i]["id"],
                    "name": sources_to_check[i]["name"],
                    "status": "error",
                    "latency_ms": None,
                    "error": str(result),
                    "critical": sources_to_check[i]["critical"],
                    "description": sources_to_check[i]["description"]
                })
            else:
                sources_status.append(result)
        
        # Calculate overall health
        healthy_sources = sum(1 for s in sources_status if s["status"] == "healthy")
        total_sources = len(sources_status)
        health_percentage = (healthy_sources / total_sources * 100) if total_sources > 0 else 0
        
        overall_status = "healthy" if health_percentage >= 90 else "unhealthy"
        
        response_data = {
            "overall_status": overall_status,
            "health_percentage": round(health_percentage, 2),
            "healthy_sources": healthy_sources,
            "total_sources": total_sources,
            "sources": sources_status,
            "timestamp": time.time()
        }
        
        logger.info(
            "Finance status check completed",
            overall_status=overall_status,
            health_percentage=health_percentage,
            healthy_sources=healthy_sources,
            total_sources=total_sources
        )
        
        return response_data

async def _check_source(session: aiohttp.ClientSession, source: Dict[str, Any]) -> Dict[str, Any]:
    """Check health of a single source"""
    try:
        start_time = time.time()
        
        # Make request
        async with session.get(source["url"]) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status == 200:
                status = "healthy"
                error = None
            elif response.status in [403, 429]:
                status = "rate_limited"
                error = f"HTTP {response.status} - Rate limited"
            else:
                status = "unhealthy"
                error = f"HTTP {response.status}"
        
        return {
            "id": source["id"],
            "name": source["name"],
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "error": error,
            "critical": source["critical"],
            "description": source["description"]
        }
        
    except Exception as e:
        return {
            "id": source["id"],
            "name": source["name"],
            "status": "unhealthy",
            "latency_ms": None,
            "error": str(e),
            "critical": source["critical"],
            "description": source["description"]
        }

@router.get("/sources/{source_id}")
async def get_source_status(source_id: str, request: Request):
    """
    Get detailed status for a specific data source
    
    Args:
        source_id: ID of the data source to check
    """
    try:
        logger.info(
            "Source status check requested",
            source_id=source_id,
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        # This would check a specific source in detail
        # For now, return a placeholder
        return {
            "source_id": source_id,
            "status": "healthy",
            "last_checked": time.time(),
            "details": {
                "endpoint": f"Specific check for {source_id}",
                "response_time": "< 100ms",
                "data_quality": "good"
            }
        }
        
    except Exception as e:
        logger.error(
            "Source status check failed",
            source_id=source_id,
            error=str(e),
            trace_id=getattr(request.state, "trace_id", "unknown")
        )
        
        return {
            "source_id": source_id,
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("", include_in_schema=False)
async def get_finance_status_no_slash(request: Request):
    """Alias for status endpoint without trailing slash"""
    return await get_finance_status_with_slash(request)
