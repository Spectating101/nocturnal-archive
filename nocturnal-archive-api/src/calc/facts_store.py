"""
Financial Facts Store
Manages financial facts with concept mapping and normalization
"""

import structlog
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from src.adapters.sec_facts import get_sec_facts_adapter
from src.calc.normalization import get_normalizer
from src.calc.fx import get_fx_normalizer

logger = structlog.get_logger(__name__)

class FactsStore:
    """Store for financial facts with concept mapping"""
    
    def __init__(self):
        self.concept_map = self._load_concept_map()
        self.sec_adapter = get_sec_facts_adapter()
        self.fx_normalizer = get_fx_normalizer()
        self.unit_normalizer = get_normalizer(self.fx_normalizer)
        
    def _load_concept_map(self) -> Dict[str, Any]:
        """Load concept mapping from YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "concept_map.yml")
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error("Failed to load concept map", error=str(e))
            return {}
    
    def _map_concept(self, kpi_name: str, standard: str = "us_gaap") -> List[str]:
        """Map internal KPI name to XBRL concepts"""
        concept_info = self.concept_map.get("concepts", {}).get(kpi_name, {})
        return concept_info.get(standard, [])
    
    async def get_fact(
        self,
        ticker: str,
        kpi_name: str,
        period: str = "latest",
        freq: str = "Q"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a financial fact with concept mapping and normalization
        
        Args:
            ticker: Company ticker
            kpi_name: Internal KPI name (e.g., "revenue", "grossProfit")
            period: Period (e.g., "2024-12-31", "latest")
            freq: Frequency (Q, A)
            
        Returns:
            Normalized fact data
        """
        try:
            # Map KPI to XBRL concepts
            concepts = self._map_concept(kpi_name, "us_gaap")
            
            if not concepts:
                logger.warning("No concepts found for KPI", kpi_name=kpi_name)
                return None
            
            # Use SEC adapter to get fact
            fact_data = await self.sec_adapter.get_fact(ticker, kpi_name, period=period, freq=freq)
            
            if fact_data:
                logger.debug("Fact retrieved and normalized", 
                           ticker=ticker, kpi=kpi_name,
                           value=fact_data.get("value"))
                
                return fact_data
            
            logger.warning("No data found for any concept", 
                          ticker=ticker, kpi=kpi_name, concepts=concepts)
            return None
            
        except Exception as e:
            logger.error("Failed to get fact", 
                        ticker=ticker, kpi=kpi_name, error=str(e))
            return None
    
    async def _normalize_fact(
        self,
        fact_data: Dict[str, Any],
        ticker: str,
        kpi_name: str
    ) -> Dict[str, Any]:
        """Normalize a financial fact"""
        
        # Extract basic data
        value = fact_data.get("value")
        unit = fact_data.get("unit", "USD")
        period = fact_data.get("period")
        accession = fact_data.get("accession")
        
        # Normalize unit and scale
        normalization = self.unit_normalizer.normalize_fact(
            value=value,
            unit=unit,
            period_end=period,
            target_currency="USD",
            target_scale="U"
        )
        
        # Build citation
        citation = {
            "source": "SEC EDGAR",
            "accession": accession,
            "url": f"https://www.sec.gov/Archives/edgar/data/{self.sec_adapter.ticker_to_cik.get(ticker, '')}/{accession}/",
            "concept": fact_data.get("concept"),
            "unit": unit,
            "scale": normalization.get("scaling_applied", {}).get("source_scale", "U"),
            "fx_used": normalization.get("fx_conversion"),
            "amended": False,  # TODO: Implement amendment detection
            "as_reported": True,
            "filed": fact_data.get("filed"),
            "form": fact_data.get("form")
        }
        
        return {
            "ticker": ticker,
            "kpi": kpi_name,
            "value": normalization.get("normalized_value", value),
            "unit": "USD",
            "period": period,
            "citation": citation,
            "raw_data": fact_data,
            "normalization": normalization
        }
    
    async def get_series(
        self,
        ticker: str,
        kpi_name: str,
        freq: str = "Q",
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Get a time series of financial facts
        
        Args:
            ticker: Company ticker
            kpi_name: Internal KPI name
            freq: Frequency (Q, A)
            limit: Number of periods
            
        Returns:
            List of normalized facts
        """
        try:
            # For now, return mock data with proper structure
            # In production, this would fetch multiple periods from EDGAR
            
            # Use SEC adapter to get series
            series = await self.sec_adapter.get_series(ticker, kpi_name, freq, limit)
            
            logger.info("Series generated", 
                       ticker=ticker, kpi=kpi_name, periods=len(series))
            
            return series
            
        except Exception as e:
            logger.error("Failed to get series", 
                        ticker=ticker, kpi=kpi_name, error=str(e))
            return []
    
    def get_derived_metrics(self) -> Dict[str, Any]:
        """Get available derived metrics"""
        return self.concept_map.get("derived_metrics", {})
    
    def get_ttm_metrics(self) -> List[str]:
        """Get metrics that support TTM calculation"""
        return self.concept_map.get("ttm_metrics", [])

# Global instance
facts_store = FactsStore()

def get_facts_store() -> FactsStore:
    """Get global facts store instance"""
    return facts_store
