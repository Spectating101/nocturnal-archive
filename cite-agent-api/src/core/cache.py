"""
Lightweight TTL cache for FinGPT sentiment results
"""
import time
from typing import Any, Dict, Tuple


class TTLCache:
    """Simple TTL cache implementation for sentiment results"""
    
    def __init__(self, ttl_seconds: int = 900):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        """Get value from cache if not expired"""
        v = self._store.get(key)
        if not v:
            return None
        ts, val = v
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp"""
        self._store[key] = (time.time(), value)

    def clear(self) -> None:
        """Clear all cached values"""
        self._store.clear()

    def size(self) -> int:
        """Get number of cached items"""
        return len(self._store)


# Global cache instance
cache = TTLCache()
