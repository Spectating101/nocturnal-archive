"""
Multi-Source Data Router
Intelligently routes financial data requests to appropriate sources
"""

import structlog
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import asyncio
from datetime import datetime

from src.adapters.sec_facts import SECFactsAdapter
from src.adapters.yahoo_finance import YahooFinanceAdapter

logger = structlog.get_logger(__name__)

class DataSource(Enum):
    SEC_EDGAR = "sec_edgar"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    POLYGON = "polygon"

class DataType(Enum):
    FINANCIAL_STATEMENTS = "financial_statements"
    REAL_TIME_QUOTE = "real_time_quote"
    HISTORICAL_PRICES = "historical_prices"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"

class MultiSourceRouter:
    """Routes financial data requests to appropriate sources"""
    
    def __init__(self):
        self.sec_adapter = SECFactsAdapter()
        self.yahoo_adapter = YahooFinanceAdapter()
        
        # Source priorities by data type
        self.source_priorities = {
            DataType.FINANCIAL_STATEMENTS: [
                DataSource.SEC_EDGAR,  # Most authoritative for US public companies
                # DataSource.YAHOO_FINANCE,  # DISABLED: yfinance has corrupted data
                DataSource.ALPHA_VANTAGE
            ],
            DataType.REAL_TIME_QUOTE: [
                DataSource.YAHOO_FINANCE,  # Real-time data
                DataSource.IEX_CLOUD,
                DataSource.POLYGON
            ],
            DataType.HISTORICAL_PRICES: [
                DataSource.YAHOO_FINANCE,  # Comprehensive historical data
                DataSource.ALPHA_VANTAGE,
                DataSource.IEX_CLOUD
            ],
            DataType.FUNDAMENTALS: [
                DataSource.SEC_EDGAR,  # Authoritative fundamentals
                DataSource.YAHOO_FINANCE,
                DataSource.ALPHA_VANTAGE
            ]
        }
        
        # Ticker patterns for source routing
        self.crypto_patterns = ["BTC", "ETH", "ADA", "DOT", "LINK", "MATIC", "SOL", "AVAX"]
        self.forex_patterns = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
        self.private_company_indicators = [
            # Common private company naming patterns
            "LLC", "Inc.", "Corp.", "Ltd.", "Co.", "Holdings", "Group", "Partners"
        ]
    
    def _determine_data_type(self, request: Dict[str, Any]) -> DataType:
        """Determine what type of data is being requested"""
        expr = request.get("expr", "").lower()
        ticker = request.get("ticker", "").upper()
        
        # Real-time quote indicators
        if any(keyword in expr for keyword in ["price", "quote", "market_cap", "pe_ratio"]):
            return DataType.REAL_TIME_QUOTE
        
        # Historical data indicators  
        if any(keyword in expr for keyword in ["historical", "chart", "price_history"]):
            return DataType.HISTORICAL_PRICES
        
        # Financial statements indicators
        if any(keyword in expr for keyword in ["revenue", "income", "balance", "cash_flow"]):
            return DataType.FINANCIAL_STATEMENTS
        
        # Default to fundamentals for financial metrics
        return DataType.FUNDAMENTALS
    
    def _determine_ticker_type(self, ticker: str) -> str:
        """Determine if ticker is crypto, forex, private, or public company"""
        ticker_upper = ticker.upper()
        
        if ticker_upper in self.crypto_patterns:
            return "crypto"
        elif ticker_upper in self.forex_patterns:
            return "forex"
        elif any(indicator in ticker_upper for indicator in self.private_company_indicators):
            return "private_company"
        else:
            return "public_company"
    
    def _get_optimal_sources(self, data_type: DataType, ticker_type: str) -> List[DataSource]:
        """Get optimal data sources for the request"""
        base_sources = self.source_priorities.get(data_type, [DataSource.YAHOO_FINANCE])
        
        # Adjust sources based on ticker type
        if ticker_type == "crypto":
            # Crypto works best with Yahoo Finance
            return [DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE]
        elif ticker_type == "forex":
            # Forex works best with Yahoo Finance
            return [DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE]
        elif ticker_type == "private_company":
            # Private companies need alternative data sources
            return [DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE]
        else:
            # Public companies can use SEC data
            return base_sources
    
    async def _try_sec_data(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to get data from SEC EDGAR"""
        try:
            ticker = request.get("ticker")
            expr = request.get("expr")
            period = request.get("period")
            freq = request.get("freq", "Q")
            
            result = await self.sec_adapter.get_fact(
                ticker=ticker,
                concept=expr,
                period=period,
                freq=freq
            )
            
            if result:
                result["data_source"] = DataSource.SEC_EDGAR.value
                logger.info("SEC data retrieved", ticker=ticker, expr=expr)
                return result
                
        except Exception as e:
            logger.warning("SEC data failed", ticker=request.get("ticker"), error=str(e))
        
        return None
    
    async def _try_yahoo_data(self, request: Dict[str, Any], data_type: DataType) -> Optional[Dict[str, Any]]:
        """Try to get data from Yahoo Finance"""
        try:
            ticker = request.get("ticker")
            
            if data_type == DataType.REAL_TIME_QUOTE:
                result = await self.yahoo_adapter.get_quote(ticker)
            elif data_type == DataType.FINANCIAL_STATEMENTS:
                period = "quarterly" if request.get("freq") == "Q" else "annual"
                result = await self.yahoo_adapter.get_financials(ticker, period)
            elif data_type == DataType.HISTORICAL_PRICES:
                period = "1y"  # Default to 1 year
                result = await self.yahoo_adapter.get_historical(ticker, period)
            else:
                # Default to quote data
                result = await self.yahoo_adapter.get_quote(ticker)
            
            if result:
                result["data_source"] = DataSource.YAHOO_FINANCE.value
                logger.info("Yahoo Finance data retrieved", ticker=ticker, data_type=data_type.value)
                return result
                
        except Exception as e:
            logger.warning("Yahoo Finance data failed", ticker=request.get("ticker"), error=str(e))
        
        return None
    
    async def get_data(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get financial data using optimal source routing"""
        ticker = request.get("ticker", "")
        expr = request.get("expr", "")
        
        logger.info("Routing data request", ticker=ticker, expr=expr)
        
        # Determine optimal sources
        data_type = self._determine_data_type(request)
        ticker_type = self._determine_ticker_type(ticker)
        sources = self._get_optimal_sources(data_type, ticker_type)
        
        logger.info("Determined routing strategy", 
                   data_type=data_type.value, 
                   ticker_type=ticker_type, 
                   sources=[s.value for s in sources])
        
        # Try sources in order of priority
        for source in sources:
            try:
                if source == DataSource.SEC_EDGAR:
                    result = await self._try_sec_data(request)
                    if result:
                        return result
                        
                elif source == DataSource.YAHOO_FINANCE:
                    result = await self._try_yahoo_data(request, data_type)
                    if result:
                        return result
                        
                # Add other sources here as they're implemented
                # elif source == DataSource.ALPHA_VANTAGE:
                #     result = await self._try_alpha_vantage_data(request)
                #     if result:
                #         return result
                
            except Exception as e:
                logger.warning("Source failed", source=source.value, error=str(e))
                continue
        
        logger.warning("All sources failed", ticker=ticker, expr=expr)
        return None
    
    async def get_universal_data(self, ticker: str, metric: str) -> Optional[Dict[str, Any]]:
        """Universal data endpoint that works with any ticker type"""
        request = {
            "ticker": ticker,
            "expr": metric,
            "period": None,
            "freq": "Q"
        }
        
        return await self.get_data(request)

# Global instance
multi_source_router = MultiSourceRouter()

