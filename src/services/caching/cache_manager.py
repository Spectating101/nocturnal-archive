import asyncio
import json
import hashlib
import logging
from typing import Any, Dict, Optional, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Comprehensive caching system with Redis for performance optimization.
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            value = await self.redis_client.get(key)
            if value is not None:
                self.cache_stats["hits"] += 1
                return json.loads(value)
            else:
                self.cache_stats["misses"] += 1
                return default
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            result = await self.redis_client.setex(key, ttl, serialized)
            self.cache_stats["sets"] += 1
            return result
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.redis_client.delete(key)
            self.cache_stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key."""
        try:
            return bool(await self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            values = await self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = json.loads(value)
                    self.cache_stats["hits"] += 1
                else:
                    self.cache_stats["misses"] += 1
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            ttl = ttl or self.default_ttl
            pipeline = self.redis_client.pipeline()
            
            for key, value in data.items():
                serialized = json.dumps(value, default=str)
                pipeline.setex(key, ttl, serialized)
            
            await pipeline.execute()
            self.cache_stats["sets"] += len(data)
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.cache_stats["deletes"] += deleted
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate_pattern error for {pattern}: {e}")
            return 0
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        
        return key_string
    
    async def cache_function(self, prefix: str, ttl: Optional[int] = None, key_func=None):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    async def cache_research_results(self, session_id: str, query: str, results: List[Dict], ttl: int = 3600):
        """Cache research results for a session."""
        key = self.generate_key("research_results", session_id=session_id, query=query)
        await self.set(key, {
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "session_id": session_id
        }, ttl)
    
    async def get_cached_research_results(self, session_id: str, query: str) -> Optional[List[Dict]]:
        """Get cached research results for a session."""
        key = self.generate_key("research_results", session_id=session_id, query=query)
        cached = await self.get(key)
        if cached:
            return cached.get("results")
        return None
    
    async def cache_synthesis(self, paper_ids: List[str], synthesis: Dict, ttl: int = 7200):
        """Cache synthesis results."""
        key = self.generate_key("synthesis", paper_ids=",".join(sorted(paper_ids)))
        await self.set(key, {
            "synthesis": synthesis,
            "timestamp": datetime.utcnow().isoformat(),
            "paper_ids": paper_ids
        }, ttl)
    
    async def get_cached_synthesis(self, paper_ids: List[str]) -> Optional[Dict]:
        """Get cached synthesis results."""
        key = self.generate_key("synthesis", paper_ids=",".join(sorted(paper_ids)))
        cached = await self.get(key)
        if cached:
            return cached.get("synthesis")
        return None
    
    async def cache_embeddings(self, text: str, embeddings: List[float], ttl: int = 86400):
        """Cache text embeddings."""
        key = self.generate_key("embeddings", text_hash=hashlib.md5(text.encode()).hexdigest())
        await self.set(key, {
            "embeddings": embeddings,
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(text)
        }, ttl)
    
    async def get_cached_embeddings(self, text: str) -> Optional[List[float]]:
        """Get cached embeddings for text."""
        key = self.generate_key("embeddings", text_hash=hashlib.md5(text.encode()).hexdigest())
        cached = await self.get(key)
        if cached:
            return cached.get("embeddings")
        return None
    
    async def cache_user_sessions(self, user_id: str, sessions: List[Dict], ttl: int = 1800):
        """Cache user sessions."""
        key = self.generate_key("user_sessions", user_id=user_id)
        await self.set(key, {
            "sessions": sessions,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }, ttl)
    
    async def get_cached_user_sessions(self, user_id: str) -> Optional[List[Dict]]:
        """Get cached user sessions."""
        key = self.generate_key("user_sessions", user_id=user_id)
        cached = await self.get(key)
        if cached:
            return cached.get("sessions")
        return None
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user."""
        patterns = [
            f"user_sessions:user_id:{user_id}",
            f"research_results:session_id:*",
            f"synthesis:*"
        ]
        
        for pattern in patterns:
            await self.invalidate_pattern(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = await self.redis_client.info()
            return {
                "cache_stats": self.cache_stats,
                "redis_info": {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_peak": info.get("used_memory_peak", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                },
                "hit_rate": self.cache_stats["hits"] / max(1, self.cache_stats["hits"] + self.cache_stats["misses"])
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"cache_stats": self.cache_stats, "error": str(e)}
    
    async def clear_all(self) -> bool:
        """Clear all cache entries."""
        try:
            await self.redis_client.flushdb()
            self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache system."""
        try:
            await self.redis_client.ping()
            stats = await self.get_cache_stats()
            return {
                "status": "healthy",
                "cache_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close Redis connection."""
        try:
            await self.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing cache connection: {e}")
