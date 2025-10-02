"""
Yahoo Finance Direct API Adapter - THE Definitive Market Data Source
Direct API calls to Yahoo Finance for real-time and historical data
"""

import asyncio
import aiohttp
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import re

logger = structlog.get_logger(__name__)

class YahooFinanceDirectAdapter:
    """Direct Yahoo Finance API adapter for accurate market data"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com"
        self.session = None
        
    async def _get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "FinSight Financial Data (contact@nocturnal.dev)"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    def _normalize_ticker(self, ticker: str) -> str:
        """Normalize ticker for Yahoo Finance"""
        ticker = ticker.upper().strip()
        
        # Handle common suffixes and exchanges
        if "." in ticker:
            return ticker  # Already has exchange suffix
        
        # Add common exchange suffixes
        exchange_suffixes = {
            "LON": ".L", "LSE": ".L",  # London
            "TOR": ".TO", "TSX": ".TO",  # Toronto
            "FRA": ".F", "XETRA": ".F",  # Frankfurt
            "PAR": ".PA", "EPA": ".PA",  # Paris
            "AMS": ".AS", "AEX": ".AS",  # Amsterdam
            "MIL": ".MI", "BIT": ".MI",  # Milan
            "MAD": ".MC", "BME": ".MC",  # Madrid
            "ZUR": ".SW", "SIX": ".SW",  # Zurich
            "STO": ".ST", "OMX": ".ST",  # Stockholm
            "OSL": ".OL", "OSE": ".OL",  # Oslo
            "COP": ".CO", "CSE": ".CO",  # Copenhagen
            "HEL": ".HE", "OMXH": ".HE",  # Helsinki
            "VIE": ".VI", "WBAG": ".VI",  # Vienna
            "ATH": ".AT", "ATHEX": ".AT",  # Athens
            "LIS": ".LS", "PSI": ".LS",  # Lisbon
            "DUB": ".IR", "ISE": ".IR",  # Dublin
            "BRU": ".BR", "EBR": ".BR",  # Brussels
            "WAR": ".WA", "GPW": ".WA",  # Warsaw
            "PRA": ".PR", "PSE": ".PR",  # Prague
            "BUD": ".BD", "BSE": ".BD",  # Budapest
            "BUC": ".RO", "BVB": ".RO",  # Bucharest
            "SOF": ".SO", "BSE": ".SO",  # Sofia
            "ZAG": ".ZG", "ZSE": ".ZG",  # Zagreb
            "LJU": ".LJ", "LJSE": ".LJ",  # Ljubljana
            "TAL": ".TL", "TSE": ".TL",  # Tallinn
            "RIG": ".RG", "RSE": ".RG",  # Riga
            "VIL": ".VL", "VSE": ".VL",  # Vilnius
        }
        
        # Check if ticker needs exchange suffix
        for exchange, suffix in exchange_suffixes.items():
            if ticker.endswith(exchange):
                return ticker.replace(exchange, suffix)
        
        return ticker
    
    async def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            session = await self._get_session()
            
            # Use Yahoo Finance API v8
            url = f"{self.base_url}/v8/finance/chart/{normalized_ticker}"
            params = {
                "range": "1d",
                "interval": "1m",
                "includePrePost": "true",
                "events": "div,splits"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get quote", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                result = data.get("chart", {}).get("result", [])
                
                if not result:
                    logger.warning("No quote data found", ticker=ticker)
                    return None
                
                quote_data = result[0]
                meta = quote_data.get("meta", {})
                
                quote = {
                    "ticker": ticker,
                    "price": meta.get("regularMarketPrice", 0),
                    "change": meta.get("regularMarketChange", 0),
                    "change_percent": meta.get("regularMarketChangePercent", 0),
                    "volume": meta.get("regularMarketVolume", 0),
                    "market_cap": meta.get("marketCap", 0),
                    "currency": meta.get("currency", "USD"),
                    "exchange": meta.get("exchangeName", ""),
                    "market_state": meta.get("marketState", "CLOSED"),
                    "source": "yahoo_finance",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("Retrieved quote", ticker=ticker, price=quote["price"])
                return quote
                
        except Exception as e:
            logger.error("Failed to get quote", ticker=ticker, error=str(e))
            return None
    
    async def get_financials(self, ticker: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """Get financial statements data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            session = await self._get_session()
            
            # Get financial data from Yahoo Finance
            url = f"{self.base_url}/v10/finance/quoteSummary/{normalized_ticker}"
            params = {
                "modules": "financialData,defaultKeyStatistics,incomeStatementHistory,incomeStatementHistoryQuarterly,balanceSheetHistory,balanceSheetHistoryQuarterly,cashflowStatementHistory,cashflowStatementHistoryQuarterly"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get financials", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                result = data.get("quoteSummary", {}).get("result", [])
                
                if not result:
                    logger.warning("No financial data found", ticker=ticker)
                    return None
                
                financial_data = result[0]
                
                # Extract key financial metrics
                financials = {
                    "ticker": ticker,
                    "source": "yahoo_finance",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Get most recent financial data
                if period == "quarterly":
                    income_stmt = financial_data.get("incomeStatementHistoryQuarterly", {}).get("incomeStatementHistory", [])
                    balance_sheet = financial_data.get("balanceSheetHistoryQuarterly", {}).get("balanceSheetHistory", [])
                else:
                    income_stmt = financial_data.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])
                    balance_sheet = financial_data.get("balanceSheetHistory", {}).get("balanceSheetHistory", [])
                
                if income_stmt:
                    latest_income = income_stmt[0]
                    financials.update({
                        "revenue": latest_income.get("totalRevenue", {}).get("raw", 0),
                        "net_income": latest_income.get("netIncome", {}).get("raw", 0),
                        "gross_profit": latest_income.get("grossProfit", {}).get("raw", 0),
                        "operating_income": latest_income.get("operatingIncome", {}).get("raw", 0),
                        "period": latest_income.get("endDate", {}).get("fmt", ""),
                        "quarterly": period == "quarterly"
                    })
                
                if balance_sheet:
                    latest_balance = balance_sheet[0]
                    financials.update({
                        "total_assets": latest_balance.get("totalAssets", {}).get("raw", 0),
                        "total_liabilities": latest_balance.get("totalLiab", {}).get("raw", 0),
                        "cash": latest_balance.get("cash", {}).get("raw", 0),
                        "debt": latest_balance.get("totalDebt", {}).get("raw", 0)
                    })
                
                logger.info("Retrieved financials", ticker=ticker, period=period)
                return financials
                
        except Exception as e:
            logger.error("Failed to get financials", ticker=ticker, error=str(e))
            return None
    
    async def get_historical_data(self, ticker: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            session = await self._get_session()
            
            # Map period to Yahoo Finance range
            period_map = {
                "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo",
                "6mo": "6mo", "1y": "1y", "2y": "2y", "5y": "5y",
                "10y": "10y", "ytd": "ytd", "max": "max"
            }
            
            range_param = period_map.get(period, "1y")
            
            url = f"{self.base_url}/v8/finance/chart/{normalized_ticker}"
            params = {
                "range": range_param,
                "interval": "1d",
                "includePrePost": "true",
                "events": "div,splits"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get historical data", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                result = data.get("chart", {}).get("result", [])
                
                if not result:
                    logger.warning("No historical data found", ticker=ticker)
                    return None
                
                chart_data = result[0]
                timestamps = chart_data.get("timestamp", [])
                quotes = chart_data.get("indicators", {}).get("quote", [{}])[0]
                
                historical_data = {
                    "ticker": ticker,
                    "period": period,
                    "data": [],
                    "source": "yahoo_finance",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Combine timestamps with price data
                for i, timestamp in enumerate(timestamps):
                    if i < len(quotes.get("open", [])):
                        data_point = {
                            "date": datetime.fromtimestamp(timestamp).isoformat(),
                            "open": quotes.get("open", [])[i],
                            "high": quotes.get("high", [])[i],
                            "low": quotes.get("low", [])[i],
                            "close": quotes.get("close", [])[i],
                            "volume": quotes.get("volume", [])[i]
                        }
                        historical_data["data"].append(data_point)
                
                logger.info("Retrieved historical data", ticker=ticker, period=period, points=len(historical_data["data"]))
                return historical_data
                
        except Exception as e:
            logger.error("Failed to get historical data", ticker=ticker, error=str(e))
            return None
    
    async def search_ticker(self, query: str) -> List[Dict[str, Any]]:
        """Search for ticker symbols"""
        try:
            session = await self._get_session()
            
            # Use Yahoo Finance search API
            url = f"{self.base_url}/v1/finance/search"
            params = {"q": query, "quotesCount": 10}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to search ticker", query=query, status=response.status)
                    return []
                
                data = await response.json()
                quotes = data.get("quotes", [])
                
                results = []
                for quote in quotes:
                    result = {
                        "symbol": quote.get("symbol", ""),
                        "shortname": quote.get("shortname", ""),
                        "longname": quote.get("longname", ""),
                        "exchange": quote.get("exchange", ""),
                        "quoteType": quote.get("quoteType", ""),
                        "market": quote.get("market", "")
                    }
                    results.append(result)
                
                logger.info("Searched ticker", query=query, results=len(results))
                return results
                
        except Exception as e:
            logger.error("Failed to search ticker", query=query, error=str(e))
            return []
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()