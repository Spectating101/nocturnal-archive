#!/usr/bin/env python3
"""
Performance Optimization Service
Advanced caching, connection pooling, and system optimization
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis
import motor.motor_asyncio
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    response_time: float
    memory_usage: float
    cpu_usage: float
    cache_hit_rate: float
    active_connections: int
    timestamp: datetime

class ConnectionPool:
    """Advanced connection pooling for databases"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.mongo_pool = None
        self.redis_pool = None
        self.thread_pool = ThreadPoolExecutor(max_workers=20)
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize connection pools"""
        try:
            # MongoDB connection pool
            self.mongo_pool = motor.motor_asyncio.AsyncIOMotorClient(
                "mongodb://localhost:27017",
                maxPoolSize=self.max_connections,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
            
            # Redis connection pool
            self.redis_pool = redis.ConnectionPool(
                host='localhost',
                port=6379,
                db=0,
                max_connections=self.max_connections,
                retry_on_timeout=True
            )
            
            logger.info("Connection pools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
    
    async def get_mongo_client(self):
        """Get MongoDB client from pool"""
        return self.mongo_pool
    
    def get_redis_client(self):
        """Get Redis client from pool"""
        return redis.Redis(connection_pool=self.redis_pool)

class AdvancedCache:
    """Advanced caching system with intelligent invalidation"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
    
    async def get(self, key: str, default=None):
        """Get value from cache with fallback strategy"""
        try:
            # Try local cache first
            if key in self.local_cache:
                self.cache_stats['hits'] += 1
                return self.local_cache[key]
            
            # Try Redis cache
            value = self.redis.get(key)
            if value:
                # Deserialize and cache locally
                import json
                parsed_value = json.loads(value)
                self.local_cache[key] = parsed_value
                self.cache_stats['hits'] += 1
                return parsed_value
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            import json
            
            # Set in local cache
            self.local_cache[key] = value
            
            # Set in Redis with TTL
            self.redis.setex(key, ttl, json.dumps(value))
            self.cache_stats['sets'] += 1
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        return (self.cache_stats['hits'] / total * 100) if total > 0 else 0

class QueryOptimizer:
    """Database query optimization"""
    
    def __init__(self, mongo_client, cache: AdvancedCache):
        self.mongo = mongo_client
        self.cache = cache
    
    async def optimized_search(self, collection: str, query: Dict, projection: Dict = None, limit: int = 50):
        """Optimized database search with caching"""
        try:
            # Generate cache key
            cache_key = f"search:{collection}:{hash(str(query))}:{limit}"
            
            # Try cache first
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute optimized query
            start_time = time.time()
            
            db = self.mongo.get_database("nocturnal_archive")
            coll = db[collection]
            
            # Build query with optimization
            cursor = coll.find(query, projection)
            if limit:
                cursor = cursor.limit(limit)
            
            # Use hint for better performance if index exists
            try:
                cursor = cursor.hint([("_id", 1)])
            except:
                pass  # Index might not exist
            
            results = await cursor.to_list(length=limit)
            
            # Cache results for 5 minutes
            await self.cache.set(cache_key, results, ttl=300)
            
            query_time = time.time() - start_time
            logger.info(f"Query executed in {query_time:.3f}s, cached for future use")
            
            return results
            
        except Exception as e:
            logger.error(f"Optimized search failed: {e}")
            return []

class SystemMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 100
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system metrics"""
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get process metrics
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            # Get network connections
            connections = len(psutil.net_connections())
            
            metrics = PerformanceMetrics(
                response_time=0.0,  # Will be set by caller
                memory_usage=memory_usage,
                cpu_usage=cpu_percent,
                cache_hit_rate=0.0,  # Will be set by caller
                active_connections=connections,
                timestamp=datetime.now()
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return PerformanceMetrics(0, 0, 0, 0, 0, datetime.now())
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        return {
            "avg_memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            "avg_cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            "avg_connections": sum(m.active_connections for m in recent_metrics) / len(recent_metrics),
            "total_measurements": len(self.metrics_history),
            "last_updated": recent_metrics[-1].timestamp.isoformat()
        }

class PerformanceOptimizer:
    """Main performance optimization service"""
    
    def __init__(self):
        self.connection_pool = ConnectionPool()
        self.cache = AdvancedCache(self.connection_pool.get_redis_client())
        self.query_optimizer = QueryOptimizer(
            self.connection_pool.get_mongo_client(),
            self.cache
        )
        self.monitor = SystemMonitor()
        self.optimization_running = False
    
    async def start_optimization(self):
        """Start background optimization tasks"""
        if self.optimization_running:
            return
        
        self.optimization_running = True
        logger.info("Starting performance optimization tasks")
        
        # Start background tasks
        asyncio.create_task(self._cache_cleanup_task())
        asyncio.create_task(self._memory_optimization_task())
        asyncio.create_task(self._connection_health_check())
    
    async def _cache_cleanup_task(self):
        """Periodic cache cleanup"""
        while self.optimization_running:
            try:
                # Clean up local cache (remove old entries)
                if len(self.cache.local_cache) > 1000:
                    # Keep only recent 500 entries
                    items = list(self.cache.local_cache.items())
                    self.cache.local_cache = dict(items[-500:])
                
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _memory_optimization_task(self):
        """Periodic memory optimization"""
        while self.optimization_running:
            try:
                # Force garbage collection
                gc.collect()
                
                # Log memory usage
                metrics = self.monitor.get_current_metrics()
                if metrics.memory_usage > 500:  # More than 500MB
                    logger.warning(f"High memory usage: {metrics.memory_usage:.1f}MB")
                
                await asyncio.sleep(180)  # 3 minutes
            except Exception as e:
                logger.error(f"Memory optimization error: {e}")
                await asyncio.sleep(60)
    
    async def _connection_health_check(self):
        """Periodic connection health check"""
        while self.optimization_running:
            try:
                # Test MongoDB connection
                mongo_client = await self.connection_pool.get_mongo_client()
                await mongo_client.admin.command('ping')
                
                # Test Redis connection
                redis_client = self.connection_pool.get_redis_client()
                redis_client.ping()
                
                logger.debug("Connection health check passed")
                await asyncio.sleep(60)  # 1 minute
            except Exception as e:
                logger.error(f"Connection health check failed: {e}")
                await asyncio.sleep(30)
    
    async def optimize_query(self, collection: str, query: Dict, **kwargs):
        """Optimize and execute database query"""
        start_time = time.time()
        
        try:
            result = await self.query_optimizer.optimized_search(collection, query, **kwargs)
            
            # Update metrics
            response_time = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            metrics.response_time = response_time
            metrics.cache_hit_rate = self.cache.get_hit_rate()
            
            return result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            raise
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "system_metrics": self.monitor.get_performance_summary(),
            "cache_stats": {
                "hit_rate": self.cache.get_hit_rate(),
                "local_cache_size": len(self.cache.local_cache),
                "stats": self.cache.cache_stats
            },
            "connection_pool": {
                "max_connections": self.connection_pool.max_connections,
                "thread_pool_workers": self.connection_pool.thread_pool._max_workers
            },
            "optimization_status": {
                "running": self.optimization_running,
                "last_cleanup": datetime.now().isoformat()
            }
        }
    
    async def stop_optimization(self):
        """Stop optimization tasks"""
        self.optimization_running = False
        logger.info("Performance optimization stopped")

# Global instance
performance_optimizer = PerformanceOptimizer()
