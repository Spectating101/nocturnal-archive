"""
Resiliency utilities: Redis caching and circuit breaker
"""

import time
import json
import hashlib
from functools import wraps
from typing import Callable, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

# Redis connection (will be initialized when Redis is available)
redis_client = None

def init_redis(redis_url: str = "redis://localhost:6379/0"):
    """Initialize Redis connection"""
    global redis_client
    try:
        import redis
        redis_client = redis.from_url(redis_url)
        redis_client.ping()  # Test connection
        logger.info("Redis connection established", url=redis_url)
    except Exception as e:
        logger.warning("Redis not available, caching disabled", error=str(e))
        redis_client = None

def _get_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments"""
    key_data = {
        "func": func_name,
        "args": args,
        "kwargs": sorted(kwargs.items()) if kwargs else {}
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return f"cache:{func_name}:{hashlib.md5(key_str.encode()).hexdigest()}"

def cache(ttl: int = 600, source_version: str = "v1"):
    """
    Redis cache decorator
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client is None:
                # Redis not available, skip caching
                return func(*args, **kwargs)
            
            try:
                cache_key = _get_cache_key(f"{source_version}:{func.__name__}", args, kwargs)
                cached_value = redis_client.get(cache_key)
                
                if cached_value:
                    logger.debug("Cache hit", key=cache_key, func=func.__name__)
                    return json.loads(cached_value)
                
                # Cache miss, execute function
                result = func(*args, **kwargs)
                
                # Do not cache provider failures or empty payloads
                if result is None:
                    return result
                if isinstance(result, (list, dict)) and len(result) == 0:
                    return result
                # Store in cache
                redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug("Cache miss, stored", key=cache_key, func=func.__name__)
                
                return result
                
            except Exception as e:
                logger.warning("Cache error, falling back to function", error=str(e), func=func.__name__)
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def circuit_breaker(name: str, fail_threshold: int = 5, reset_seconds: int = 60):
    """
    Circuit breaker decorator
    
    Args:
        name: Circuit breaker name
        fail_threshold: Number of failures before opening circuit
        reset_seconds: Seconds to wait before trying again
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client is None:
                # Redis not available, skip circuit breaker
                return func(*args, **kwargs)
            
            try:
                cb_key = f"cb:{name}"
                cb_state = redis_client.get(cb_key)
                
                if cb_state:
                    state = json.loads(cb_state)
                    now = time.time()
                    
                    if state.get("until", 0) > now:
                        # Circuit is open
                        logger.warning("Circuit breaker open", name=name, until=state["until"])
                        raise RuntimeError(f"Circuit breaker '{name}' is open")
                else:
                    state = {"fails": 0, "until": 0}
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Success - reset failure count
                if state["fails"] > 0:
                    state["fails"] = 0
                    state["until"] = 0
                    redis_client.set(cb_key, json.dumps(state))
                    logger.info("Circuit breaker reset", name=name)
                
                return result
                
            except Exception as e:
                if redis_client is None:
                    raise
                
                # Failure - increment counter
                try:
                    cb_key = f"cb:{name}"
                    cb_state = redis_client.get(cb_key)
                    
                    if cb_state:
                        state = json.loads(cb_state)
                    else:
                        state = {"fails": 0, "until": 0}
                    
                    state["fails"] += 1
                    
                    if state["fails"] >= fail_threshold:
                        state["until"] = time.time() + reset_seconds
                        state["fails"] = 0  # Reset counter when opening circuit
                        logger.warning("Circuit breaker opened", name=name, threshold=fail_threshold, reset_seconds=reset_seconds)
                    
                    redis_client.set(cb_key, json.dumps(state))
                    
                except Exception as cb_error:
                    logger.error("Circuit breaker error", name=name, error=str(cb_error))
                
                raise
        
        return wrapper
    return decorator

def degraded_response(message: str = "Service temporarily unavailable", details: dict = None) -> dict:
    """Return a degraded response when services are down"""
    return {
        "degraded": True,
        "message": message,
        "details": details or {},
        "timestamp": time.time()
    }
