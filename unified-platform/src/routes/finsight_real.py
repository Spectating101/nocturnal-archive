"""
Real FinSight API Routes - Integrated from nocturnal-archive-api
Financial data analysis and SEC EDGAR integration
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import structlog
import os
import sys

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

from src.config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/finsight", tags=["FinSight"])

# Import FinSight components
try:
    from src.engine.retrievers.finance.edgar import EdgarRetriever, FilingInfo, FilingContent
    from src.facts.store import FactsStore
    from src.calc.registry import KPIRegistry
    from src.utils.error_handling import create_problem_response, get_error_type
    from src.adapters.sec_facts import SECFactsAdapter
    FINSIGHT_AVAILABLE = True
    logger.info("✅ Real FinSight components loaded successfully")
except ImportError as e:
    logger.warning(f"FinSight components not available: {e}")
    FINSIGHT_AVAILABLE = False

# Simplified FinSight implementation for demo purposes
class SimpleFactsStore:
    """Simplified facts store for demo purposes"""
    
    async def get_kpi_series(self, ticker: str, kpi: str, freq: str, limit: int, ttm: bool, segment: str = None):
        """Return mock financial data"""
        import random
        from datetime import datetime, timedelta
        
        data = []
        base_date = datetime.now()
        
        for i in range(limit):
            if freq == "Q":
                period_date = base_date - timedelta(days=90*i)
                period = f"{period_date.year}-Q{(period_date.month-1)//3 + 1}"
            else:
                period_date = base_date - timedelta(days=365*i)
                period = f"{period_date.year}"
            
            # Mock financial data
            if kpi == "revenue":
                value = random.randint(1000000000, 50000000000)  # 1B to 50B
            elif kpi == "grossMargin":
                value = random.randint(20, 80)  # 20% to 80%
            else:
                value = random.randint(100000000, 10000000000)  # 100M to 10B
            
            data.append({
                "period": period,
                "value": value,
                "unit": "USD" if kpi != "grossMargin" else "PERCENT",
                "accession": f"0000320193-{period_date.year}-{i:06d}",
                "source": "SEC EDGAR (Mock Data)"
            })
        
        return data
    
    async def search_kpis(self, ticker: str, kpi: str, freq: str, limit: int, ttm: bool):
        """Return mock search results"""
        return await self.get_kpi_series(ticker, kpi, freq, limit, ttm)

class SimpleEdgarRetriever:
    """Simplified EDGAR retriever for demo purposes"""
    
    async def search_filings(self, ticker: str, cik: str, form: str, year_range: tuple, limit: int):
        """Return mock filing data"""
        import random
        from datetime import datetime
        
        filings = []
        for i in range(min(limit, 5)):
            year = random.randint(year_range[0], year_range[1])
            accession = f"0000320193-{year}-{i:06d}"
            
            filings.append({
                "accession": accession,
                "form": form,
                "filing_date": f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "company": ticker or "DEMO COMPANY",
                "cik": cik or "0000320193",
                "url": f"https://www.sec.gov/Archives/edgar/data/320193/{accession}/{accession}.txt"
            })
        
        return filings

# Global instances - USE REAL COMPONENTS WITH STRICT MODE
if FINSIGHT_AVAILABLE:
    kpi_registry = KPIRegistry()
    facts_store = FactsStore()
    edgar_retriever = EdgarRetriever()
    sec_adapter = SECFactsAdapter()
    
    # Force strict mode for real data only
    import os
    os.environ['FINSIGHT_STRICT'] = 'true'
    logger.info("🚀 Using REAL FinSight components with STRICT MODE - no mocks allowed!")
else:
    # Use simplified implementations
    facts_store = SimpleFactsStore()
    edgar_retriever = SimpleEdgarRetriever()
    sec_adapter = None
    logger.warning("⚠️ Using mock FinSight components - real APIs not available")

class KPISearchRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    kpi: str = Field(..., description="KPI name (e.g., 'revenue', 'grossMargin')")
    freq: str = Field("Q", description="Frequency ('Q' for quarterly, 'A' for annual)")
    limit: int = Field(12, ge=1, le=50, description="Maximum number of periods")
    ttm: bool = Field(False, description="Calculate trailing twelve months")

class FilingSearchRequest(BaseModel):
    ticker: Optional[str] = Field(None, description="Company ticker symbol (e.g., AAPL)")
    cik: Optional[str] = Field(None, description="Company CIK number")
    form: str = Field("10-K", description="Form type (10-K, 10-Q, 8-K)")
    year_range: Tuple[int, int] = Field((2020, 2024), description="Year range (start, end)")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")

@router.get("/health")
async def finsight_health():
    """FinSight module health check"""
    return {
        "module": "finsight",
        "status": "healthy" if FINSIGHT_AVAILABLE else "unavailable",
        "components": {
            "edgar_retriever": FINSIGHT_AVAILABLE,
            "facts_store": FINSIGHT_AVAILABLE,
            "kpi_registry": FINSIGHT_AVAILABLE
        },
        "endpoints": [
            "GET /finsight/health",
            "GET /finsight/kpis/{ticker}/{kpi}",
            "POST /finsight/kpis/search",
            "POST /finsight/filings/search"
        ],
        "timestamp": date.today().isoformat()
    }

@router.get("/kpis/{ticker}/{kpi}")
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
    if not FINSIGHT_AVAILABLE:
        raise HTTPException(status_code=503, detail="FinSight components not available")
    
    try:
        logger.info(
            "Finance KPI request",
            ticker=ticker,
            kpi=kpi,
            freq=freq,
            limit=limit,
            ttm=ttm,
            segment=segment
        )
        
        # FIRST: Try to get real data from SEC
        if sec_adapter:
            logger.info(f"🔍 Fetching REAL SEC data for {ticker} {kpi}")
            
            try:
                # Get real SEC data using the correct method
                sec_fact = await sec_adapter.get_fact(ticker, kpi)
                
                if sec_fact and "value" in sec_fact:
                    # Convert SEC fact to KPI data format
                    kpi_data = [{
                        "period": sec_fact.get("period", "Unknown"),
                        "value": sec_fact.get("value", 0),
                        "unit": sec_fact.get("unit", "USD"),
                        "accession": sec_fact.get("citation", {}).get("accession", "N/A"),
                        "source": "SEC EDGAR (Real Data)",
                        "url": sec_fact.get("citation", {}).get("url", "N/A")
                    }]
                    
                    logger.info(f"✅ Found real SEC data for {ticker} {kpi}: ${sec_fact.get('value', 0):,}")
                    real_data = True
                else:
                    logger.warning(f"⚠️ No SEC data found for {ticker} {kpi}, using facts store")
                    kpi_data = await facts_store.get_kpi_series(ticker, kpi, freq, limit, ttm, segment)
                    real_data = False
            except Exception as sec_error:
                logger.warning(f"⚠️ SEC adapter error: {sec_error}, using facts store")
                kpi_data = await facts_store.get_kpi_series(ticker, kpi, freq, limit, ttm, segment)
                real_data = False
        else:
            # FALLBACK: Use facts store if SEC adapter not available
            logger.warning(f"⚠️ SEC adapter not available, using facts store")
            kpi_data = await facts_store.get_kpi_series(ticker, kpi, freq, limit, ttm, segment)
            real_data = False
        
        return {
            "ticker": ticker,
            "kpi": kpi,
            "frequency": freq,
            "data": kpi_data,
            "real_data": real_data,
            "source": "SEC EDGAR (Real Data)" if real_data else "FinSight Facts Store (Fallback)",
            "metadata": {
                "total_periods": len(kpi_data),
                "ttm_calculated": ttm,
                "segment_filter": segment,
                "data_source": "real_sec" if real_data else "fallback"
            }
        }
        
    except Exception as e:
        logger.error(f"KPI request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve KPI data: {str(e)}")

@router.post("/kpis/search")
async def search_kpis(req: KPISearchRequest, request: Request):
    """
    Search for KPI data with advanced filtering
    """
    if not FINSIGHT_AVAILABLE:
        raise HTTPException(status_code=503, detail="FinSight components not available")
    
    try:
        logger.info(
            "Finance KPI search request",
            ticker=req.ticker,
            kpi=req.kpi,
            freq=req.freq,
            limit=req.limit
        )
        
        # Search KPI data
        results = await facts_store.search_kpis(
            ticker=req.ticker,
            kpi=req.kpi,
            freq=req.freq,
            limit=req.limit,
            ttm=req.ttm
        )
        
        return {
            "query": req.dict(),
            "results": results,
            "count": len(results),
            "timestamp": date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"KPI search failed: {e}")
        raise HTTPException(status_code=500, detail=f"KPI search failed: {str(e)}")

@router.post("/filings/search")
async def search_filings(req: FilingSearchRequest, request: Request):
    """
    Search SEC filings in EDGAR database
    
    Search for SEC filings by company ticker/CIK, form type, and date range.
    Returns basic filing information including accession numbers and URLs.
    """
    if not FINSIGHT_AVAILABLE:
        raise HTTPException(status_code=503, detail="FinSight components not available")
    
    try:
        logger.info(
            "Finance filing search request",
            ticker=req.ticker,
            cik=req.cik,
            form=req.form,
            year_range=req.year_range,
            limit=req.limit
        )
        
        # Search filings using Edgar retriever
        filings = await edgar_retriever.search_filings(
            ticker=req.ticker,
            cik=req.cik,
            form=req.form,
            year_range=req.year_range,
            limit=req.limit
        )
        
        return {
            "query": req.dict(),
            "filings": filings,
            "count": len(filings),
            "timestamp": date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Filing search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Filing search failed: {str(e)}")

@router.get("/status")
async def finsight_status(settings: Settings = Depends(get_settings)):
    """Get FinSight module status and configuration"""
    return {
        "module": "finsight",
        "enabled": FINSIGHT_AVAILABLE,
        "status": "healthy" if FINSIGHT_AVAILABLE else "unavailable",
        "configuration": {
            "edgar_enabled": FINSIGHT_AVAILABLE,
            "facts_store_enabled": FINSIGHT_AVAILABLE,
            "kpi_registry_enabled": FINSIGHT_AVAILABLE
        },
        "endpoints": [
            "GET /finsight/health",
            "GET /finsight/status", 
            "GET /finsight/kpis/{ticker}/{kpi}",
            "POST /finsight/kpis/search",
            "POST /finsight/filings/search"
        ],
        "timestamp": date.today().isoformat()
    }
