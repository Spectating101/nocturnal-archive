"""
SEC EDGAR Submissions API adapter
"""

import asyncio
import aiohttp
import structlog
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import SourceAdapter, AdapterOutput, Provenance, SourceUnavailableError, ParseError

logger = structlog.get_logger(__name__)

class SECSubmissionsAdapter(SourceAdapter):
    """Adapter for SEC EDGAR Submissions API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 6.0  # 10 requests per minute = 6 seconds between requests
    
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
        Search for company filings
        
        Args:
            cik: Company CIK number (required)
            
        Returns:
            AdapterOutput with company filings index
        """
        if not self.session:
            raise RuntimeError("SECSubmissionsAdapter must be used as async context manager")
        
        cik = kwargs.get("cik")
        if not cik:
            raise ValueError("CIK is required for SEC submissions search")
        
        # Pad CIK to 10 digits
        cik_padded = str(cik).zfill(10)
        
        try:
            # Build URL
            url = f"{self.base_url}{cik_padded}.json"
            
            logger.info(
                "Searching SEC submissions",
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
                    raise SourceUnavailableError(f"SEC submissions failed: {response.status}")
                
                raw_data = await response.json()
            
            # Parse response
            parsed_data = await self.parse(raw_data)
            
            logger.info(
                "SEC submissions search completed",
                cik=cik,
                filings_found=len(parsed_data["data"].get("filings", {}).get("recent", {}).get("form", []))
            )
            
            return parsed_data
            
        except Exception as e:
            logger.error(
                "SEC submissions search failed",
                cik=cik,
                error=str(e)
            )
            raise
    
    async def fetch(self, **kwargs) -> AdapterOutput:
        """
        Fetch specific submission data
        
        Args:
            cik: Company CIK number (required)
            
        Returns:
            AdapterOutput with submission data
        """
        # For submissions API, fetch is the same as search
        return await self.search(**kwargs)
    
    async def parse(self, raw: Any) -> AdapterOutput:
        """
        Parse SEC submissions JSON into normalized format
        
        Args:
            raw: Raw JSON from SEC submissions API
            
        Returns:
            AdapterOutput with parsed filings index
        """
        try:
            if not isinstance(raw, dict):
                raise ParseError("Expected JSON object from SEC submissions API")
            
            # Extract company info
            company_info = raw.get("cik", {})
            company_name = company_info.get("title", "Unknown Company")
            cik = company_info.get("cik", "")
            
            # Extract filings
            filings_data = raw.get("filings", {}).get("recent", {})
            
            # Build normalized filings list
            filings = []
            form_types = filings_data.get("form", [])
            filing_dates = filings_data.get("filingDate", [])
            accession_numbers = filings_data.get("accessionNumber", [])
            primary_documents = filings_data.get("primaryDocument", [])
            
            # Create provenance for each filing
            provenance_list = []
            
            for i in range(len(form_types)):
                if i < len(accession_numbers):
                    accession = accession_numbers[i]
                    form_type = form_types[i] if i < len(form_types) else "Unknown"
                    filing_date = filing_dates[i] if i < len(filing_dates) else None
                    primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                    
                    # Build filing info
                    filing_info = {
                        "accession": accession,
                        "form": form_type,
                        "filing_date": filing_date,
                        "primary_doc_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{primary_doc}" if primary_doc else None,
                        "company_name": company_name,
                        "cik": cik
                    }
                    filings.append(filing_info)
                    
                    # Create provenance
                    provenance = self._create_provenance(
                        url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{primary_doc}",
                        accession=accession,
                        period=filing_date
                    )
                    provenance_list.append(provenance)
            
            # Build normalized output
            normalized_data = {
                "company_name": company_name,
                "cik": cik,
                "filings": filings,
                "total_filings": len(filings),
                "last_updated": raw.get("lastUpdated", None)
            }
            
            # Metadata
            metadata = {
                "source": "sec_submissions",
                "parsed_at": datetime.now().isoformat(),
                "total_filings": len(filings),
                "form_types": list(set(form_types)),
                "date_range": {
                    "earliest": min(filing_dates) if filing_dates else None,
                    "latest": max(filing_dates) if filing_dates else None
                }
            }
            
            return AdapterOutput(
                data=normalized_data,
                provenance=provenance_list,
                source_version=self._get_source_version(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to parse SEC submissions", error=str(e))
            raise ParseError(f"Failed to parse SEC submissions: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SEC submissions API health"""
        try:
            import time
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
            url = f"{self.base_url}{test_cik}.json"
            
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
