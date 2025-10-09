"""
Federal Reserve Economic Data (FRED) API adapter
"""

import asyncio
import aiohttp
import structlog
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import SourceAdapter, AdapterOutput, Provenance, SourceUnavailableError, ParseError

logger = structlog.get_logger(__name__)

class FREDAdapter(SourceAdapter):
    """Adapter for Federal Reserve Economic Data (FRED) API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = None  # Will be set from environment
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 0.5  # 120 requests per minute = 0.5 seconds between requests
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Get API key from environment
        import os
        self.api_key = os.getenv("FRED_API_KEY")
        
        self.session = aiohttp.ClientSession(
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Respect FRED rate limiting guidelines"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug("FRED rate limit sleep", sleep_time=sleep_time)
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def search(self, **kwargs) -> AdapterOutput:
        """
        Search for economic series
        
        Args:
            series_id: FRED series ID (required)
            limit: Maximum number of observations (optional, default 100)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            AdapterOutput with economic series data
        """
        if not self.session:
            raise RuntimeError("FREDAdapter must be used as async context manager")
        
        series_id = kwargs.get("series_id")
        if not series_id:
            raise ValueError("series_id is required for FRED search")
        
        limit = kwargs.get("limit", 100)
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        
        try:
            # Build URL
            url = f"{self.base_url}series/observations"
            params = {
                "series_id": series_id,
                "file_type": "json",
                "limit": limit
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            if start_date:
                params["observation_start"] = start_date
            if end_date:
                params["observation_end"] = end_date
            
            logger.info(
                "Fetching FRED series",
                series_id=series_id,
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )
            
            # Apply rate limiting
            await self._rate_limit()
            
            # Make request
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise SourceUnavailableError(f"FRED API failed: {response.status}")
                
                raw_data = await response.json()
            
            # Parse response
            parsed_data = await self.parse(raw_data, series_id)
            
            logger.info(
                "FRED series fetch completed",
                series_id=series_id,
                observations_found=len(parsed_data["data"].get("observations", []))
            )
            
            return parsed_data
            
        except Exception as e:
            logger.error(
                "FRED series fetch failed",
                series_id=series_id,
                error=str(e)
            )
            raise
    
    async def fetch(self, **kwargs) -> AdapterOutput:
        """Fetch is the same as search for FRED"""
        return await self.search(**kwargs)
    
    async def parse(self, raw: Any, series_id: str = None) -> AdapterOutput:
        """
        Parse FRED API response into normalized format
        
        Args:
            raw: Raw JSON from FRED API
            series_id: FRED series ID
            
        Returns:
            AdapterOutput with parsed macro series data
        """
        try:
            if not isinstance(raw, dict):
                raise ParseError("Expected JSON object from FRED API")
            
            # Extract series info
            series_info = raw.get("seriess", [{}])[0] if raw.get("seriess") else {}
            observations = raw.get("observations", [])
            
            # Build normalized data points
            data_points = []
            provenance_list = []
            
            for obs in observations:
                if not isinstance(obs, dict):
                    continue
                
                date_str = obs.get("date")
                value_str = obs.get("value")
                
                # Skip missing values
                if value_str == ".":
                    continue
                
                try:
                    value = float(value_str) if value_str else None
                except (ValueError, TypeError):
                    continue
                
                data_point = {
                    "date": date_str,
                    "value": value,
                    "realtime_start": obs.get("realtime_start"),
                    "realtime_end": obs.get("realtime_end")
                }
                data_points.append(data_point)
                
                # Create provenance
                provenance = self._create_provenance(
                    url=f"https://fred.stlouisfed.org/series/{series_id}",
                    period=date_str
                )
                provenance_list.append(provenance)
            
            # Build normalized output
            normalized_data = {
                "series_id": series_id or series_info.get("id", "unknown"),
                "title": series_info.get("title", ""),
                "units": series_info.get("units", ""),
                "frequency": series_info.get("frequency", ""),
                "seasonal_adjustment": series_info.get("seasonal_adjustment", ""),
                "last_updated": series_info.get("last_updated", ""),
                "observation_start": series_info.get("observation_start", ""),
                "observation_end": series_info.get("observation_end", ""),
                "points": data_points,
                "total_observations": len(data_points)
            }
            
            # Metadata
            metadata = {
                "source": "fred",
                "parsed_at": datetime.now().isoformat(),
                "total_observations": len(data_points),
                "series_info": series_info,
                "date_range": {
                    "start": min([p["date"] for p in data_points]) if data_points else None,
                    "end": max([p["date"] for p in data_points]) if data_points else None
                }
            }
            
            return AdapterOutput(
                data=normalized_data,
                provenance=provenance_list,
                source_version=self._get_source_version(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to parse FRED data", error=str(e))
            raise ParseError(f"Failed to parse FRED data: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check FRED API health"""
        try:
            start_time = time.time()
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={"Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            
            # Test with a known series (CPI)
            url = f"{self.base_url}series/observations"
            params = {
                "series_id": "CPIAUCSL",  # Consumer Price Index
                "file_type": "json",
                "limit": 1
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with self.session.get(url, params=params) as response:
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    return {
                        "source_id": self.source_id,
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "source_id": self.source_id,
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "latency_ms": round(latency_ms, 2),
                        "timestamp": time.time()
                    }
                    
        except Exception as e:
            return {
                "source_id": self.source_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

