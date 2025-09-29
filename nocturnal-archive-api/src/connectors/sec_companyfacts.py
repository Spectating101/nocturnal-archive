"""
SEC EDGAR Company Facts API adapter
"""

import asyncio
import aiohttp
import structlog
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import SourceAdapter, AdapterOutput, Provenance, SourceUnavailableError, ParseError

logger = structlog.get_logger(__name__)

class SECCompanyFactsAdapter(SourceAdapter):
    """Adapter for SEC EDGAR Company Facts API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 6.0  # 10 requests per minute
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Nocturnal Archive Research Tool (contact@nocturnal.dev)",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Respect SEC rate limiting guidelines"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug("SEC rate limit sleep", sleep_time=sleep_time)
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def search(self, **kwargs) -> AdapterOutput:
        """
        Search for company facts
        
        Args:
            cik: Company CIK number (required)
            
        Returns:
            AdapterOutput with company facts data
        """
        if not self.session:
            raise RuntimeError("SECCompanyFactsAdapter must be used as async context manager")
        
        cik = kwargs.get("cik")
        if not cik:
            raise ValueError("CIK is required for SEC company facts search")
        
        # Pad CIK to 10 digits
        cik_padded = str(cik).zfill(10)
        
        try:
            # Build URL
            url = f"{self.base_url}CIK{cik_padded}.json"
            
            logger.info(
                "Fetching SEC company facts",
                cik=cik,
                cik_padded=cik_padded,
                url=url
            )
            
            # Apply rate limiting
            await self._rate_limit()
            
            # Make request
            async with self.session.get(url) as response:
                if response.status == 403 or response.status == 429:
                    raise SourceUnavailableError(f"SEC rate limited: {response.status}")
                
                if response.status != 200:
                    raise SourceUnavailableError(f"SEC company facts failed: {response.status}")
                
                raw_data = await response.json()
            
            # Parse response
            parsed_data = await self.parse(raw_data)
            
            logger.info(
                "SEC company facts fetch completed",
                cik=cik,
                concepts_found=len(parsed_data["data"].get("facts", {}).get("us-gaap", {}))
            )
            
            return parsed_data
            
        except Exception as e:
            logger.error(
                "SEC company facts fetch failed",
                cik=cik,
                error=str(e)
            )
            raise
    
    async def fetch(self, **kwargs) -> AdapterOutput:
        """Fetch is the same as search for company facts"""
        return await self.search(**kwargs)
    
    async def parse(self, raw: Any) -> AdapterOutput:
        """
        Parse SEC company facts JSON into normalized format
        
        Args:
            raw: Raw JSON from SEC company facts API
            
        Returns:
            AdapterOutput with parsed XBRL facts
        """
        try:
            if not isinstance(raw, dict):
                raise ParseError("Expected JSON object from SEC company facts API")
            
            # Extract company info
            entity_name = raw.get("entityName", "Unknown Company")
            cik = raw.get("cik", "")
            sic = raw.get("sic", "")
            sic_description = raw.get("sicDescription", "")
            tickers = raw.get("tickers", [])
            
            # Extract facts by taxonomy
            facts_data = raw.get("facts", {})
            us_gaap_facts = facts_data.get("us-gaap", {})
            dei_facts = facts_data.get("dei", {})
            
            # Build normalized facts structure
            normalized_facts = {}
            provenance_list = []
            
            # Process US-GAAP facts
            for concept, concept_data in us_gaap_facts.items():
                if not isinstance(concept_data, dict) or "units" not in concept_data:
                    continue
                
                concept_facts = []
                for unit, unit_data in concept_data["units"].items():
                    if not isinstance(unit_data, list):
                        continue
                    
                    for fact in unit_data:
                        if not isinstance(fact, dict):
                            continue
                        
                        # Extract fact details
                        value = fact.get("val")
                        start_date = fact.get("start")
                        end_date = fact.get("end")
                        form = fact.get("form")
                        accession = fact.get("accn")
                        fy = fact.get("fy")
                        fp = fact.get("fp")  # fiscal period
                        filed = fact.get("filed")
                        frame = fact.get("frame")
                        
                        # Build fact object
                        fact_obj = {
                            "concept": concept,
                            "value": value,
                            "unit": unit,
                            "start_date": start_date,
                            "end_date": end_date,
                            "form": form,
                            "accession": accession,
                            "fiscal_year": fy,
                            "fiscal_period": fp,
                            "filed_date": filed,
                            "frame": frame,
                            "dimensions": self._extract_dimensions(fact)
                        }
                        
                        concept_facts.append(fact_obj)
                        
                        # Create provenance
                        provenance = self._create_provenance(
                            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                            accession=accession,
                            concept=concept,
                            period=end_date,
                            unit=unit,
                            fragment_id=frame
                        )
                        provenance_list.append(provenance)
                
                if concept_facts:
                    normalized_facts[concept] = concept_facts
            
            # Build normalized output
            normalized_data = {
                "entity_name": entity_name,
                "cik": cik,
                "sic": sic,
                "sic_description": sic_description,
                "tickers": tickers,
                "facts": normalized_facts,
                "taxonomies": list(facts_data.keys()),
                "total_concepts": len(normalized_facts)
            }
            
            # Metadata
            metadata = {
                "source": "sec_companyfacts",
                "parsed_at": datetime.now().isoformat(),
                "total_concepts": len(normalized_facts),
                "taxonomies": list(facts_data.keys()),
                "entity_info": {
                    "name": entity_name,
                    "cik": cik,
                    "sic": sic,
                    "tickers": tickers
                }
            }
            
            return AdapterOutput(
                data=normalized_data,
                provenance=provenance_list,
                source_version=self._get_source_version(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to parse SEC company facts", error=str(e))
            raise ParseError(f"Failed to parse SEC company facts: {str(e)}")
    
    def _extract_dimensions(self, fact: Dict[str, Any]) -> Dict[str, str]:
        """Extract dimension information from fact"""
        dimensions = {}
        
        # Common dimensions in SEC XBRL
        dimension_keys = [
            "Segment", "BusinessSegment", "ProductOrService", "GeographicArea",
            "StatementScenario", "StatementGeographicalAxis", "StatementBusinessSegmentAxis"
        ]
        
        for key in dimension_keys:
            if key in fact:
                dimensions[key] = fact[key]
        
        return dimensions
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SEC company facts API health"""
        try:
            start_time = time.time()
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": "Nocturnal Archive Research Tool (contact@nocturnal.dev)",
                        "Accept": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            
            # Test with a known CIK (Apple)
            test_cik = "0000320193"
            url = f"{self.base_url}CIK{test_cik}.json"
            
            async with self.session.get(url) as response:
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    return {
                        "source_id": self.source_id,
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "source_id": self.source_id,
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "latency_ms": round(latency_ms, 2),
                        "timestamp": time.time()
                    }
                    
        except Exception as e:
            return {
                "source_id": self.source_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

