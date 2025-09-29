"""
Financial Facts Store
Normalizes and indexes XBRL facts for efficient retrieval
"""

import structlog
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
import json

logger = structlog.get_logger(__name__)

class PeriodType(Enum):
    DURATION = "duration"
    INSTANT = "instant"

@dataclass
class Fact:
    """Represents a single financial fact with provenance"""
    concept: str
    value: float
    unit: str
    period: str
    period_type: PeriodType
    accession: str
    fragment_id: Optional[str]
    url: str
    dimensions: Dict[str, str]
    quality_flags: List[str]
    company_name: str
    cik: str

class FactsStore:
    """Store for financial facts with indexing and retrieval"""
    
    def __init__(self):
        self.facts_by_company: Dict[str, Dict[str, List[Fact]]] = {}
        self.facts_by_concept: Dict[str, List[Fact]] = {}
        self.company_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def store_company_facts(self, company_data: Dict[str, Any]):
        """
        Store facts from SEC company facts API
        
        Args:
            company_data: Normalized data from SECCompanyFactsAdapter
        """
        try:
            cik = company_data.get("cik", "")
            company_name = company_data.get("entity_name", "")
            
            if not cik:
                logger.warning("No CIK found in company data")
                return
            
            logger.info(
                "Storing company facts",
                cik=cik,
                company_name=company_name,
                concepts_count=company_data.get("total_concepts", 0)
            )
            
            # Store company metadata
            self.company_metadata[cik] = {
                "company_name": company_name,
                "cik": cik,
                "sic": company_data.get("sic", ""),
                "sic_description": company_data.get("sic_description", ""),
                "tickers": company_data.get("tickers", []),
                "last_updated": datetime.now().isoformat()
            }
            
            # Initialize company facts storage
            if cik not in self.facts_by_company:
                self.facts_by_company[cik] = {}
            
            # Process facts
            facts_data = company_data.get("facts", {})
            facts_stored = 0
            
            for concept, concept_facts in facts_data.items():
                if not isinstance(concept_facts, list):
                    continue
                
                # Initialize concept storage
                if concept not in self.facts_by_company[cik]:
                    self.facts_by_company[cik][concept] = []
                
                # Store facts for this concept
                for fact_data in concept_facts:
                    fact = self._create_fact_from_data(fact_data, concept, cik, company_name)
                    if fact:
                        self.facts_by_company[cik][concept].append(fact)
                        
                        # Also store by concept for cross-company queries
                        if concept not in self.facts_by_concept:
                            self.facts_by_concept[concept] = []
                        self.facts_by_concept[concept].append(fact)
                        
                        facts_stored += 1
            
            logger.info(
                "Company facts stored",
                cik=cik,
                facts_stored=facts_stored,
                concepts_stored=len(facts_data)
            )
            
        except Exception as e:
            logger.error("Failed to store company facts", error=str(e))
            raise
    
    def _create_fact_from_data(
        self,
        fact_data: Dict[str, Any],
        concept: str,
        cik: str,
        company_name: str
    ) -> Optional[Fact]:
        """Create Fact object from raw fact data"""
        try:
            value = fact_data.get("value")
            if value is None:
                return None
            
            # Determine period type based on concept or data
            period_type = PeriodType.DURATION  # Default
            if "Assets" in concept or "Liabilities" in concept or "Equity" in concept:
                period_type = PeriodType.INSTANT
            
            # Build quality flags
            quality_flags = []
            if fact_data.get("restated"):
                quality_flags.append("restated")
            if fact_data.get("estimated"):
                quality_flags.append("estimated")
            
            fact = Fact(
                concept=concept,
                value=float(value),
                unit=fact_data.get("unit", "USD"),
                period=fact_data.get("end_date", ""),
                period_type=period_type,
                accession=fact_data.get("accession", ""),
                fragment_id=fact_data.get("frame"),
                url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{fact_data.get('accession', '')}",
                dimensions=fact_data.get("dimensions", {}),
                quality_flags=quality_flags,
                company_name=company_name,
                cik=cik
            )
            
            return fact
            
        except Exception as e:
            logger.warning("Failed to create fact", concept=concept, error=str(e))
            return None
    
    async def get_fact(
        self,
        ticker: str,
        concept: str,
        period: str = "latest",
        freq: str = "Q",
        ttm: bool = False,
        segment: Optional[str] = None
    ) -> Optional[Fact]:
        """
        Get a single fact for a company
        
        Args:
            ticker: Company ticker symbol
            concept: XBRL concept (e.g., "us-gaap:Assets")
            period: Period (e.g., "2024-Q4", "latest")
            freq: Frequency ("Q" for quarterly, "A" for annual)
            ttm: Whether to calculate trailing twelve months
            segment: Business segment filter
            
        Returns:
            Fact object or None if not found
        """
        try:
            # Resolve ticker to CIK
            cik = await self._resolve_ticker_to_cik(ticker)
            if not cik:
                logger.warning("Could not resolve ticker to CIK", ticker=ticker)
                return None
            
            # Get facts for company and concept
            company_facts = self.facts_by_company.get(cik, {})
            concept_facts = company_facts.get(concept, [])
            
            if not concept_facts:
                logger.warning("No facts found", ticker=ticker, concept=concept)
                return None
            
            # Filter by segment if specified
            if segment:
                concept_facts = [f for f in concept_facts if f.dimensions.get("BusinessSegment") == segment]
            
            # Filter by frequency
            if freq == "Q":
                concept_facts = [f for f in concept_facts if "Q" in f.period]
            elif freq == "A":
                concept_facts = [f for f in concept_facts if "Q" not in f.period]
            
            if not concept_facts:
                logger.warning("No facts found for frequency", ticker=ticker, concept=concept, freq=freq)
                return None
            
            # Sort by period (most recent first)
            concept_facts.sort(key=lambda x: x.period, reverse=True)
            
            # Get fact for specific period
            if period == "latest":
                fact = concept_facts[0]
            else:
                # Find exact period match
                fact = None
                for f in concept_facts:
                    if f.period == period:
                        fact = f
                        break
                
                if not fact:
                    logger.warning("Period not found", ticker=ticker, concept=concept, period=period)
                    return None
            
            # Handle TTM if requested
            if ttm and fact.period_type == PeriodType.DURATION:
                fact = await self._calculate_ttm(cik, concept, fact.period, segment)
            
            return fact
            
        except Exception as e:
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            return None
    
    async def get_facts_series(
        self,
        ticker: str,
        concept: str,
        freq: str = "Q",
        limit: int = 12,
        segment: Optional[str] = None
    ) -> List[Fact]:
        """
        Get a series of facts for a company
        
        Args:
            ticker: Company ticker symbol
            concept: XBRL concept
            freq: Frequency filter
            limit: Maximum number of facts to return
            segment: Business segment filter
            
        Returns:
            List of Fact objects sorted by period
        """
        try:
            # Resolve ticker to CIK
            cik = await self._resolve_ticker_to_cik(ticker)
            if not cik:
                return []
            
            # Get facts for company and concept
            company_facts = self.facts_by_company.get(cik, {})
            concept_facts = company_facts.get(concept, [])
            
            if not concept_facts:
                return []
            
            # Filter by segment if specified
            if segment:
                concept_facts = [f for f in concept_facts if f.dimensions.get("BusinessSegment") == segment]
            
            # Filter by frequency
            if freq == "Q":
                concept_facts = [f for f in concept_facts if "Q" in f.period]
            elif freq == "A":
                concept_facts = [f for f in concept_facts if "Q" not in f.period]
            
            # Sort by period (most recent first) and limit
            concept_facts.sort(key=lambda x: x.period, reverse=True)
            return concept_facts[:limit]
            
        except Exception as e:
            logger.error("Failed to get facts series", ticker=ticker, concept=concept, error=str(e))
            return []
    
    async def _resolve_ticker_to_cik(self, ticker: str) -> Optional[str]:
        """Resolve ticker symbol to CIK"""
        # For now, use a simple mapping - in production, this would use the identifier resolver
        ticker_to_cik = {
            "AAPL": "0000320193",
            "MSFT": "0000789019",
            "GOOGL": "0001652044",
            "AMZN": "0001018724",
            "TSLA": "0001318605",
            "META": "0001326801",
            "NVDA": "0001045810",
        }
        
        return ticker_to_cik.get(ticker.upper())
    
    async def _calculate_ttm(
        self,
        cik: str,
        concept: str,
        end_period: str,
        segment: Optional[str] = None
    ) -> Optional[Fact]:
        """Calculate trailing twelve months for a duration concept"""
        try:
            # Get last 4 quarters
            company_facts = self.facts_by_company.get(cik, {})
            concept_facts = company_facts.get(concept, [])
            
            if segment:
                concept_facts = [f for f in concept_facts if f.dimensions.get("BusinessSegment") == segment]
            
            # Filter for quarterly data
            quarterly_facts = [f for f in concept_facts if "Q" in f.period]
            quarterly_facts.sort(key=lambda x: x.period, reverse=True)
            
            if len(quarterly_facts) < 4:
                logger.warning("Insufficient quarterly data for TTM", cik=cik, concept=concept)
                return None
            
            # Sum last 4 quarters
            ttm_value = sum(f.value for f in quarterly_facts[:4])
            
            # Create TTM fact
            ttm_fact = Fact(
                concept=concept,
                value=ttm_value,
                unit=quarterly_facts[0].unit,
                period=f"TTM-{end_period}",
                period_type=PeriodType.DURATION,
                accession="TTM-CALCULATED",
                fragment_id=None,
                url="",
                dimensions=quarterly_facts[0].dimensions,
                quality_flags=["ttm_calculated"],
                company_name=quarterly_facts[0].company_name,
                cik=cik
            )
            
            return ttm_fact
            
        except Exception as e:
            logger.error("Failed to calculate TTM", cik=cik, concept=concept, error=str(e))
            return None
    
    def get_company_metadata(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company metadata by ticker"""
        cik = self._resolve_ticker_to_cik_sync(ticker)
        if cik:
            return self.company_metadata.get(cik)
        return None
    
    def _resolve_ticker_to_cik_sync(self, ticker: str) -> Optional[str]:
        """Synchronous ticker to CIK resolution"""
        ticker_to_cik = {
            "AAPL": "0000320193",
            "MSFT": "0000789019",
            "GOOGL": "0001652044",
            "AMZN": "0001018724",
            "TSLA": "0001318605",
            "META": "0001326801",
            "NVDA": "0001045810",
        }
        
        return ticker_to_cik.get(ticker.upper())
    
    def get_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the facts store"""
        total_facts = sum(
            len(concept_facts)
            for company_facts in self.facts_by_company.values()
            for concept_facts in company_facts.values()
        )
        
        return {
            "companies_count": len(self.facts_by_company),
            "concepts_count": len(self.facts_by_concept),
            "total_facts": total_facts,
            "companies": list(self.company_metadata.keys())
        }
    
    def clear_store(self):
        """Clear all stored facts"""
        self.facts_by_company.clear()
        self.facts_by_concept.clear()
        self.company_metadata.clear()
        logger.info("Facts store cleared")

