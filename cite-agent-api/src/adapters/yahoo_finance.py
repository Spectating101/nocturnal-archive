"""
Yahoo Finance Adapter
Provides real-time and historical financial data for global markets
"""

import structlog
import aiohttp
import yfinance as yf
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import pandas as pd

logger = structlog.get_logger(__name__)

# Data validation ranges - Claude's security audit recommendation
SANITY_CHECKS = {
    "AAPL": {"revenue_Q": (80e9, 130e9), "revenue_A": (350e9, 450e9)},
    "MSFT": {"revenue_Q": (50e9, 70e9), "revenue_A": (200e9, 250e9)},
    "GOOGL": {"revenue_Q": (70e9, 90e9), "revenue_A": (280e9, 350e9)},
}

class YahooFinanceAdapter:
    """Yahoo Finance adapter for real-time and historical data"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com"
        self.session = None
        self.sanity_checks = SANITY_CHECKS

    def _validate_value(self, ticker: str, concept: str, value: float, freq: str = "Q") -> bool:
        """Validate financial data against known ranges"""
        if not value or ticker not in self.sanity_checks:
            return True

        key = f"{concept}_{freq}"
        if key in self.sanity_checks[ticker]:
            min_val, max_val = self.sanity_checks[ticker][key]
            if not (min_val <= value <= max_val):
                logger.warning(
                    "Yahoo Finance data validation failed",
                    ticker=ticker,
                    concept=concept,
                    value=value,
                    expected_range=f"[{min_val:,.0f}, {max_val:,.0f}]"
                )
                return False
        return True
        
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
        # Handle common suffixes and exchanges
        ticker = ticker.upper().strip()
        
        # Crypto mappings
        crypto_mappings = {
            "BTC": "BTC-USD",
            "ETH": "ETH-USD", 
            "ADA": "ADA-USD",
            "DOT": "DOT-USD",
            "LINK": "LINK-USD"
        }
        
        if ticker in crypto_mappings:
            return crypto_mappings[ticker]
            
        # Forex mappings  
        forex_mappings = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X"
        }
        
        if ticker in forex_mappings:
            return forex_mappings[ticker]
            
        return ticker
    
    async def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            
            # Use yfinance for real-time data
            ticker_obj = yf.Ticker(normalized_ticker)
            info = ticker_obj.info
            
            if not info or 'symbol' not in info:
                logger.warning("No data found for ticker", ticker=ticker, normalized=normalized_ticker)
                return None
            
            # Extract key financial metrics
            quote_data = {
                "ticker": ticker,
                "symbol": info.get('symbol', ticker),
                "price": info.get('currentPrice') or info.get('regularMarketPrice'),
                "currency": info.get('currency', 'USD'),
                "market_cap": info.get('marketCap'),
                "volume": info.get('volume'),
                "avg_volume": info.get('averageVolume'),
                "pe_ratio": info.get('trailingPE'),
                "eps": info.get('trailingEps'),
                "dividend_yield": info.get('dividendYield'),
                "52w_high": info.get('fiftyTwoWeekHigh'),
                "52w_low": info.get('fiftyTwoWeekLow'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "country": info.get('country'),
                "exchange": info.get('exchange'),
                "market_state": info.get('marketState', 'CLOSED'),
                "source": "Yahoo Finance",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Build citation
            citation = {
                "source": "Yahoo Finance",
                "url": f"https://finance.yahoo.com/quote/{normalized_ticker}",
                "exchange": info.get('exchange'),
                "currency": info.get('currency', 'USD'),
                "market_state": info.get('marketState', 'CLOSED')
            }
            
            quote_data["citations"] = [citation]
            
            logger.info("Retrieved Yahoo Finance quote", ticker=ticker, price=quote_data.get("price"))
            return quote_data
            
        except Exception as e:
            logger.error("Failed to get Yahoo Finance quote", ticker=ticker, error=str(e))
            return None
    
    async def get_financials(self, ticker: str, period: str = "annual") -> Optional[Dict[str, Any]]:
        """Get financial statements data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            ticker_obj = yf.Ticker(normalized_ticker)
            
            # Get financial data
            if period == "annual":
                financials = ticker_obj.financials
                quarterly = False
            else:
                financials = ticker_obj.quarterly_financials  
                quarterly = True
            
            if financials is None or financials.empty:
                logger.warning("No financial data available", ticker=ticker)
                return None
            
            # Convert to dict with latest period
            latest_period = financials.columns[0] if len(financials.columns) > 0 else None
            if latest_period is None:
                return None
                
            financial_data = financials[latest_period].to_dict()
            
            # Normalize financial concepts
            normalized_data = {
                "ticker": ticker,
                "period": latest_period.strftime("%Y-%m-%d") if hasattr(latest_period, 'strftime') else str(latest_period),
                "quarterly": quarterly,
                "currency": "USD",  # Yahoo Finance typically returns USD
                "revenue": financial_data.get("Total Revenue") or financial_data.get("Revenue"),
                "cost_of_revenue": financial_data.get("Cost Of Goods Sold") or financial_data.get("Cost of Revenue"),
                "gross_profit": financial_data.get("Gross Profit"),
                "operating_income": financial_data.get("Operating Income"),
                "net_income": financial_data.get("Net Income"),
                "total_assets": financial_data.get("Total Assets"),
                "total_liabilities": financial_data.get("Total Liabilities"),
                "shareholders_equity": financial_data.get("Stockholders Equity"),
                "cash": financial_data.get("Cash"),
                "debt": financial_data.get("Total Debt"),
                "source": "Yahoo Finance",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Build citation
            citation = {
                "source": "Yahoo Finance Financials",
                "url": f"https://finance.yahoo.com/quote/{normalized_ticker}/financials",
                "period": latest_period.strftime("%Y-%m-%d") if hasattr(latest_period, 'strftime') else str(latest_period),
                "quarterly": quarterly
            }
            
            normalized_data["citations"] = [citation]
            
            logger.info("Retrieved Yahoo Finance financials", ticker=ticker, period=latest_period)
            return normalized_data
            
        except Exception as e:
            logger.error("Failed to get Yahoo Finance financials", ticker=ticker, error=str(e))
            return None
    
    async def get_historical(self, ticker: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        try:
            normalized_ticker = self._normalize_ticker(ticker)
            ticker_obj = yf.Ticker(normalized_ticker)
            
            # Get historical data
            hist = ticker_obj.history(period=period)
            
            if hist is None or hist.empty:
                logger.warning("No historical data available", ticker=ticker)
                return None
            
            # Convert to list of dicts
            hist_data = []
            for date, row in hist.iterrows():
                hist_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row['Open']) if pd.notna(row['Open']) else None,
                    "high": float(row['High']) if pd.notna(row['High']) else None,
                    "low": float(row['Low']) if pd.notna(row['Low']) else None,
                    "close": float(row['Close']) if pd.notna(row['Close']) else None,
                    "volume": int(row['Volume']) if pd.notna(row['Volume']) else None
                })
            
            historical_data = {
                "ticker": ticker,
                "period": period,
                "data_points": len(hist_data),
                "data": hist_data,
                "source": "Yahoo Finance",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Build citation
            citation = {
                "source": "Yahoo Finance Historical",
                "url": f"https://finance.yahoo.com/quote/{normalized_ticker}/history",
                "period": period
            }
            
            historical_data["citations"] = [citation]
            
            logger.info("Retrieved Yahoo Finance historical data", ticker=ticker, period=period, points=len(hist_data))
            return historical_data
            
        except Exception as e:
            logger.error("Failed to get Yahoo Finance historical data", ticker=ticker, error=str(e))
            return None

