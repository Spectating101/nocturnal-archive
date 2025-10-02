"""
SEC Filings Adapter - THE Definitive Financial Data Source
Parses actual SEC filings for current, accurate financial data
"""

import asyncio
import aiohttp
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

logger = structlog.get_logger(__name__)

class SECFilingsAdapter:
    """SEC Filings adapter for current, accurate financial data"""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.session = None
        self.headers = {
            "User-Agent": "FinSight Financial Data (contact@nocturnal.dev)",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }
        
    async def _get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def get_company_cik(self, ticker: str) -> Optional[str]:
        """Get CIK for a ticker symbol"""
        try:
            session = await self._get_session()
            
            # Try direct ticker lookup first
            url = f"{self.base_url}/api/xbrl/companyconcept/CIK{ticker.zfill(10)}.json"
            async with session.get(url) as response:
                if response.status == 200:
                    return ticker.zfill(10)
            
            # If not found, search for ticker
            # This is a simplified approach - in production, we'd use a proper ticker-to-CIK mapping
            return None
            
        except Exception as e:
            logger.error("Failed to get CIK", ticker=ticker, error=str(e))
            return None
    
    async def get_recent_filings(self, ticker: str, form_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get recent filings for a company"""
        if form_types is None:
            form_types = ["10-Q", "10-K", "8-K"]
            
        try:
            cik = await self.get_company_cik(ticker)
            if not cik:
                logger.warning("No CIK found", ticker=ticker)
                return []
            
            session = await self._get_session()
            url = f"{self.base_url}/submissions/CIK{cik}.json"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to get submissions", ticker=ticker, status=response.status)
                    return []
                
                data = await response.json()
                filings = data.get("filings", {}).get("recent", {})
                
                # Extract filing information
                recent_filings = []
                for i, form in enumerate(filings.get("form", [])):
                    if form in form_types:
                        filing = {
                            "form": form,
                            "filingDate": filings.get("filingDate", [])[i],
                            "reportDate": filings.get("reportDate", [])[i],
                            "accessionNumber": filings.get("accessionNumber", [])[i],
                            "primaryDocument": filings.get("primaryDocument", [])[i]
                        }
                        recent_filings.append(filing)
                
                logger.info("Retrieved recent filings", ticker=ticker, count=len(recent_filings))
                return recent_filings
                
        except Exception as e:
            logger.error("Failed to get recent filings", ticker=ticker, error=str(e))
            return []
    
    async def get_financial_data_from_filing(self, ticker: str, form_type: str = "10-Q", 
                                           report_date: str = None) -> Optional[Dict[str, Any]]:
        """Get financial data from a specific filing"""
        try:
            filings = await self.get_recent_filings(ticker, [form_type])
            if not filings:
                logger.warning("No filings found", ticker=ticker, form_type=form_type)
                return None
            
            # Find the most recent filing or specific report date
            target_filing = None
            if report_date:
                for filing in filings:
                    if filing["reportDate"] == report_date:
                        target_filing = filing
                        break
            else:
                target_filing = filings[0]  # Most recent
            
            if not target_filing:
                logger.warning("No matching filing found", ticker=ticker, report_date=report_date)
                return None
            
            # Get the XBRL data from the filing
            return await self._parse_filing_xbrl(target_filing)
            
        except Exception as e:
            logger.error("Failed to get financial data from filing", ticker=ticker, error=str(e))
            return None
    
    async def _parse_filing_xbrl(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse XBRL data from a filing"""
        try:
            accession = filing["accessionNumber"]
            primary_doc = filing["primaryDocument"]
            
            # Construct URL for the XBRL filing
            # Format: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no}/{primary_doc}
            cik = accession.split("-")[0]
            accession_no = accession.replace("-", "")
            
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no}/{primary_doc}"
            
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to get filing document", url=url, status=response.status)
                    return None
                
                content = await response.text()
                
                # Parse XBRL data (simplified - in production, we'd use proper XBRL parsing)
                financial_data = self._extract_financial_data_from_xbrl(content)
                
                if financial_data:
                    financial_data.update({
                        "filing": filing,
                        "source": "sec_edgar",
                        "url": url,
                        "parsed_at": datetime.now().isoformat()
                    })
                
                return financial_data
                
        except Exception as e:
            logger.error("Failed to parse filing XBRL", filing=filing, error=str(e))
            return None
    
    def _extract_financial_data_from_xbrl(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract financial data from XBRL content"""
        try:
            # This is a simplified extraction - in production, we'd use proper XBRL parsing
            # For now, we'll extract key financial metrics using regex patterns
            
            financial_data = {}
            
            # Extract revenue (multiple possible tags)
            revenue_patterns = [
                r'<us-gaap:Revenues[^>]*>([^<]+)</us-gaap:Revenues>',
                r'<us-gaap:SalesRevenueNet[^>]*>([^<]+)</us-gaap:SalesRevenueNet>',
                r'<us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax[^>]*>([^<]+)</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>'
            ]
            
            for pattern in revenue_patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        revenue = float(match.group(1).replace(',', ''))
                        financial_data["revenue"] = revenue
                        break
                    except ValueError:
                        continue
            
            # Extract other key metrics
            metrics = {
                "net_income": r'<us-gaap:NetIncomeLoss[^>]*>([^<]+)</us-gaap:NetIncomeLoss>',
                "total_assets": r'<us-gaap:Assets[^>]*>([^<]+)</us-gaap:Assets>',
                "total_liabilities": r'<us-gaap:Liabilities[^>]*>([^<]+)</us-gaap:Liabilities>',
                "cash": r'<us-gaap:CashAndCashEquivalentsAtCarryingValue[^>]*>([^<]+)</us-gaap:CashAndCashEquivalentsAtCarryingValue>'
            }
            
            for metric, pattern in metrics.items():
                match = re.search(pattern, content)
                if match:
                    try:
                        value = float(match.group(1).replace(',', ''))
                        financial_data[metric] = value
                    except ValueError:
                        continue
            
            return financial_data if financial_data else None
            
        except Exception as e:
            logger.error("Failed to extract financial data from XBRL", error=str(e))
            return None
    
    async def get_fact(self, ticker: str, concept: str, period: str = None, freq: str = "Q") -> Optional[Dict[str, Any]]:
        """Get specific financial fact from SEC filings"""
        try:
            # Determine form type based on frequency
            form_type = "10-Q" if freq == "Q" else "10-K"
            
            # Get financial data from most recent filing
            financial_data = await self.get_financial_data_from_filing(ticker, form_type, period)
            
            if not financial_data:
                return None
            
            # Map concept to financial data
            concept_map = {
                "revenue": "revenue",
                "net_income": "net_income",
                "total_assets": "total_assets",
                "total_liabilities": "total_liabilities",
                "cash": "cash"
            }
            
            mapped_concept = concept_map.get(concept)
            if not mapped_concept or mapped_concept not in financial_data:
                logger.warning("Concept not found in financial data", concept=concept, available=list(financial_data.keys()))
                return None
            
            value = financial_data[mapped_concept]
            
            return {
                "value": value,
                "unit": "USD",
                "period": financial_data["filing"]["reportDate"],
                "concept": concept,
                "source": "sec_edgar",
                "url": financial_data["url"],
                "filing": financial_data["filing"],
                "parsed_at": financial_data["parsed_at"]
            }
            
        except Exception as e:
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            return None
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()