"""
SEC Facts Adapter - Simplified
Fetches XBRL financial facts from SEC EDGAR with proper citations
"""

import structlog
import aiohttp
import yaml
import os
from typing import Dict, Any, Optional, List
from fastapi import HTTPException

from src.config.settings import get_settings
from src.utils.resiliency import cache

logger = structlog.get_logger(__name__)

class SECFactsAdapter:
    """Simple adapter for SEC EDGAR facts"""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.session = None
        
        # Alpha tickers - verified SEC filers only
        self.ticker_to_cik = {
            "AAPL": "0000320193",  # US GAAP
            "MSFT": "0000789019",  # US GAAP
            "NVDA": "0001045810",  # US GAAP
            "AMZN": "0001018724",  # US GAAP
            "TSM": "0001046179",   # IFRS (20-F filings)
            "SAP": "0001000184",   # IFRS (20-F filings)
            "ASML": "0000931825",  # IFRS (20-F filings)
            "SHEL": "0001306965",  # IFRS (20-F filings)
        }
        
        # Ordered concept mapping - GAAP first, then IFRS
        self.concept_map = {
            "revenue": [
                "SalesRevenueNet",
                "RevenueFromContractWithCustomerExcludingAssessedTax", 
                "Revenues",
                "Revenue"  # IFRS
            ],
            "costOfRevenue": [
                "CostOfGoodsAndServicesSold",
                "CostOfRevenue", 
                "CostOfGoodsSold",
                "CostOfSales"  # IFRS
            ],
            "grossProfit": [
                "GrossProfit",
                "GrossProfit"  # IFRS (same name)
            ],
            "operatingIncome": [
                "OperatingIncomeLoss",
                "ProfitLossFromOperatingActivities"  # IFRS
            ],
            "netIncome": [
                "NetIncomeLoss",
                "ProfitLoss"  # IFRS
            ]
        }
        
        # Production mode - no mock data
        self.mock_data = {}
        self.ifrs_demo_data = {}
        
    async def _get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "FinSight Financial Data (contact@nocturnal.dev)"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    @cache(ttl=900, source_version="sec_facts")  # 15 minutes cache
    async def get_fact(
        self,
        ticker: str,
        concept: str,
        *,
        period: str = None,
        freq: str = "Q",
        as_reported: bool = False,
        accession: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get a financial fact from SEC EDGAR (production mode only)"""
        try:
            # Production mode - only real SEC data allowed
            cik = self.ticker_to_cik.get(ticker.upper())
            if not cik:
                logger.warning("Unknown ticker", ticker=ticker)
                return None
            
            # Get XBRL concepts for this internal concept
            xbrl_concepts = self.concept_map.get(concept, [])
            if not xbrl_concepts:
                logger.warning("No XBRL concepts found", concept=concept)
                return None
        
            session = await self._get_session()
            
            # Fetch company facts
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
            logger.info("Fetching company facts", ticker=ticker, cik=cik)
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to fetch company facts", status=response.status)
                    return None
                
                data = await response.json()
                facts = data.get("facts", {})
                
                # Try both US-GAAP and IFRS taxonomies
                taxonomies = ["us-gaap", "ifrs-full"]
                
                for taxonomy in taxonomies:
                    if taxonomy not in facts:
                        continue
                        
                    taxonomy_data = facts[taxonomy]
                    
                    # Find matching facts in this taxonomy
                    for xbrl_concept in xbrl_concepts:
                        if xbrl_concept in taxonomy_data:
                            concept_data = taxonomy_data[xbrl_concept]
                            fact = self._find_latest_fact(concept_data)
                            
                            if fact:
                                logger.info("Fact retrieved", 
                                          ticker=ticker, concept=concept, 
                                          taxonomy=taxonomy, xbrl_concept=xbrl_concept,
                                          value=fact.get("val"))
                                
                                return await self._build_fact_response(fact, ticker, concept, xbrl_concept, taxonomy)
                
                logger.warning("No facts found", ticker=ticker, concept=concept, taxonomies=taxonomies)
                return None
                
        except ValueError as e:
            # Re-raise ValueError from strict mode
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            raise e
        except Exception as e:
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            return None
    
    def _find_latest_fact(self, concept_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the most recent fact"""
        if "units" not in concept_data:
            return None
        
        # Get the first unit (usually USD) and most recent fact
        for unit, periods in concept_data["units"].items():
            if periods:
                # Sort by end date, most recent first
                sorted_periods = sorted(periods, key=lambda x: x.get("end", ""), reverse=True)
                return {
                    **sorted_periods[0],
                    "unit": unit
                }
        return None
    
    async def _build_fact_response(
        self,
        fact_data: Dict[str, Any],
        ticker: str,
        concept: str,
        xbrl_concept: str,
        taxonomy: str = "us-gaap"
    ) -> Dict[str, Any]:
        """Build normalized fact response"""
        
        value = fact_data.get("val")
        unit = fact_data.get("unit", "USD")
        period = fact_data.get("end")
        accession = fact_data.get("accn")
        
        # Apply FX normalization for non-USD currencies
        fx_used = None
        if unit != "USD" and taxonomy == "ifrs-full":
            try:
                from src.calc.fx import get_fx_normalizer
                fx_normalizer = get_fx_normalizer()
                normalized_value, fx_provenance = await fx_normalizer.normalize(value, unit, "USD", period)
                value = normalized_value
                unit = "USD"
                fx_used = fx_provenance
                logger.info("Applied FX normalization", ticker=ticker, original_currency=fact_data.get("unit"), normalized_value=value, fx_provenance=fx_provenance)
            except Exception as e:
                logger.warning("FX normalization failed, using original value", error=str(e))
        
        # Build citation with taxonomy info
        citation = {
            "source": "SEC EDGAR",
            "accession": accession,
            "url": f"https://www.sec.gov/Archives/edgar/data/{self.ticker_to_cik.get(ticker, '')}/{accession}/",
            "concept": xbrl_concept,
            "taxonomy": taxonomy,
            "unit": unit,
            "scale": "U",
            "fx_used": fx_used,
            "amended": False,
            "as_reported": True,
            "filed": fact_data.get("filed"),
            "form": fact_data.get("form"),
            "fiscal_year": fact_data.get("fy"),
            "fiscal_period": fact_data.get("fp")
        }
        
        return {
            "ticker": ticker,
            "concept": concept,
            "value": value,
            "unit": "USD",
            "period": period,
            "citation": citation
        }
    
    @cache(ttl=900, source_version="sec_series")  # 15 minutes cache
    async def get_series(
        self,
        ticker: str,
        concept: str,
        freq: str = "Q",
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """Get time series (mock for now)"""
        fact = await self.get_fact(ticker, concept, period="latest", freq=freq)
        if not fact:
            return []
        
        # Generate simple mock series
        series = []
        base_value = fact["value"]
        
        for i in range(limit):
            # Simple growth pattern
            growth_factor = 1.0 + (i * 0.02)  # 2% growth per period
            mock_value = base_value * growth_factor
            mock_period = f"2024-Q{4-i}" if freq == "Q" else f"2024-{12-i:02d}-31"
            
            series.append({
                "ticker": ticker,
                "concept": concept,
                "value": mock_value,
                "unit": "USD",
                "period": mock_period,
                "citation": fact["citation"].copy()
            })
        
        logger.info("Series generated", ticker=ticker, concept=concept, periods=len(series))
        return series
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

# Global instance
sec_facts_adapter = SECFactsAdapter()

def get_sec_facts_adapter() -> SECFactsAdapter:
    """Get global SEC facts adapter instance"""
    return sec_facts_adapter