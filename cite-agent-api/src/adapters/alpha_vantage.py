"""
Alpha Vantage Adapter - THE Definitive Financial Data Backup Source
Professional financial data API for comprehensive market coverage
"""

import asyncio
import aiohttp
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = structlog.get_logger(__name__)

class AlphaVantageAdapter:
    """Alpha Vantage API adapter for professional financial data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "demo"  # Use demo key for testing
        self.base_url = "https://www.alphavantage.co/query"
        self.session = None
        
    async def _get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "FinSight Financial Data (contact@nocturnal.dev)"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote data"""
        try:
            session = await self._get_session()
            
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get quote", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                
                if "Error Message" in data:
                    logger.error("Alpha Vantage error", ticker=ticker, error=data["Error Message"])
                    return None
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", ticker=ticker, note=data["Note"])
                    return None
                
                quote_data = data.get("Global Quote", {})
                if not quote_data:
                    logger.warning("No quote data found", ticker=ticker)
                    return None
                
                quote = {
                    "ticker": ticker,
                    "price": float(quote_data.get("05. price", 0)),
                    "change": float(quote_data.get("09. change", 0)),
                    "change_percent": float(quote_data.get("10. change percent", "0%").replace("%", "")),
                    "volume": int(quote_data.get("06. volume", 0)),
                    "high": float(quote_data.get("03. high", 0)),
                    "low": float(quote_data.get("04. low", 0)),
                    "open": float(quote_data.get("02. open", 0)),
                    "previous_close": float(quote_data.get("08. previous close", 0)),
                    "source": "alpha_vantage",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("Retrieved quote", ticker=ticker, price=quote["price"])
                return quote
                
        except Exception as e:
            logger.error("Failed to get quote", ticker=ticker, error=str(e))
            return None
    
    async def get_income_statement(self, ticker: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """Get income statement data"""
        try:
            session = await self._get_session()
            
            function = "INCOME_STATEMENT"
            params = {
                "function": function,
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get income statement", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                
                if "Error Message" in data:
                    logger.error("Alpha Vantage error", ticker=ticker, error=data["Error Message"])
                    return None
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", ticker=ticker, note=data["Note"])
                    return None
                
                # Get quarterly or annual data
                statements = data.get("quarterlyReports" if period == "quarterly" else "annualReports", [])
                if not statements:
                    logger.warning("No income statement data found", ticker=ticker, period=period)
                    return None
                
                latest_statement = statements[0]
                
                income_data = {
                    "ticker": ticker,
                    "period": period,
                    "fiscal_date_ending": latest_statement.get("fiscalDateEnding", ""),
                    "revenue": float(latest_statement.get("totalRevenue", 0)),
                    "gross_profit": float(latest_statement.get("grossProfit", 0)),
                    "operating_income": float(latest_statement.get("operatingIncome", 0)),
                    "net_income": float(latest_statement.get("netIncome", 0)),
                    "ebitda": float(latest_statement.get("ebitda", 0)),
                    "source": "alpha_vantage",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("Retrieved income statement", ticker=ticker, period=period)
                return income_data
                
        except Exception as e:
            logger.error("Failed to get income statement", ticker=ticker, error=str(e))
            return None
    
    async def get_balance_sheet(self, ticker: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """Get balance sheet data"""
        try:
            session = await self._get_session()
            
            params = {
                "function": "BALANCE_SHEET",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get balance sheet", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                
                if "Error Message" in data:
                    logger.error("Alpha Vantage error", ticker=ticker, error=data["Error Message"])
                    return None
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", ticker=ticker, note=data["Note"])
                    return None
                
                # Get quarterly or annual data
                statements = data.get("quarterlyReports" if period == "quarterly" else "annualReports", [])
                if not statements:
                    logger.warning("No balance sheet data found", ticker=ticker, period=period)
                    return None
                
                latest_statement = statements[0]
                
                balance_data = {
                    "ticker": ticker,
                    "period": period,
                    "fiscal_date_ending": latest_statement.get("fiscalDateEnding", ""),
                    "total_assets": float(latest_statement.get("totalAssets", 0)),
                    "total_liabilities": float(latest_statement.get("totalLiabilities", 0)),
                    "total_equity": float(latest_statement.get("totalShareholderEquity", 0)),
                    "cash": float(latest_statement.get("cashAndCashEquivalentsAtCarryingValue", 0)),
                    "debt": float(latest_statement.get("totalDebt", 0)),
                    "source": "alpha_vantage",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("Retrieved balance sheet", ticker=ticker, period=period)
                return balance_data
                
        except Exception as e:
            logger.error("Failed to get balance sheet", ticker=ticker, error=str(e))
            return None
    
    async def get_cash_flow(self, ticker: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """Get cash flow statement data"""
        try:
            session = await self._get_session()
            
            params = {
                "function": "CASH_FLOW",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get cash flow", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                
                if "Error Message" in data:
                    logger.error("Alpha Vantage error", ticker=ticker, error=data["Error Message"])
                    return None
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", ticker=ticker, note=data["Note"])
                    return None
                
                # Get quarterly or annual data
                statements = data.get("quarterlyReports" if period == "quarterly" else "annualReports", [])
                if not statements:
                    logger.warning("No cash flow data found", ticker=ticker, period=period)
                    return None
                
                latest_statement = statements[0]
                
                cashflow_data = {
                    "ticker": ticker,
                    "period": period,
                    "fiscal_date_ending": latest_statement.get("fiscalDateEnding", ""),
                    "operating_cashflow": float(latest_statement.get("operatingCashflow", 0)),
                    "net_income": float(latest_statement.get("netIncome", 0)),
                    "capital_expenditures": float(latest_statement.get("capitalExpenditures", 0)),
                    "free_cashflow": float(latest_statement.get("operatingCashflow", 0)) - float(latest_statement.get("capitalExpenditures", 0)),
                    "source": "alpha_vantage",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("Retrieved cash flow", ticker=ticker, period=period)
                return cashflow_data
                
        except Exception as e:
            logger.error("Failed to get cash flow", ticker=ticker, error=str(e))
            return None
    
    async def get_financials(self, ticker: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """Get comprehensive financial data"""
        try:
            # Get all financial statements
            income_task = self.get_income_statement(ticker, period)
            balance_task = self.get_balance_sheet(ticker, period)
            cashflow_task = self.get_cash_flow(ticker, period)
            
            income_data, balance_data, cashflow_data = await asyncio.gather(
                income_task, balance_task, cashflow_task, return_exceptions=True
            )
            
            # Combine all financial data
            financials = {
                "ticker": ticker,
                "period": period,
                "source": "alpha_vantage",
                "timestamp": datetime.now().isoformat()
            }
            
            if isinstance(income_data, dict):
                financials.update(income_data)
            
            if isinstance(balance_data, dict):
                financials.update(balance_data)
            
            if isinstance(cashflow_data, dict):
                financials.update(cashflow_data)
            
            logger.info("Retrieved comprehensive financials", ticker=ticker, period=period)
            return financials
            
        except Exception as e:
            logger.error("Failed to get financials", ticker=ticker, error=str(e))
            return None
    
    async def get_historical_data(self, ticker: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        try:
            session = await self._get_session()
            
            # Map period to Alpha Vantage output size
            period_map = {
                "1mo": "compact", "3mo": "compact", "6mo": "compact",
                "1y": "compact", "2y": "full", "5y": "full", "10y": "full", "max": "full"
            }
            
            output_size = period_map.get(period, "compact")
            
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "outputsize": output_size,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error("Failed to get historical data", ticker=ticker, status=response.status)
                    return None
                
                data = await response.json()
                
                if "Error Message" in data:
                    logger.error("Alpha Vantage error", ticker=ticker, error=data["Error Message"])
                    return None
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", ticker=ticker, note=data["Note"])
                    return None
                
                time_series = data.get("Time Series (Daily)", {})
                if not time_series:
                    logger.warning("No historical data found", ticker=ticker)
                    return None
                
                historical_data = {
                    "ticker": ticker,
                    "period": period,
                    "data": [],
                    "source": "alpha_vantage",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Convert time series to list format
                for date, values in time_series.items():
                    data_point = {
                        "date": date,
                        "open": float(values.get("1. open", 0)),
                        "high": float(values.get("2. high", 0)),
                        "low": float(values.get("3. low", 0)),
                        "close": float(values.get("4. close", 0)),
                        "volume": int(values.get("5. volume", 0))
                    }
                    historical_data["data"].append(data_point)
                
                # Sort by date (newest first)
                historical_data["data"].sort(key=lambda x: x["date"], reverse=True)
                
                logger.info("Retrieved historical data", ticker=ticker, period=period, points=len(historical_data["data"]))
                return historical_data
                
        except Exception as e:
            logger.error("Failed to get historical data", ticker=ticker, error=str(e))
            return None
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()