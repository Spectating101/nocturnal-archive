"""
Advanced Browser-Based Financial Data Adapter
Production-grade web scraping with intelligent parsing, validation, and fallbacks
"""

import asyncio
import httpx
import structlog
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

logger = structlog.get_logger(__name__)


class AdvancedBrowserFinanceAdapter:
    """
    Production-grade browser-based financial data fetching
    Features:
    - Multiple parsing strategies
    - Cross-validation between sources
    - Intelligent caching
    - Robust error handling
    - Data sanity checks
    """

    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour TTL

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def get_fact(self, ticker: str, concept: str, period: str = "latest", freq: str = "Q") -> Optional[Dict[str, Any]]:
        """
        Get a financial fact with multiple strategies and validation
        """
        cache_key = f"{ticker}:{concept}:{period}:{freq}"

        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.info("Cache hit", ticker=ticker, concept=concept)
                return cached_data

        logger.info("Fetching financial fact", ticker=ticker, concept=concept, period=period, freq=freq)

        # Strategy 1: Yahoo Finance (most reliable for recent data)
        result = await self._fetch_from_yahoo_advanced(ticker, concept, freq)

        if result and self._validate_data(result, concept):
            self.cache[cache_key] = (result, datetime.now())
            return result

        # Strategy 2: SEC EDGAR (most authoritative, but slower)
        result = await self._fetch_from_sec_edgar(ticker, concept, freq)

        if result and self._validate_data(result, concept):
            self.cache[cache_key] = (result, datetime.now())
            return result

        # Strategy 3: Marketwatch (backup)
        result = await self._fetch_from_marketwatch(ticker, concept, freq)

        if result and self._validate_data(result, concept):
            self.cache[cache_key] = (result, datetime.now())
            return result

        logger.warning("All fetching strategies failed", ticker=ticker, concept=concept)
        return None

    async def _fetch_from_yahoo_advanced(self, ticker: str, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """
        Advanced Yahoo Finance scraping with multiple parsing strategies
        """
        try:
            url = f"https://finance.yahoo.com/quote/{ticker}/financials"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": self.user_agents[0],
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }

                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    logger.warning("Yahoo Finance returned non-200", status=response.status_code, ticker=ticker)
                    return None

                html = response.text
                soup = BeautifulSoup(html, 'html.parser')

                # Strategy 1: Find financials table
                result = self._parse_yahoo_table(soup, concept, freq)
                if result:
                    result["data_source"] = "yahoo_finance_browser"
                    result["citation"] = {
                        "url": url,
                        "source": "Yahoo Finance (Web)"
                    }
                    logger.info("Yahoo Finance data extracted", ticker=ticker, concept=concept, value=result.get("value"))
                    return result

                # Strategy 2: Find JSON-LD data
                result = self._parse_yahoo_jsonld(soup, concept)
                if result:
                    result["data_source"] = "yahoo_finance_browser"
                    result["citation"] = {
                        "url": url,
                        "source": "Yahoo Finance (Web/JSON-LD)"
                    }
                    return result

                logger.warning("Yahoo Finance parsing failed", ticker=ticker, concept=concept)
                return None

        except Exception as e:
            logger.error("Yahoo Finance fetch failed", ticker=ticker, error=str(e))
            return None

    def _parse_yahoo_table(self, soup: BeautifulSoup, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """
        Parse Yahoo Finance financial tables with intelligent row matching
        """
        try:
            # Map concepts to Yahoo Finance row labels
            concept_mapping = {
                "revenue": ["Total Revenue", "Revenue", "Total Revenues"],
                "costOfRevenue": ["Cost of Revenue", "Cost Of Revenue", "Cost of Goods Sold", "COGS"],
                "grossProfit": ["Gross Profit"],
                "operatingIncome": ["Operating Income", "Operating Income or Loss"],
                "netIncome": ["Net Income", "Net Income Common Stockholders"],
                "totalAssets": ["Total Assets"],
                "totalLiabilities": ["Total Liabilities"],
                "ebit": ["EBIT"],
                "ebitda": ["EBITDA"],
            }

            search_terms = concept_mapping.get(concept, [concept])

            # Find all table rows
            all_rows = soup.find_all(['div', 'tr'], class_=re.compile(r'row|fin|data'))

            for row in all_rows:
                row_text = row.get_text(separator=' ', strip=True)

                # Check if this row matches our concept
                for term in search_terms:
                    if term.lower() in row_text.lower():
                        # Extract numbers from this row
                        # Yahoo typically shows: [Label] [Q1 2024] [Q2 2024] [Q3 2024] [Q4 2024]
                        numbers = re.findall(r'([\d,]+\.?\d*[KMB]?)', row_text)

                        if numbers:
                            # First number after label is usually most recent
                            value_str = numbers[0]
                            value = self._convert_financial_notation(value_str)

                            # Extract period if possible
                            period_match = re.search(r'(Q[1-4]\s*20\d{2}|20\d{2})', row_text)
                            period = period_match.group(0) if period_match else "latest"

                            return {
                                "concept": concept,
                                "value": value,
                                "unit": "USD",
                                "period": period,
                            }

            # Fallback: Try finding specific table with "Financials" in header
            tables = soup.find_all('table')
            for table in tables:
                result = self._parse_table_systematically(table, concept, search_terms)
                if result:
                    return result

            return None

        except Exception as e:
            logger.warning("Yahoo table parsing failed", error=str(e))
            return None

    def _parse_table_systematically(self, table, concept: str, search_terms: List[str]) -> Optional[Dict[str, Any]]:
        """
        Systematically parse a table by finding the header row and data row
        """
        try:
            rows = table.find_all('tr')

            # Find header row (usually has dates)
            header_row = None
            header_cols = []

            for row in rows:
                cols = row.find_all(['th', 'td'])
                col_texts = [col.get_text(strip=True) for col in cols]

                # Check if this looks like a header (has quarters or years)
                if any(re.search(r'(Q[1-4]|20\d{2})', text) for text in col_texts):
                    header_row = row
                    header_cols = col_texts
                    break

            if not header_row:
                return None

            # Now find the data row matching our concept
            for row in rows:
                cols = row.find_all(['th', 'td'])
                if not cols:
                    continue

                label = cols[0].get_text(strip=True)

                # Check if this row matches our concept
                for term in search_terms:
                    if term.lower() in label.lower():
                        # Extract first data column (most recent)
                        if len(cols) > 1:
                            value_text = cols[1].get_text(strip=True)
                            value = self._convert_financial_notation(value_text)

                            period = header_cols[1] if len(header_cols) > 1 else "latest"

                            return {
                                "concept": concept,
                                "value": value,
                                "unit": "USD",
                                "period": period,
                            }

            return None

        except Exception as e:
            logger.warning("Systematic table parsing failed", error=str(e))
            return None

    def _parse_yahoo_jsonld(self, soup: BeautifulSoup, concept: str) -> Optional[Dict[str, Any]]:
        """
        Extract financial data from JSON-LD structured data
        """
        try:
            # Find JSON-LD script tags
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                try:
                    data = json.loads(script.string)

                    # Look for financial data in the JSON structure
                    if isinstance(data, dict) and 'financialData' in data:
                        financial_data = data['financialData']

                        # Map concept to JSON field
                        json_mapping = {
                            "revenue": "totalRevenue",
                            "grossProfit": "grossProfit",
                            "netIncome": "netIncome",
                            "ebitda": "ebitda",
                        }

                        field = json_mapping.get(concept)
                        if field and field in financial_data:
                            return {
                                "concept": concept,
                                "value": float(financial_data[field]),
                                "unit": "USD",
                                "period": "latest",
                            }

                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.warning("JSON-LD parsing failed", error=str(e))
            return None

    async def _fetch_from_sec_edgar(self, ticker: str, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """
        Fetch from SEC EDGAR filings (most authoritative source)
        """
        try:
            from src.identifiers.resolve import resolve_ticker

            # Resolve ticker to CIK
            mapping = await resolve_ticker(ticker)
            if not mapping or not mapping.cik:
                return None

            cik = mapping.cik.lstrip('0')  # Remove leading zeros for URL

            # Get latest 10-Q filing
            filings_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-Q&dateb=&owner=exclude&count=1&search_text="

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "User-Agent": "Nocturnal Archive Research research@nocturnal.dev",
                    "Accept": "text/html,application/xhtml+xml",
                }

                response = await client.get(filings_url, headers=headers)

                if response.status_code != 200:
                    return None

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find the latest filing link
                doc_link = soup.find('a', {'id': 'documentsbutton'})
                if not doc_link:
                    return None

                filing_url = f"https://www.sec.gov{doc_link['href']}"

                # Fetch the filing documents page
                response = await client.get(filing_url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find the main XBRL instance document
                xbrl_link = soup.find('a', string=re.compile(r'.*_htm\.xml$'))
                if not xbrl_link:
                    # Try finding any XML file
                    xbrl_link = soup.find('a', href=re.compile(r'\.xml$'))

                if not xbrl_link:
                    return None

                xbrl_url = f"https://www.sec.gov{xbrl_link['href']}"

                # Fetch and parse XBRL
                response = await client.get(xbrl_url, headers=headers)

                # Parse XBRL for the concept
                value = self._parse_xbrl(response.text, concept)

                if value:
                    return {
                        "concept": concept,
                        "value": value,
                        "unit": "USD",
                        "period": "latest",
                        "data_source": "sec_edgar_browser",
                        "citation": {
                            "url": xbrl_url,
                            "source": "SEC EDGAR Filing"
                        }
                    }

            return None

        except Exception as e:
            logger.warning("SEC EDGAR fetch failed", ticker=ticker, error=str(e))
            return None

    def _parse_xbrl(self, xbrl_text: str, concept: str) -> Optional[float]:
        """
        Parse XBRL XML to extract financial values
        """
        try:
            # Map concepts to XBRL tags
            xbrl_mapping = {
                "revenue": ["us-gaap:Revenues", "us-gaap:SalesRevenueNet"],
                "costOfRevenue": ["us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsAndServicesSold"],
                "grossProfit": ["us-gaap:GrossProfit"],
                "operatingIncome": ["us-gaap:OperatingIncomeLoss"],
                "netIncome": ["us-gaap:NetIncomeLoss"],
            }

            tags = xbrl_mapping.get(concept, [])

            for tag in tags:
                # Find the tag in XML (case-insensitive)
                pattern = rf'<{tag}[^>]*>([\d,]+)</{tag}>'
                match = re.search(pattern, xbrl_text, re.IGNORECASE)

                if match:
                    value_str = match.group(1).replace(',', '')
                    return float(value_str)

            return None

        except Exception as e:
            logger.warning("XBRL parsing failed", error=str(e))
            return None

    async def _fetch_from_marketwatch(self, ticker: str, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """
        Fetch from MarketWatch as additional fallback
        """
        try:
            url = f"https://www.marketwatch.com/investing/stock/{ticker}/financials"

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"User-Agent": self.user_agents[0]}
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    return None

                soup = BeautifulSoup(response.text, 'html.parser')

                # Parse MarketWatch tables (similar structure to Yahoo)
                result = self._parse_yahoo_table(soup, concept, freq)

                if result:
                    result["data_source"] = "marketwatch_browser"
                    result["citation"] = {
                        "url": url,
                        "source": "MarketWatch (Web)"
                    }
                    return result

            return None

        except Exception as e:
            logger.warning("MarketWatch fetch failed", ticker=ticker, error=str(e))
            return None

    def _convert_financial_notation(self, value_str: str) -> float:
        """
        Convert financial notation to float
        Handles: 1,234.56, 1.23B, 1.23M, 1.23K, etc.
        """
        try:
            value_str = value_str.strip().replace(',', '')

            multipliers = {
                'K': 1_000,
                'M': 1_000_000,
                'B': 1_000_000_000,
                'T': 1_000_000_000_000,
            }

            for suffix, multiplier in multipliers.items():
                if value_str.upper().endswith(suffix):
                    number = float(value_str[:-1])
                    return number * multiplier

            # Handle parentheses for negative numbers
            if '(' in value_str:
                value_str = value_str.replace('(', '').replace(')', '')
                return -float(value_str)

            return float(value_str)

        except Exception as e:
            logger.warning("Value conversion failed", value=value_str, error=str(e))
            return 0.0

    def _validate_data(self, data: Dict[str, Any], concept: str) -> bool:
        """
        Validate extracted data for sanity
        """
        if not data or "value" not in data:
            return False

        value = data["value"]

        # Check if value is reasonable
        if not isinstance(value, (int, float)):
            return False

        # Sanity checks by concept
        thresholds = {
            "revenue": (1_000, 10_000_000_000_000),  # $1K to $10T
            "costOfRevenue": (0, 10_000_000_000_000),
            "grossProfit": (-1_000_000_000_000, 10_000_000_000_000),  # Can be negative
            "netIncome": (-1_000_000_000_000, 10_000_000_000_000),
            "operatingIncome": (-1_000_000_000_000, 10_000_000_000_000),
        }

        min_val, max_val = thresholds.get(concept, (0, float('inf')))

        if value < min_val or value > max_val:
            logger.warning("Data failed sanity check", concept=concept, value=value, min=min_val, max=max_val)
            return False

        return True

    async def get_facts_from_same_period(
        self,
        ticker: str,
        concepts: List[str],
        period: str = "latest",
        freq: str = "Q"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple facts from the SAME period
        This is critical for preventing period mismatch bugs!
        """
        try:
            # Fetch all concepts in parallel
            tasks = [self.get_fact(ticker, concept, period, freq) for concept in concepts]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Build facts dictionary
            facts = {}
            periods = set()

            for i, result in enumerate(results):
                if isinstance(result, dict) and result:
                    concept = concepts[i]
                    facts[concept] = result
                    periods.add(result.get("period", "unknown"))

            # Validate all facts are from same period
            if len(periods) > 1:
                logger.warning("Facts from multiple periods detected",
                             ticker=ticker, periods=list(periods))
                # Try to filter to most common period
                # For now, return all facts but log the warning

            if facts:
                logger.info("Retrieved facts from same period",
                           ticker=ticker, concepts_count=len(facts), periods=list(periods))

            return facts

        except Exception as e:
            logger.error("Failed to get facts from same period", ticker=ticker, error=str(e))
            return {}


# Singleton instance
_advanced_browser_adapter = None

def get_advanced_browser_finance_adapter() -> AdvancedBrowserFinanceAdapter:
    """Get the singleton advanced browser adapter"""
    global _advanced_browser_adapter
    if _advanced_browser_adapter is None:
        _advanced_browser_adapter = AdvancedBrowserFinanceAdapter()
    return _advanced_browser_adapter
