"""
Identifier resolution service
Maps between different financial identifiers (ticker, ISIN, CIK, FIGI)
"""

import asyncio
import aiohttp
import structlog
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

logger = structlog.get_logger(__name__)

@dataclass
class IdentifierMapping:
    """Represents a mapping between different identifiers"""
    ticker: Optional[str] = None
    cik: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    figi: Optional[str] = None
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None

class IdentifierResolver:
    """Service for resolving financial identifiers"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cik_cache: Dict[str, IdentifierMapping] = {}
        self.ticker_cache: Dict[str, IdentifierMapping] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Accept": "application/json",
                "User-Agent": "Nocturnal Archive Research Tool (contact@nocturnal.dev)"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def resolve_ticker(self, ticker: str) -> Optional[IdentifierMapping]:
        """
        Resolve ticker symbol to other identifiers
        
        Args:
            ticker: Ticker symbol (e.g., "AAPL")
            
        Returns:
            IdentifierMapping with all available identifiers
        """
        if not self.session:
            raise RuntimeError("IdentifierResolver must be used as async context manager")
        
        ticker = ticker.upper()
        
        # Check cache first
        if ticker in self.ticker_cache:
            return self.ticker_cache[ticker]
        
        try:
            logger.info("Resolving ticker", ticker=ticker)
            
            # Try SEC ticker mapping first
            mapping = await self._resolve_sec_ticker(ticker)
            if mapping:
                self.ticker_cache[ticker] = mapping
                return mapping
            
            # Try OpenFIGI as fallback
            mapping = await self._resolve_openfigi_ticker(ticker)
            if mapping:
                self.ticker_cache[ticker] = mapping
                return mapping
            
            logger.warning("Could not resolve ticker", ticker=ticker)
            return None
            
        except Exception as e:
            logger.error("Ticker resolution failed", ticker=ticker, error=str(e))
            return None
    
    async def resolve_cik(self, cik: str) -> Optional[IdentifierMapping]:
        """
        Resolve CIK to other identifiers
        
        Args:
            cik: Company CIK number
            
        Returns:
            IdentifierMapping with all available identifiers
        """
        if not self.session:
            raise RuntimeError("IdentifierResolver must be used as async context manager")
        
        cik = str(cik).zfill(10)  # Pad to 10 digits
        
        # Check cache first
        if cik in self.cik_cache:
            return self.cik_cache[cik]
        
        try:
            logger.info("Resolving CIK", cik=cik)
            
            # Try SEC ticker mapping first
            mapping = await self._resolve_sec_cik(cik)
            if mapping:
                self.cik_cache[cik] = mapping
                return mapping
            
            logger.warning("Could not resolve CIK", cik=cik)
            return None
            
        except Exception as e:
            logger.error("CIK resolution failed", cik=cik, error=str(e))
            return None
    
    async def resolve_isin(self, isin: str) -> Optional[IdentifierMapping]:
        """
        Resolve ISIN to other identifiers
        
        Args:
            isin: ISIN identifier
            
        Returns:
            IdentifierMapping with all available identifiers
        """
        if not self.session:
            raise RuntimeError("IdentifierResolver must be used as async context manager")
        
        try:
            logger.info("Resolving ISIN", isin=isin)
            
            # Use OpenFIGI for ISIN resolution
            mapping = await self._resolve_openfigi_isin(isin)
            if mapping:
                return mapping
            
            logger.warning("Could not resolve ISIN", isin=isin)
            return None
            
        except Exception as e:
            logger.error("ISIN resolution failed", isin=isin, error=str(e))
            return None
    
    async def _resolve_sec_ticker(self, ticker: str) -> Optional[IdentifierMapping]:
        """Resolve ticker using SEC ticker mapping"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
            
            # Search for ticker in SEC data
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    cik = str(entry.get("cik_str", "")).zfill(10)
                    company_name = entry.get("title", "")
                    
                    mapping = IdentifierMapping(
                        ticker=ticker.upper(),
                        cik=cik,
                        company_name=company_name
                    )
                    
                    logger.info("Resolved via SEC", ticker=ticker, cik=cik, company=company_name)
                    return mapping
            
            return None
            
        except Exception as e:
            logger.error("SEC ticker resolution failed", ticker=ticker, error=str(e))
            return None
    
    async def _resolve_sec_cik(self, cik: str) -> Optional[IdentifierMapping]:
        """Resolve CIK using SEC ticker mapping"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
            
            # Search for CIK in SEC data
            for entry in data.values():
                entry_cik = str(entry.get("cik_str", "")).zfill(10)
                if entry_cik == cik:
                    ticker = entry.get("ticker", "")
                    company_name = entry.get("title", "")
                    
                    mapping = IdentifierMapping(
                        ticker=ticker.upper() if ticker else None,
                        cik=cik,
                        company_name=company_name
                    )
                    
                    logger.info("Resolved via SEC", cik=cik, ticker=ticker, company=company_name)
                    return mapping
            
            return None
            
        except Exception as e:
            logger.error("SEC CIK resolution failed", cik=cik, error=str(e))
            return None
    
    async def _resolve_openfigi_ticker(self, ticker: str) -> Optional[IdentifierMapping]:
        """Resolve ticker using OpenFIGI API"""
        try:
            url = "https://api.openfigi.com/v3/mapping"
            
            payload = [{
                "idType": "TICKER",
                "idValue": ticker
            }]
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
            
            if not data or not data[0].get("data"):
                return None
            
            # Get first result
            result = data[0]["data"][0]
            
            mapping = IdentifierMapping(
                ticker=ticker.upper(),
                figi=result.get("figi"),
                isin=result.get("isin"),
                cusip=result.get("cusip"),
                company_name=result.get("name"),
                exchange=result.get("exchCode"),
                country=result.get("countryCode")
            )
            
            logger.info("Resolved via OpenFIGI", ticker=ticker, figi=result.get("figi"))
            return mapping
            
        except Exception as e:
            logger.error("OpenFIGI ticker resolution failed", ticker=ticker, error=str(e))
            return None
    
    async def _resolve_openfigi_isin(self, isin: str) -> Optional[IdentifierMapping]:
        """Resolve ISIN using OpenFIGI API"""
        try:
            url = "https://api.openfigi.com/v3/mapping"
            
            payload = [{
                "idType": "ID_ISIN",
                "idValue": isin
            }]
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
            
            if not data or not data[0].get("data"):
                return None
            
            # Get first result
            result = data[0]["data"][0]
            
            mapping = IdentifierMapping(
                isin=isin,
                figi=result.get("figi"),
                ticker=result.get("ticker"),
                cusip=result.get("cusip"),
                company_name=result.get("name"),
                exchange=result.get("exchCode"),
                country=result.get("countryCode")
            )
            
            logger.info("Resolved via OpenFIGI", isin=isin, figi=result.get("figi"))
            return mapping
            
        except Exception as e:
            logger.error("OpenFIGI ISIN resolution failed", isin=isin, error=str(e))
            return None
    
    def get_cached_mapping(self, identifier: str, id_type: str = "ticker") -> Optional[IdentifierMapping]:
        """Get cached mapping without API call"""
        if id_type == "ticker":
            return self.ticker_cache.get(identifier.upper())
        elif id_type == "cik":
            cik = str(identifier).zfill(10)
            return self.cik_cache.get(cik)
        else:
            return None
    
    def clear_cache(self):
        """Clear all cached mappings"""
        self.ticker_cache.clear()
        self.cik_cache.clear()
        logger.info("Identifier cache cleared")

# Convenience functions
async def resolve_ticker(ticker: str) -> Optional[IdentifierMapping]:
    """Resolve ticker symbol to other identifiers"""
    async with IdentifierResolver() as resolver:
        return await resolver.resolve_ticker(ticker)

async def resolve_cik(cik: str) -> Optional[IdentifierMapping]:
    """Resolve CIK to other identifiers"""
    async with IdentifierResolver() as resolver:
        return await resolver.resolve_cik(cik)

async def resolve_isin(isin: str) -> Optional[IdentifierMapping]:
    """Resolve ISIN to other identifiers"""
    async with IdentifierResolver() as resolver:
        return await resolver.resolve_isin(isin)

