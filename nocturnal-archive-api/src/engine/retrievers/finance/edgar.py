"""
EDGAR SEC Filing Retriever
Retrieves and parses SEC filings from EDGAR database
"""

import asyncio
import aiohttp
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
import time

logger = structlog.get_logger(__name__)

@dataclass
class FilingInfo:
    """Information about a SEC filing"""
    accession: str
    form: str
    filing_date: date
    url: str
    company_name: str
    ticker: str
    cik: str

@dataclass
class FilingContent:
    """Parsed content of a SEC filing"""
    accession: str
    raw_html: str
    sections: Dict[str, str]  # section_name -> content
    tables: List[Dict[str, Any]]  # List of parsed tables
    metadata: Dict[str, Any]

class EdgarRetriever:
    """EDGAR SEC filing retriever"""
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.search_url = f"{self.base_url}/cgi-bin/browse-edgar"
        self.filing_url = f"{self.base_url}/Archives/edgar/data"
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1-2 req/sec as per SEC guidelines
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Nocturnal Archive Research Tool (contact@nocturnal.dev)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
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
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def search_filings(
        self,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        form: str = "10-K",
        year_range: Tuple[int, int] = (2020, 2024),
        limit: int = 10
    ) -> List[FilingInfo]:
        """
        Search for SEC filings
        
        Args:
            ticker: Company ticker symbol (e.g., "AAPL")
            cik: Company CIK number
            form: Form type (e.g., "10-K", "10-Q", "8-K")
            year_range: Tuple of (start_year, end_year)
            limit: Maximum number of results
            
        Returns:
            List of FilingInfo objects
        """
        if not self.session:
            raise RuntimeError("EdgarRetriever must be used as async context manager")
        
        try:
            # Build search parameters
            params = {
                "action": "getcompany",
                "type": form,
                "dateb": f"{year_range[1]}1231",  # End date
                "datea": f"{year_range[0]}0101",  # Start date
                "count": str(limit),
                "output": "atom"
            }
            
            if ticker:
                params["CIK"] = ticker
            elif cik:
                params["CIK"] = cik
            else:
                raise ValueError("Either ticker or cik must be provided")
            
            logger.info(
                "Searching EDGAR filings",
                ticker=ticker,
                cik=cik,
                form=form,
                year_range=year_range,
                limit=limit
            )
            
            # Apply rate limiting
            await self._rate_limit()
            
            # Make request with throttle-aware backoff (cap ~60s total)
            total_wait = 0.0
            backoff = 1.0
            while True:
                async with self.session.get(self.search_url, params=params) as response:
                    if response.status in (403, 429):
                        logger.warning("EDGAR throttle detected", status=response.status, backoff=backoff)
                        await asyncio.sleep(backoff)
                        total_wait += backoff
                        backoff = min(backoff * 2, 8.0)
                        if total_wait >= 60.0:
                            raise RuntimeError("edgar_throttled")
                        continue
                    if response.status != 200:
                        raise HTTPError(f"EDGAR search failed: {response.status}")
                    content = await response.text()
                    break
                
            # Parse results
            filings = self._parse_search_results(content, limit)
            
            logger.info(
                "EDGAR search completed",
                filings_found=len(filings)
            )
            
            return filings
            
        except Exception as e:
            logger.error(
                "EDGAR search failed",
                error=str(e),
                ticker=ticker,
                cik=cik,
                form=form
            )
            raise
    
    async def fetch_filing(self, accession: str) -> FilingContent:
        """
        Fetch and parse a specific SEC filing
        
        Args:
            accession: Filing accession number (e.g., "0000320193-24-000006")
            
        Returns:
            FilingContent object with parsed content
        """
        if not self.session:
            raise RuntimeError("EdgarRetriever must be used as async context manager")
        
        try:
            # Convert accession to URL
            # Format: 0000320193-24-000006 -> 0000320193/24-000006/0000320193-24-000006.txt
            cik = accession.split('-')[0]
            filing_url = f"{self.filing_url}/{cik}/{accession.replace('-', '')}/{accession}.txt"
            
            logger.info(
                "Fetching EDGAR filing",
                accession=accession,
                url=filing_url
            )
            
            # Apply rate limiting
            await self._rate_limit()
            
            # Fetch filing with throttle-aware backoff
            total_wait = 0.0
            backoff = 1.0
            while True:
                async with self.session.get(filing_url) as response:
                    if response.status in (403, 429):
                        logger.warning("EDGAR throttle detected", status=response.status, backoff=backoff)
                        await asyncio.sleep(backoff)
                        total_wait += backoff
                        backoff = min(backoff * 2, 8.0)
                        if total_wait >= 60.0:
                            raise RuntimeError("edgar_throttled")
                        continue
                    if response.status != 200:
                        raise HTTPError(f"Failed to fetch filing: {response.status}")
                    raw_html = await response.text()
                    break
            
            # Parse content
            content = self._parse_filing_content(accession, raw_html)
            
            logger.info(
                "EDGAR filing fetched and parsed",
                accession=accession,
                sections_found=len(content.sections),
                tables_found=len(content.tables)
            )
            
            return content
            
        except Exception as e:
            logger.error(
                "Failed to fetch EDGAR filing",
                error=str(e),
                accession=accession
            )
            raise
    
    def _parse_search_results(self, content: str, limit: int) -> List[FilingInfo]:
        """Parse EDGAR search results from XML/Atom feed"""
        try:
            from xml.etree import ElementTree as ET
            
            root = ET.fromstring(content)
            filings = []
            
            # Parse Atom feed entries
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry')[:limit]:
                try:
                    # Extract filing information
                    title = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    link = entry.find('.//{http://www.w3.org/2005/Atom}link')
                    updated = entry.find('.//{http://www.w3.org/2005/Atom}updated')
                    
                    if title is not None and link is not None:
                        title_text = title.text or ""
                        link_href = link.get('href', "")
                        
                        # Parse title to extract form and date
                        # Formats: "10-K - Apple Inc. ...", "10-K/A - ..."
                        form_match = re.search(r'^(\w+-\w+(?:/A)?)', title_text)
                        form = form_match.group(1) if form_match else "UNKNOWN"
                        
                        # Extract CIK from link
                        cik_match = re.search(r'/data/(\d+)/', link_href)
                        cik = cik_match.group(1) if cik_match else ""
                        
                        # Extract accession from link
                        accession_match = re.search(r'/([^/]+)\.txt$', link_href)
                        accession = accession_match.group(1) if accession_match else ""
                        
                        # Parse date
                        filing_date = datetime.now().date()
                        if updated is not None and updated.text:
                            try:
                                filing_date = datetime.fromisoformat(updated.text.replace('Z', '+00:00')).date()
                            except:
                                pass
                        
                        # Extract company name
                        company_match = re.search(r'-\s*([^(]+)\s*\(', title_text)
                        company_name = company_match.group(1).strip() if company_match else "Unknown Company"
                        
                        filings.append(FilingInfo(
                            accession=accession,
                            form=form,
                            filing_date=filing_date,
                            url=link_href,
                            company_name=company_name,
                            ticker="",  # Not available in search results
                            cik=cik
                        ))
                        
                except Exception as e:
                    logger.warning("Failed to parse filing entry", error=str(e))
                    continue
            
            return filings
            
        except Exception as e:
            logger.error("Failed to parse EDGAR search results", error=str(e))
            return []
    
    def _parse_filing_content(self, accession: str, raw_html: str) -> FilingContent:
        """Parse SEC filing content to extract sections and tables"""
        try:
            # Parse HTML
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Extract sections
            sections = {}
            
            # Common section patterns - handle various heading formats
            section_patterns = {
                'mda': r'(?i)(item\s*7\.?\s*management\'s\s*discussion\s*and\s*analysis|management\'s\s*discussion\s*and\s*analysis|md&a|mda)',
                'risk': r'(?i)(item\s*1a\.?\s*risk\s*factors|risk\s*factors|risks\s*and\s*uncertainties)',
                'business': r'(?i)(item\s*1\.?\s*business|description\s*of\s*business|business)',
                'properties': r'(?i)(item\s*2\.?\s*properties|properties)',
                'legal': r'(?i)(item\s*3\.?\s*legal\s*proceedings|legal\s*proceedings)',
                'market': r'(?i)(item\s*5\.?\s*market\s*for\s*registrant\'s\s*common\s*equity|market\s*for\s*registrant\'s\s*common\s*equity)',
                'financial': r'(?i)(item\s*8\.?\s*financial\s*statements|financial\s*statements|consolidated\s*statements)'
            }
            
            # Find sections by text patterns
            text_content = soup.get_text()
            for section_name, pattern in section_patterns.items():
                match = re.search(pattern, text_content)
                if match:
                    # Extract content around the match
                    start_pos = match.start()
                    end_pos = min(start_pos + 5000, len(text_content))  # Limit section size
                    sections[section_name] = text_content[start_pos:end_pos].strip()
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                try:
                    table_data = self._parse_table(table)
                    if table_data:
                        tables.append(table_data)
                except Exception as e:
                    logger.warning("Failed to parse table", error=str(e))
                    continue
            
            # Extract metadata
            metadata = {
                'accession': accession,
                'parsed_at': datetime.now().isoformat(),
                'total_sections': len(sections),
                'total_tables': len(tables),
                'content_length': len(raw_html)
            }

            # Mark amended filings (10-K/A, 10-Q/A)
            try:
                is_amend = bool(re.search(r'\/(10-[KQ]\/A|10-[KQ]A)\b', raw_html, flags=re.IGNORECASE))
            except Exception:
                is_amend = ('/A' in accession)
            metadata['amends'] = is_amend
            
            return FilingContent(
                accession=accession,
                raw_html=raw_html,
                sections=sections,
                tables=tables,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to parse filing content", error=str(e), accession=accession)
            return FilingContent(
                accession=accession,
                raw_html=raw_html,
                sections={},
                tables=[],
                metadata={'error': str(e)}
            )
    
    def _parse_table(self, table) -> Dict[str, Any]:
        """Parse HTML table into structured data"""
        try:
            rows = []
            headers = []
            
            # Extract headers
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())
            
            # Extract data rows
            for tr in table.find_all('tr')[1:]:  # Skip header row
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text().strip())
                if row:
                    rows.append(row)
            
            return {
                'headers': headers,
                'rows': rows,
                'row_count': len(rows),
                'col_count': len(headers)
            }
            
        except Exception as e:
            logger.warning("Failed to parse table", error=str(e))
            return {}

# Convenience functions for async usage
async def search_edgar_filings(
    ticker: Optional[str] = None,
    cik: Optional[str] = None,
    form: str = "10-K",
    year_range: Tuple[int, int] = (2020, 2024),
    limit: int = 10
) -> List[FilingInfo]:
    """Search EDGAR filings"""
    async with EdgarRetriever() as retriever:
        return await retriever.search_filings(ticker, cik, form, year_range, limit)

async def fetch_edgar_filing(accession: str) -> FilingContent:
    """Fetch specific EDGAR filing"""
    async with EdgarRetriever() as retriever:
        return await retriever.fetch_filing(accession)
