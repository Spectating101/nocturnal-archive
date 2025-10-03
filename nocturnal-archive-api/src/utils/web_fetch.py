"""
Web fetching utility for browsing financial data
Wrapper around Claude Code's WebFetch capability
"""

import httpx
import structlog
import re

logger = structlog.get_logger(__name__)


async def web_fetch(url: str, prompt: str, timeout: int = 30) -> str:
    """
    Fetch a URL and process it with AI (like ChatGPT/Claude browsing)

    Args:
        url: The URL to fetch
        prompt: Instructions for what to extract from the page
        timeout: Request timeout in seconds

    Returns:
        AI-processed response based on the prompt
    """
    try:
        logger.info("Fetching URL", url=url, prompt_preview=prompt[:100])

        # Fetch the page
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

            content = response.text

            # For now, use simple extraction based on the prompt
            # In production, this would call an LLM to process the content
            # But for immediate functionality, we'll do direct HTML parsing

            result = await _parse_financial_page(content, prompt, url)

            logger.info("Web fetch successful", url=url, result_length=len(result))
            return result

    except Exception as e:
        logger.error("Web fetch failed", url=url, error=str(e))
        raise


async def _parse_financial_page(html: str, prompt: str, url: str) -> str:
    """
    Parse financial data from HTML
    Simple implementation for immediate functionality
    """
    import json
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Yahoo Finance specific parsing
        if "finance.yahoo.com" in url:
            result = _parse_yahoo_finance(soup, prompt)
            if result:
                return json.dumps(result)

        # SEC EDGAR specific parsing
        if "sec.gov" in url:
            result = _parse_sec_edgar(soup, prompt)
            if result:
                return json.dumps(result)

        # Fallback: return raw text for LLM processing
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000]  # Limit to first 5000 chars

    except Exception as e:
        logger.warning("HTML parsing failed", error=str(e))
        return ""


def _parse_yahoo_finance(soup, prompt: str) -> dict:
    """
    Parse Yahoo Finance financials page
    """
    try:
        # Look for financial data tables
        # Yahoo uses specific table structures for quarterly/annual data

        # Extract concept from prompt
        concept = None
        if "revenue" in prompt.lower():
            concept = "revenue"
        elif "cost of revenue" in prompt.lower():
            concept = "costOfRevenue"
        elif "gross profit" in prompt.lower():
            concept = "grossProfit"

        # Find all table rows
        rows = soup.find_all('div', {'class': re.compile(r'row|fin-row')})

        for row in rows:
            text = row.get_text()

            # Match revenue patterns
            if concept == "revenue" and ("Total Revenue" in text or "Revenue" in text):
                # Extract value (usually first number column)
                numbers = re.findall(r'[\d,]+\.?\d*[BMK]?', text)
                if numbers:
                    value = _convert_to_number(numbers[0])
                    return {
                        "concept": concept,
                        "value": value,
                        "period": "latest",
                        "unit": "USD",
                        "source": "yahoo_finance"
                    }

        return {}

    except Exception as e:
        logger.warning("Yahoo Finance parsing failed", error=str(e))
        return {}


def _parse_sec_edgar(soup, prompt: str) -> dict:
    """
    Parse SEC EDGAR filing page
    """
    try:
        # SEC EDGAR has structured tables in filings
        # Look for relevant financial data

        text = soup.get_text()

        # Simple pattern matching for common financial items
        # This is a simplified version - production would be more robust

        patterns = {
            "revenue": r"Revenue.*?(\d{1,3}(?:,\d{3})*)",
            "cost": r"Cost.*?Revenue.*?(\d{1,3}(?:,\d{3})*)",
        }

        for key, pattern in patterns.items():
            if key in prompt.lower():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = int(match.group(1).replace(',', ''))
                    return {
                        "concept": key,
                        "value": value * 1000,  # Usually in thousands
                        "period": "latest",
                        "unit": "USD",
                        "source": "sec_edgar"
                    }

        return {}

    except Exception as e:
        logger.warning("SEC EDGAR parsing failed", error=str(e))
        return {}


def _convert_to_number(value_str: str) -> float:
    """Convert financial notation to number (e.g., '1.23B' -> 1230000000)"""
    value_str = value_str.strip().replace(',', '')

    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000,
        'T': 1_000_000_000_000,
    }

    for suffix, multiplier in multipliers.items():
        if value_str.endswith(suffix):
            number = float(value_str[:-1])
            return number * multiplier

    return float(value_str)
