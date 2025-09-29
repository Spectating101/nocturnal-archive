"""
Base adapter interface for FinSight data sources
"""

from typing import Any, Dict, List, Optional, TypedDict
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)

class Provenance(TypedDict):
    """Provenance information for data points"""
    source_id: str
    url: str
    accession: Optional[str]
    fragment_id: Optional[str]
    period: Optional[str]
    unit: Optional[str]
    page_hint: Optional[int]
    concept: Optional[str]
    dimension: Optional[Dict[str, str]]

class AdapterOutput(TypedDict):
    """Standard output format for all adapters"""
    data: Any
    provenance: List[Provenance]
    source_version: str
    metadata: Dict[str, Any]

class SourceAdapter(ABC):
    """Abstract base class for all data source adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with source configuration
        
        Args:
            config: Source configuration from sources.yaml
        """
        self.config = config
        self.source_id = config["id"]
        self.jurisdiction = config["jurisdiction"]
        self.authority = config["authority"]
        self.status = config["status"]
        self.base_url = config["base_url"]
        self.endpoints = config["endpoints"]
        self.auth = config.get("auth", "none")
        self.etiquette = config.get("etiquette", {})
        
        logger.info(
            "Initialized source adapter",
            source_id=self.source_id,
            jurisdiction=self.jurisdiction,
            authority=self.authority,
            status=self.status
        )
    
    @abstractmethod
    async def search(self, **kwargs) -> AdapterOutput:
        """
        Search for data using source-specific parameters
        
        Returns:
            AdapterOutput with search results and provenance
        """
        pass
    
    @abstractmethod
    async def fetch(self, **kwargs) -> AdapterOutput:
        """
        Fetch specific data by identifier
        
        Returns:
            AdapterOutput with fetched data and provenance
        """
        pass
    
    @abstractmethod
    async def parse(self, raw: Any) -> AdapterOutput:
        """
        Parse raw data into normalized format
        
        Args:
            raw: Raw data from source
            
        Returns:
            AdapterOutput with parsed data and provenance
        """
        pass
    
    def _create_provenance(
        self,
        url: str,
        accession: Optional[str] = None,
        fragment_id: Optional[str] = None,
        period: Optional[str] = None,
        unit: Optional[str] = None,
        page_hint: Optional[int] = None,
        concept: Optional[str] = None,
        dimension: Optional[Dict[str, str]] = None
    ) -> Provenance:
        """Create provenance object for a data point"""
        return Provenance(
            source_id=self.source_id,
            url=url,
            accession=accession,
            fragment_id=fragment_id,
            period=period,
            unit=unit,
            page_hint=page_hint,
            concept=concept,
            dimension=dimension
        )
    
    def _get_source_version(self) -> str:
        """Get source version for cache invalidation"""
        # Simple version based on source config hash
        import hashlib
        config_str = str(sorted(self.config.items()))
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def _apply_etiquette(self, url: str) -> str:
        """Apply source-specific etiquette rules"""
        # Add User-Agent if required
        if self.etiquette.get("user_agent_required"):
            # This would be handled by the HTTP client
            pass
        
        return url
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if source is healthy and accessible
        
        Returns:
            Health status with latency and error info
        """
        try:
            import time
            start_time = time.time()
            
            # Simple ping to base URL or health endpoint
            # This would be implemented by each adapter
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "source_id": self.source_id,
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(
                "Health check failed",
                source_id=self.source_id,
                error=str(e)
            )
            return {
                "source_id": self.source_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

class AdapterError(Exception):
    """Base exception for adapter errors"""
    pass

class SourceUnavailableError(AdapterError):
    """Source is temporarily unavailable"""
    pass

class AuthenticationError(AdapterError):
    """Authentication failed"""
    pass

class RateLimitError(AdapterError):
    """Rate limit exceeded"""
    pass

class DataNotFoundError(AdapterError):
    """Requested data not found"""
    pass

class ParseError(AdapterError):
    """Failed to parse source data"""
    pass

