"""
Redis fallback middleware for degraded mode operation
"""

import structlog
from typing import Optional, Any
import asyncio

logger = structlog.get_logger(__name__)

class RedisPipeline:
    """Pipeline-like object for batch operations"""
    
    def __init__(self, redis_fallback):
        self.redis_fallback = redis_fallback
        self.operations = []
    
    def incr(self, key: str):
        """Add increment operation to pipeline"""
        self.operations.append(('incr', key, 1))
        return self
    
    def incrby(self, key: str, value: int):
        """Add increment operation to pipeline"""
        self.operations.append(('incrby', key, value))
        return self
    
    def expire(self, key: str, ttl: int):
        """Add expire operation to pipeline"""
        self.operations.append(('expire', key, ttl))
        return self
    
    async def execute(self):
        """Execute all operations in pipeline"""
        results = []
        for op_type, key, value in self.operations:
            if op_type == 'incr':
                result = await self.redis_fallback.incrby(key, value)
                results.append(result)
            elif op_type == 'incrby':
                result = await self.redis_fallback.incrby(key, value)
                results.append(result)
            elif op_type == 'expire':
                result = await self.redis_fallback.expire(key, value)
                results.append(result)
        self.operations = []
        return results

class RedisFallback:
    """Fallback Redis client for when Redis is unavailable"""
    
    def __init__(self):
        self.memory_store = {}
        self.rate_limits = {}
        self.token_usage = {}
        logger.warning("Redis fallback mode enabled - using in-memory storage")
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value from memory store"""
        return self.memory_store.get(key)
    
    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        """Set value in memory store with TTL simulation"""
        self.memory_store[key] = value
        # Schedule cleanup after TTL (simplified)
        asyncio.create_task(self._cleanup_after_ttl(key, ttl))
        return True
    
    async def incrby(self, key: str, value: int) -> int:
        """Increment value in memory store"""
        current = int(self.memory_store.get(key, 0))
        new_value = current + value
        self.memory_store[key] = str(new_value)
        return new_value
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        asyncio.create_task(self._cleanup_after_ttl(key, ttl))
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory store"""
        if key in self.memory_store:
            del self.memory_store[key]
            return True
        return False
    
    async def scan_iter(self, match: str):
        """Scan keys matching pattern"""
        for key in self.memory_store.keys():
            if match.replace("*", "") in key:
                yield key
    
    def pipeline(self):
        """Return a pipeline-like object for batch operations"""
        return RedisPipeline(self)
    
    async def _cleanup_after_ttl(self, key: str, ttl: int):
        """Cleanup key after TTL"""
        await asyncio.sleep(ttl)
        if key in self.memory_store:
            del self.memory_store[key]
    
    async def close(self):
        """Close the fallback client (no-op for in-memory)"""
        pass

async def get_redis_client():
    """Get Redis client with fallback"""
    try:
        import redis.asyncio as redis
        client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        await client.ping()
        logger.info("Redis connection established")
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable, using fallback: {e}")
        return RedisFallback()
