"""
SEC EDGAR Company Facts Adapter
Fetches and normalizes XBRL financial facts from SEC EDGAR
"""

import structlog
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = structlog.get_logger(__name__)

class EdgarCompanyFactsAdapter:
    """Adapter for SEC EDGAR Company Facts API"""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.session = None
        self.cache = {}
        
        # Ticker to CIK mapping (simplified for demo)
        self.ticker_to_cik = {
            "AAPL": "0000320193",
            "MSFT": "0000789019", 
            "NVDA": "0001045810",
            "AMZN": "0001018724",
            "ASML": "0001038369",
            "TSM": "0001046179",
            "SAP": "0001031314",
            "SHEL": "0001302001"
        }
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "FinSight Financial Data (contact@nocturnal.dev)"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def fetch_companyfacts(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch company facts for a ticker
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Normalized company facts data
        """
        try:
            cik = self.ticker_to_cik.get(ticker.upper())
            if not cik:
                raise ValueError(f"Unknown ticker: {ticker}")
            
            # Check cache first
            cache_key = f"companyfacts:{cik}"
            if cache_key in self.cache:
                logger.debug("Company facts cache hit", ticker=ticker, cik=cik)
                return self.cache[cache_key]
            
            session = await self._get_session()
            url = f"{self.base_url}/CIK{cik}.json"
            
            logger.info("Fetching company facts", ticker=ticker, cik=cik, url=url)
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Normalize the data
                    normalized = self._normalize_companyfacts(data, ticker)
                    
                    # Cache for 1 hour
                    self.cache[cache_key] = normalized
                    
                    logger.info("Company facts fetched successfully", 
                              ticker=ticker, facts_count=len(normalized.get("facts", {})))
                    
                    return normalized
                else:
                    logger.error("Failed to fetch company facts", 
                               ticker=ticker, status=response.status)
                    raise Exception(f"EDGAR API error: {response.status}")
                    
        except Exception as e:
            logger.error("Company facts fetch failed", ticker=ticker, error=str(e))
            raise
    
    def _normalize_companyfacts(self, data: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """Normalize EDGAR company facts data"""
        
        normalized = {
            "ticker": ticker.upper(),
            "cik": data.get("cik"),
            "entityName": data.get("entityName"),
            "sic": data.get("sic"),
            "sicDescription": data.get("sicDescription"),
            "facts": {}
        }
        
        # Process US-GAAP facts
        us_gaap = data.get("facts", {}).get("us-gaap", {})
        for concept, concept_data in us_gaap.items():
            if "units" in concept_data:
                for unit, periods in concept_data["units"].items():
                    for period_data in periods:
                        fact_key = f"{concept}_{unit}_{period_data.get('form', '10-K')}_{period_data.get('filed', '')}"
                        
                        normalized["facts"][fact_key] = {
                            "concept": concept,
                            "unit": unit,
                            "value": period_data.get("val"),
                            "period": period_data.get("end"),
                            "filed": period_data.get("filed"),
                            "form": period_data.get("form"),
                            "accession": period_data.get("accn"),
                            "fiscal_year": period_data.get("fy"),
                            "fiscal_period": period_data.get("fp"),
                            "frame": period_data.get("frame")
                        }
        
        return normalized
    
    async def get_fact(self, ticker: str, concept: str, period: str = "latest") -> Optional[Dict[str, Any]]:
        """
        Get a specific financial fact
        
        Args:
            ticker: Company ticker
            concept: XBRL concept name
            period: Period (e.g., "2024-12-31", "latest")
            
        Returns:
            Fact data with normalization
        """
        try:
            facts_data = await self.fetch_companyfacts(ticker)
            
            # Find matching facts
            matching_facts = []
            for fact_key, fact_data in facts_data["facts"].items():
                if concept.lower() in fact_data["concept"].lower():
                    matching_facts.append(fact_data)
            
            if not matching_facts:
                return None
            
            # Sort by period (most recent first)
            matching_facts.sort(key=lambda x: x.get("period", ""), reverse=True)
            
            if period == "latest":
                return matching_facts[0]
            else:
                # Find exact period match
                for fact in matching_facts:
                    if fact.get("period") == period:
                        return fact
                
                # Return latest if no exact match
                return matching_facts[0]
                
        except Exception as e:
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            return None
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

# Global instance
edgar_adapter = EdgarCompanyFactsAdapter()

def get_edgar_adapter() -> EdgarCompanyFactsAdapter:
    """Get global EDGAR adapter instance"""
    return edgar_adapter

