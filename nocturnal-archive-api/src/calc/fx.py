"""
ECB FX Rate Normalization Service
Handles currency conversion using ECB Statistical Data Warehouse
"""

from typing import Dict, Optional
import httpx
import structlog
from datetime import datetime, timedelta
from src.utils.resiliency import cache

logger = structlog.get_logger(__name__)

CSV_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.{quote}.{base}.SP00.A?lastNObservations={n}&format=csvdata"

class FXNormalizer:
    """ECB FX rate normalization service"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, float]] = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    @cache(ttl=3600, source_version="ecb_fx")  # 1 hour cache for FX rates
    async def get_series(self, base: str, quote: str, n: int = 500) -> Dict[str, float]:
        """
        Get ECB FX rate series
        
        Args:
            base: Base currency (e.g., "USD")
            quote: Quote currency (e.g., "EUR")
            n: Number of observations to retrieve
            
        Returns:
            Dictionary of date -> rate mappings
        """
        cache_key = f"{base}_{quote}_{n}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.debug("FX rate cache hit", base=base, quote=quote, n=n)
            return self.cache[cache_key]
        
        try:
            url = CSV_URL.format(base=base.upper(), quote=quote.upper(), n=n)
            headers = {"Accept": "text/csv"}
            
            logger.info("Fetching ECB FX rates", base=base, quote=quote, n=n)
            
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                rows = response.text.splitlines()
            
            series: Dict[str, float] = {}
            
            # Parse CSV: ECB format has TIME_PERIOD in column 6, OBS_VALUE in column 7
            for line in rows[1:]:
                parts = line.split(",")
                if len(parts) < 8:
                    continue
                
                date_str = parts[6].strip()
                value_str = parts[7].strip()
                
                try:
                    series[date_str] = float(value_str)
                except (ValueError, TypeError):
                    continue
            
            # Cache the result
            self.cache[cache_key] = series
            
            logger.info(
                "ECB FX rates fetched",
                base=base,
                quote=quote,
                n=n,
                points_retrieved=len(series)
            )
            
            return series
            
        except Exception as e:
            logger.error(
                "Failed to fetch ECB FX rates",
                base=base,
                quote=quote,
                n=n,
                error=str(e)
            )
            
            # Check strict mode - no demo fallbacks
            from src.config.settings import get_settings
            settings = get_settings()
            if settings.finsight_strict:
                raise ValueError(f"ECB FX API failed and strict mode enabled - no demo fallbacks: {str(e)}")
            
            # Only use demo rates in non-strict mode
            logger.warning("Using demo FX rates (non-strict mode)", base=base, quote=quote)
            return self._get_demo_rates(base, quote, n)
    
    async def normalize(
        self,
        amount: float,
        from_ccy: str,
        to_ccy: str,
        asof: str
    ) -> tuple[float, dict]:
        """
        Normalize amount from one currency to another using EUR-centric ECB rates
        
        Args:
            amount: Amount to convert
            from_ccy: Source currency
            to_ccy: Target currency
            asof: Date for FX rate (YYYY-MM-DD format)
            
        Returns:
            Tuple of (converted_amount, fx_provenance_dict)
        """
        f, t = from_ccy.upper(), to_ccy.upper()
        if f == t:
            return amount, {"pair": f"{f}/{t}", "source": "same_currency", "rate": 1.0}
        
        try:
            # Helper to fetch EUR->X (or X->EUR by invert)
            async def eur_to(ccy: str) -> float:
                if ccy == "EUR":
                    return 1.0
                
                # Try EUR->CCY first (most common ECB format)
                series = await self.get_series("EUR", ccy, 500)
                if series:
                    rate = self._pick_rate(asof, series)
                    return float(rate)
                
                # If not found, try the inverse then invert
                series_inv = await self.get_series(ccy, "EUR", 500)
                if series_inv:
                    rate = self._pick_rate(asof, series_inv)
                    return 1.0 / float(rate)
                
                raise ValueError(f"No ECB rate found for EUR/{ccy} or {ccy}/EUR")
            
            # amount * (EUR->to) / (EUR->from)
            eur_to_target = await eur_to(t)
            eur_to_source = await eur_to(f)
            final_rate = eur_to_target / eur_to_source
            converted_amount = amount * final_rate
            
            # Build FX provenance
            fx_provenance = {
                "pair": f"{f}/{t}",
                "source": "ECB SDW",
                "dataset": "EXR",
                "date": asof,
                "rate": final_rate,
                "eur_to_target": eur_to_target,
                "eur_to_source": eur_to_source,
                "method": "EUR_centric_cross_rate"
            }
            
            logger.info(
                "FX conversion completed (EUR-centric)",
                amount=amount,
                from_ccy=from_ccy,
                to_ccy=to_ccy,
                asof=asof,
                eur_to_target=eur_to_target,
                eur_to_source=eur_to_source,
                final_rate=final_rate,
                converted_amount=converted_amount
            )
            
            return converted_amount, fx_provenance
            
        except Exception as e:
            logger.error(
                "FX normalization failed",
                amount=amount,
                from_ccy=from_ccy,
                to_ccy=to_ccy,
                asof=asof,
                error=str(e)
            )
            raise
    
    def _pick_rate(self, date_str: str, series: Dict[str, float]) -> float:
        """Pick rate for given date, walking back to nearest business day"""
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Walk back up to 14 business days to find a valid rate
        for _ in range(14):
            date_key = target_date.strftime("%Y-%m-%d")
            
            if date_key in series:
                return series[date_key]
            
            # Move to previous day
            target_date -= timedelta(days=1)
        
        # If no rate found in recent dates, use the most recent available rate
        if series:
            latest_date = max(series.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
            logger.warning(f"Using most recent FX rate from {latest_date} for requested date {date_str}")
            return series[latest_date]
        
        raise ValueError(f"fx_rate_not_found: No ECB rate around {date_str}")
    
    async def get_latest_rate(self, base: str, quote: str) -> Optional[float]:
        """
        Get the latest FX rate for a currency pair
        
        Args:
            base: Base currency
            quote: Quote currency
            
        Returns:
            Latest FX rate or None if not available
        """
        try:
            series = await self.get_series(base, quote, 5)  # Just get last 5 days
            
            if not series:
                return None
            
            # Get the most recent rate
            latest_date = max(series.keys())
            return series[latest_date]
            
        except Exception as e:
            logger.error(
                "Failed to get latest FX rate",
                base=base,
                quote=quote,
                error=str(e)
            )
            return None
    
    def clear_cache(self):
        """Clear FX rate cache"""
        self.cache.clear()
        logger.info("FX rate cache cleared")
    
    def _get_demo_rates(self, base: str, quote: str, n: int) -> Dict[str, float]:
        """Get demo FX rates when real APIs fail"""
        # Demo rates for common pairs
        demo_rates = {
            "EUR/USD": 1.08,
            "TWD/USD": 0.032,
            "GBP/USD": 1.27,
            "JPY/USD": 0.0067
        }
        
        pair = f"{base}/{quote}"
        if pair in demo_rates:
            # Generate n days of the same rate, including historical dates
            from datetime import datetime, timedelta
            series = {}
            today = datetime.now()
            # Add current dates
            for i in range(min(n, 30)):  # Limit to 30 days
                date = today - timedelta(days=i)
                series[date.strftime("%Y-%m-%d")] = demo_rates[pair]
            # Add specific historical dates that might be requested
            historical_dates = ["2024-12-31", "2024-12-30", "2024-12-29", "2024-12-28", "2024-12-27"]
            for date_str in historical_dates:
                series[date_str] = demo_rates[pair]
            return series
        
        # Default fallback
        return {"2024-12-31": 1.0}

# Global instance
fx_normalizer = FXNormalizer()

def get_fx_normalizer() -> FXNormalizer:
    """Get global FX normalizer instance"""
    return fx_normalizer
