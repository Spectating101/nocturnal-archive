"""
Definitive Multi-Source Router - THE Ultimate Financial Data Aggregator
Intelligently routes requests to optimal data sources with cross-validation
"""

import asyncio
import structlog
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime
import statistics

from src.adapters.sec_facts import get_sec_facts_adapter  # Use fixed SEC Facts adapter
from src.adapters.yahoo_finance_direct import YahooFinanceDirectAdapter
from src.adapters.alpha_vantage import AlphaVantageAdapter
# Browser adapter disabled pending validation
# from src.adapters.advanced_browser_finance import get_advanced_browser_finance_adapter

logger = structlog.get_logger(__name__)

class DataSource(Enum):
    SEC_EDGAR = "sec_edgar"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    # BROWSER data source temporarily disabled pending compliance review

class DataType(Enum):
    FINANCIAL_STATEMENTS = "financial_statements"
    REAL_TIME_QUOTE = "real_time_quote"
    HISTORICAL_PRICES = "historical_prices"
    FUNDAMENTALS = "fundamentals"

class DefinitiveRouter:
    """THE Definitive Financial Data Router with cross-validation"""
    
    def __init__(self, alpha_vantage_key: str = None):
        self.browser_adapter = None  # Browser adapter disabled for now
        self.sec_adapter = get_sec_facts_adapter()  # Use fixed SEC Facts adapter with period matching
        self.yahoo_adapter = YahooFinanceDirectAdapter()
        self.alpha_adapter = AlphaVantageAdapter(alpha_vantage_key)

        # Source priorities by data type
        self.source_priorities = {
            DataType.FINANCIAL_STATEMENTS: [
                DataSource.SEC_EDGAR,      # Most authoritative for US public companies
                DataSource.YAHOO_FINANCE,  # Good coverage, real-time
                DataSource.ALPHA_VANTAGE   # Professional backup
            ],
            DataType.REAL_TIME_QUOTE: [
                DataSource.YAHOO_FINANCE,  # Real-time data
                DataSource.ALPHA_VANTAGE, # Professional backup
                DataSource.SEC_EDGAR       # Not applicable for real-time
            ],
            DataType.HISTORICAL_PRICES: [
                DataSource.YAHOO_FINANCE,  # Comprehensive historical data
                DataSource.ALPHA_VANTAGE,  # Professional backup
                DataSource.SEC_EDGAR       # Not applicable for prices
            ],
            DataType.FUNDAMENTALS: [
                DataSource.SEC_EDGAR,      # Most authoritative
                DataSource.YAHOO_FINANCE, # Good coverage
                DataSource.ALPHA_VANTAGE   # Professional backup
            ]
        }
        
        # Data quality thresholds
        self.quality_thresholds = {
            "revenue": {"min": 1e6, "max": 1e12},      # $1M to $1T
            "net_income": {"min": -1e11, "max": 1e11}, # -$100B to $100B
            "total_assets": {"min": 1e6, "max": 1e13}, # $1M to $10T
            "price": {"min": 0.01, "max": 100000},      # $0.01 to $100K
            "volume": {"min": 0, "max": 1e12}           # 0 to 1T shares
        }
    
    def _determine_data_type(self, request: Dict[str, Any]) -> DataType:
        """Determine the type of data being requested"""
        expr = request.get("expr", "").lower()
        
        # Real-time quote indicators
        if any(keyword in expr for keyword in ["price", "quote", "current", "real-time"]):
            return DataType.REAL_TIME_QUOTE
        
        # Historical price indicators
        if any(keyword in expr for keyword in ["historical", "chart", "price_history", "time_series"]):
            return DataType.HISTORICAL_PRICES
        
        # Financial statements indicators
        if any(keyword in expr for keyword in ["revenue", "income", "balance", "cash_flow", "financial"]):
            return DataType.FINANCIAL_STATEMENTS
        
        # Default to fundamentals for financial metrics
        return DataType.FUNDAMENTALS
    
    def _validate_data_quality(self, data: Dict[str, Any], concept: str) -> bool:
        """Validate data quality and reasonableness"""
        if not data or "value" not in data:
            return False
        
        value = data["value"]
        if not isinstance(value, (int, float)) or value == 0:
            return False
        
        # Get quality thresholds for the concept
        thresholds = self.quality_thresholds.get(concept, {})
        if not thresholds:
            return True  # No specific thresholds, assume valid
        
        min_val = thresholds.get("min", float('-inf'))
        max_val = thresholds.get("max", float('inf'))
        
        if value < min_val or value > max_val:
            logger.warning("Data quality validation failed", 
                         concept=concept, value=value, 
                         min_threshold=min_val, max_threshold=max_val)
            return False
        
        return True
    
    def _cross_validate_data(self, results: List[Dict[str, Any]], concept: str) -> Dict[str, Any]:
        """Cross-validate data from multiple sources"""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Extract values and sources
        values = []
        sources = []
        for result in results:
            if result and "value" in result:
                values.append(result["value"])
                sources.append(result.get("source", "unknown"))
        
        if not values:
            return None
        
        # Calculate statistics
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Determine best value (prefer median for robustness)
        best_value = median_val
        
        # Find the result with the best value
        best_result = None
        min_diff = float('inf')
        for result in results:
            if result and "value" in result:
                diff = abs(result["value"] - best_value)
                if diff < min_diff:
                    min_diff = diff
                    best_result = result
        
        if best_result:
            # Add cross-validation metadata
            best_result["cross_validation"] = {
                "sources_count": len(values),
                "mean": mean_val,
                "median": median_val,
                "std_dev": std_dev,
                "all_values": values,
                "all_sources": sources,
                "confidence": "high" if std_dev < mean_val * 0.1 else "medium" if std_dev < mean_val * 0.2 else "low"
            }
        
        return best_result
    
    async def _try_browser_data(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Browser adapter temporarily disabled"""
        logger.info("Browser data source disabled; skipping", ticker=request.get("ticker"))
        return None

    async def _try_sec_data(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to get data from SEC EDGAR"""
        try:
            ticker = request.get("ticker")
            expr = request.get("expr")
            period = request.get("period")
            freq = request.get("freq", "Q")

            result = await self.sec_adapter.get_fact(ticker, expr, period=period, freq=freq)

            if result and self._validate_data_quality(result, expr):
                result["data_source"] = DataSource.SEC_EDGAR.value
                logger.info("SEC data retrieved", ticker=ticker, expr=expr, value=result.get("value"))
                return result
            else:
                logger.warning("SEC data validation failed", ticker=ticker, expr=expr)
                return None

        except Exception as e:
            logger.warning("SEC data failed", ticker=request.get("ticker"), error=str(e))
            return None
    
    async def _try_yahoo_data(self, request: Dict[str, Any], data_type: DataType) -> Optional[Dict[str, Any]]:
        """Try to get data from Yahoo Finance"""
        try:
            ticker = request.get("ticker")
            expr = request.get("expr")
            
            if data_type == DataType.REAL_TIME_QUOTE:
                result = await self.yahoo_adapter.get_quote(ticker)
                if result:
                    result["data_source"] = DataSource.YAHOO_FINANCE.value
                    return result
                    
            elif data_type == DataType.FINANCIAL_STATEMENTS:
                period = "quarterly" if request.get("freq") == "Q" else "annual"
                result = await self.yahoo_adapter.get_financials(ticker, period)
                
                if result:
                    # Map expression to financial data
                    concept_map = {
                        "revenue": "revenue",
                        "net_income": "net_income",
                        "total_assets": "total_assets",
                        "cash": "cash"
                    }
                    
                    mapped_concept = concept_map.get(expr)
                    if mapped_concept and mapped_concept in result:
                        yahoo_result = {
                            "value": result[mapped_concept],
                            "unit": "USD",
                            "period": result.get("period", ""),
                            "concept": expr,
                            "data_source": DataSource.YAHOO_FINANCE.value,
                            "source": "yahoo_finance"
                        }
                        
                        if self._validate_data_quality(yahoo_result, expr):
                            logger.info("Yahoo Finance data retrieved", ticker=ticker, expr=expr, value=yahoo_result["value"])
                            return yahoo_result
            
            elif data_type == DataType.HISTORICAL_PRICES:
                period = request.get("period", "1y")
                result = await self.yahoo_adapter.get_historical_data(ticker, period)
                if result:
                    result["data_source"] = DataSource.YAHOO_FINANCE.value
                    return result
            
            return None
                
        except Exception as e:
            logger.warning("Yahoo Finance data failed", ticker=request.get("ticker"), error=str(e))
            return None
    
    async def _try_alpha_vantage_data(self, request: Dict[str, Any], data_type: DataType) -> Optional[Dict[str, Any]]:
        """Try to get data from Alpha Vantage"""
        try:
            ticker = request.get("ticker")
            expr = request.get("expr")
            
            if data_type == DataType.REAL_TIME_QUOTE:
                result = await self.alpha_adapter.get_quote(ticker)
                if result:
                    result["data_source"] = DataSource.ALPHA_VANTAGE.value
                    return result
                    
            elif data_type == DataType.FINANCIAL_STATEMENTS:
                period = "quarterly" if request.get("freq") == "Q" else "annual"
                result = await self.alpha_adapter.get_financials(ticker, period)
                
                if result:
                    # Map expression to financial data
                    concept_map = {
                        "revenue": "revenue",
                        "net_income": "net_income",
                        "total_assets": "total_assets",
                        "cash": "cash"
                    }
                    
                    mapped_concept = concept_map.get(expr)
                    if mapped_concept and mapped_concept in result:
                        alpha_result = {
                            "value": result[mapped_concept],
                            "unit": "USD",
                            "period": result.get("fiscal_date_ending", ""),
                            "concept": expr,
                            "data_source": DataSource.ALPHA_VANTAGE.value,
                            "source": "alpha_vantage"
                        }
                        
                        if self._validate_data_quality(alpha_result, expr):
                            logger.info("Alpha Vantage data retrieved", ticker=ticker, expr=expr, value=alpha_result["value"])
                            return alpha_result
            
            elif data_type == DataType.HISTORICAL_PRICES:
                period = request.get("period", "1y")
                result = await self.alpha_adapter.get_historical_data(ticker, period)
                if result:
                    result["data_source"] = DataSource.ALPHA_VANTAGE.value
                    return result
            
            return None
                
        except Exception as e:
            logger.warning("Alpha Vantage data failed", ticker=request.get("ticker"), error=str(e))
            return None
    
    async def get_data(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get financial data using optimal source routing with cross-validation"""
        ticker = request.get("ticker", "")
        expr = request.get("expr", "")
        
        logger.info("Routing data request", ticker=ticker, expr=expr)
        
        # Determine optimal sources
        data_type = self._determine_data_type(request)
        sources = self.source_priorities.get(data_type, [DataSource.YAHOO_FINANCE])
        
        logger.info("Determined routing strategy", 
                   data_type=data_type.value, 
                   sources=[s.value for s in sources])
        
        # Try sources in parallel for cross-validation
        tasks = []
        source_methods = {
            DataSource.SEC_EDGAR: self._try_sec_data,
            DataSource.YAHOO_FINANCE: self._try_yahoo_data,
            DataSource.ALPHA_VANTAGE: self._try_alpha_vantage_data
        }
        
        for source in sources:
            method = source_methods.get(source)
            if method:
                if source == DataSource.SEC_EDGAR:
                    tasks.append(method(request))
                else:
                    tasks.append(method(request, data_type))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_results.append(result)
        
        if not valid_results:
            logger.warning("No valid data sources", ticker=ticker, expr=expr)
            return None
        
        # Cross-validate results if multiple sources
        if len(valid_results) > 1:
            best_result = self._cross_validate_data(valid_results, expr)
            if best_result:
                logger.info("Cross-validation completed", 
                           ticker=ticker, expr=expr, 
                           sources_count=len(valid_results),
                           confidence=best_result.get("cross_validation", {}).get("confidence", "unknown"))
                return best_result
        
        # Return best single result
        best_result = valid_results[0]
        logger.info("Single source data retrieved", 
                   ticker=ticker, expr=expr, 
                   source=best_result.get("data_source", "unknown"))
        return best_result
    
    async def close(self):
        """Close all adapters"""
        await self.sec_adapter.close()
        await self.yahoo_adapter.close()
        await self.alpha_adapter.close()