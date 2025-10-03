"""
Browser-Based Financial Data Adapter
Uses web scraping to get accurate financial data like ChatGPT/Claude do
"""

import structlog
from typing import Dict, Any, Optional
import json
import re

logger = structlog.get_logger(__name__)


class BrowserFinanceAdapter:
    """
    Fetch financial data by browsing websites (like ChatGPT does!)
    More reliable than broken APIs
    """

    def __init__(self):
        self.sources = {
            "yahoo": "https://finance.yahoo.com/quote/{ticker}/financials",
            "sec_viewer": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-Q&dateb=&owner=exclude&count=10",
        }

    async def get_fact(self, ticker: str, concept: str, period: str = "latest", freq: str = "Q") -> Optional[Dict[str, Any]]:
        """
        Get a financial fact by browsing the web

        Strategy:
        1. Try Yahoo Finance page (most reliable, has recent data)
        2. Try SEC EDGAR viewer (official source)
        3. Parse HTML to extract the exact value
        """
        logger.info("Fetching via browser", ticker=ticker, concept=concept, period=period, freq=freq)

        # Try Yahoo Finance first
        result = await self._fetch_from_yahoo(ticker, concept, freq)
        if result:
            return result

        # Fallback to SEC viewer
        result = await self._fetch_from_sec_viewer(ticker, concept, freq)
        if result:
            return result

        logger.warning("Browser fetch failed for all sources", ticker=ticker, concept=concept)
        return None

    async def _fetch_from_yahoo(self, ticker: str, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """Fetch from Yahoo Finance page (works without API key!)"""
        try:
            from src.utils.web_fetch import web_fetch

            url = f"https://finance.yahoo.com/quote/{ticker}/financials"

            # Map concepts to Yahoo Finance terminology
            concept_mapping = {
                "revenue": ["Total Revenue", "Revenue"],
                "costOfRevenue": ["Cost of Revenue", "Cost Of Revenue"],
                "grossProfit": ["Gross Profit"],
                "operatingIncome": ["Operating Income"],
                "netIncome": ["Net Income"],
                "totalAssets": ["Total Assets"],
                "totalLiabilities": ["Total Liabilities"],
            }

            search_terms = concept_mapping.get(concept, [concept])

            # Fetch the page
            prompt = f"""
            Extract the latest {freq}uarterly financial data for {ticker}.

            Find these items: {', '.join(search_terms)}

            Return ONLY a JSON object with this exact structure:
            {{
                "concept": "{concept}",
                "value": <numeric value in dollars, no commas>,
                "period": "<period like Q3 2024>",
                "unit": "USD",
                "source": "yahoo_finance"
            }}

            IMPORTANT:
            - Return the MOST RECENT period (latest quarter)
            - Convert all values to raw numbers (e.g., "1.23B" → 1230000000)
            - If multiple columns, use the FIRST column (most recent)
            """

            result = await web_fetch(url, prompt)

            # Parse the JSON response
            try:
                # Extract JSON from response (might have explanation around it)
                json_match = re.search(r'\{[^}]+\}', result)
                if json_match:
                    data = json.loads(json_match.group(0))

                    if data.get("value"):
                        logger.info("Yahoo Finance browser fetch successful",
                                   ticker=ticker, concept=concept, value=data["value"])
                        return {
                            "concept": concept,
                            "value": float(data["value"]),
                            "unit": data.get("unit", "USD"),
                            "period": data.get("period", "latest"),
                            "data_source": "yahoo_finance_browser",
                            "citation": {
                                "url": url,
                                "source": "Yahoo Finance (Web)"
                            }
                        }
            except Exception as e:
                logger.warning("Failed to parse Yahoo response", error=str(e), response=result[:200])

            return None

        except Exception as e:
            logger.warning("Yahoo Finance browser fetch failed", ticker=ticker, error=str(e))
            return None

    async def _fetch_from_sec_viewer(self, ticker: str, concept: str, freq: str) -> Optional[Dict[str, Any]]:
        """Fetch from SEC EDGAR viewer page"""
        try:
            from src.utils.web_fetch import web_fetch
            from src.identifiers.resolve import resolve_ticker

            # Get CIK first
            mapping = await resolve_ticker(ticker)
            if not mapping or not mapping.cik:
                return None

            cik = mapping.cik
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-Q&dateb=&owner=exclude&count=1"

            prompt = f"""
            This is an SEC EDGAR filing list page for {ticker}.

            1. Find the MOST RECENT 10-Q filing
            2. Click through to that filing
            3. Find the "{concept}" value in the financial statements
            4. Return ONLY a JSON object:

            {{
                "concept": "{concept}",
                "value": <numeric value>,
                "period": "<fiscal period>",
                "accession": "<accession number>",
                "unit": "USD",
                "source": "sec_edgar"
            }}

            Extract the RAW NUMBER, no formatting.
            """

            result = await web_fetch(url, prompt)

            # Parse response
            try:
                json_match = re.search(r'\{[^}]+\}', result)
                if json_match:
                    data = json.loads(json_match.group(0))

                    if data.get("value"):
                        logger.info("SEC browser fetch successful",
                                   ticker=ticker, concept=concept, value=data["value"])
                        return {
                            "concept": concept,
                            "value": float(data["value"]),
                            "unit": data.get("unit", "USD"),
                            "period": data.get("period", "latest"),
                            "accession": data.get("accession", ""),
                            "data_source": "sec_edgar_browser",
                            "citation": {
                                "url": url,
                                "accession": data.get("accession", ""),
                                "source": "SEC EDGAR (Web)"
                            }
                        }
            except Exception as e:
                logger.warning("Failed to parse SEC response", error=str(e), response=result[:200])

            return None

        except Exception as e:
            logger.warning("SEC browser fetch failed", ticker=ticker, error=str(e))
            return None

    async def get_facts_from_same_period(self, ticker: str, concepts: list, period: str = "latest", freq: str = "Q") -> Dict[str, Dict[str, Any]]:
        """
        Get multiple facts from the SAME period/filing
        This ensures period consistency (no mixing 2018 revenue with 2025 COGS!)
        """
        try:
            from src.utils.web_fetch import web_fetch

            url = f"https://finance.yahoo.com/quote/{ticker}/financials"

            # Map all concepts to Yahoo terminology
            concept_mapping = {
                "revenue": "Total Revenue",
                "costOfRevenue": "Cost of Revenue",
                "grossProfit": "Gross Profit",
                "operatingIncome": "Operating Income",
                "netIncome": "Net Income",
            }

            items_to_find = [concept_mapping.get(c, c) for c in concepts]

            prompt = f"""
            Extract the latest {freq}uarterly financial data for {ticker}.

            Find ALL of these items from the SAME period (same column):
            {chr(10).join(f"- {item}" for item in items_to_find)}

            Return ONLY a JSON object mapping concept names to values:
            {{
                "revenue": <value>,
                "costOfRevenue": <value>,
                "period": "<period like Q3 2024>",
                "all_from_same_period": true
            }}

            CRITICAL: All values must be from the FIRST column (most recent period).
            Convert values to raw numbers (e.g., "1.23B" → 1230000000).
            """

            result = await web_fetch(url, prompt)

            # Parse response
            try:
                json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))

                    # Build facts dictionary
                    facts = {}
                    period = data.get("period", "latest")

                    for concept in concepts:
                        if concept in data and data[concept]:
                            facts[concept] = {
                                "concept": concept,
                                "value": float(data[concept]),
                                "unit": "USD",
                                "period": period,
                                "data_source": "yahoo_finance_browser",
                                "citation": {
                                    "url": url,
                                    "source": "Yahoo Finance (Web)"
                                }
                            }

                    if facts:
                        logger.info("Fetched facts from same period via browser",
                                   ticker=ticker, concepts=list(facts.keys()), period=period)
                        return facts

            except Exception as e:
                logger.warning("Failed to parse multi-fact response", error=str(e), response=result[:200])

            return {}

        except Exception as e:
            logger.error("Browser multi-fact fetch failed", ticker=ticker, error=str(e))
            return {}


# Singleton instance
_browser_adapter = None

def get_browser_finance_adapter() -> BrowserFinanceAdapter:
    """Get the singleton browser finance adapter"""
    global _browser_adapter
    if _browser_adapter is None:
        _browser_adapter = BrowserFinanceAdapter()
    return _browser_adapter
