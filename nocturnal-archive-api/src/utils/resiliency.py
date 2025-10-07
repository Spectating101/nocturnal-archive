"""
Resiliency utilities: Redis caching and circuit breaker
"""

import time
import json
import hashlib
from functools import wraps
from typing import Callable, Optional, Protocol, runtime_checkable
import structlog

logger = structlog.get_logger(__name__)

# Redis connection (will be initialized when Redis is available)
redis_client = None

# Optional metrics recorder (duck-typed to avoid hard dependency)
metrics_recorder = None


@runtime_checkable
class MetricsRecorder(Protocol):
    """Interface for recording resiliency telemetry without imposing dependencies."""

    def increment(self, name: str, value: int = 1, tags: Optional[dict] = None) -> None: ...

    def observe(self, name: str, value: float, tags: Optional[dict] = None) -> None: ...


def set_metrics_recorder(recorder: Optional[MetricsRecorder]) -> None:
    """Register a metrics recorder implementation (e.g., Prometheus, StatsD)."""

    global metrics_recorder
    metrics_recorder = recorder


def _increment(metric: str, *, value: int = 1, tags: Optional[dict] = None) -> None:
    if metrics_recorder is None:
        return
    try:
        metrics_recorder.increment(metric, value=value, tags=tags)
    except Exception as exc:
        logger.warning("metrics_increment_failed", metric=metric, error=str(exc))


def _observe(metric: str, value: float, *, tags: Optional[dict] = None) -> None:
    if metrics_recorder is None:
        return
    try:
        metrics_recorder.observe(metric, value, tags=tags)
    except Exception as exc:
        logger.warning("metrics_observe_failed", metric=metric, error=str(exc))

def init_redis(redis_url: str = "redis://localhost:6379/0"):
    """Initialize Redis connection"""
    global redis_client
    try:
        import redis
        redis_client = redis.from_url(redis_url)
        redis_client.ping()  # Test connection
        logger.info("redis_connection_established", log_event="redis_connection_established", url=redis_url)
        _increment("resiliency.redis.connected", tags={"url": redis_url})
    except Exception as e:
        logger.warning("redis_unavailable", log_event="redis_unavailable", error=str(e), url=redis_url)
        _increment("resiliency.redis.unavailable", tags={"url": redis_url})
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
            start = time.perf_counter()
            metric_tags = {"func": func.__name__, "version": source_version}

            if redis_client is None:
                # Redis not available, skip caching
                _increment("resiliency.cache.bypass", tags=metric_tags)
                result = func(*args, **kwargs)
                _observe("resiliency.cache.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "source": "bypass"})
                return result

            try:
                cache_key = _get_cache_key(f"{source_version}:{func.__name__}", args, kwargs)
                cached_value = redis_client.get(cache_key)
                
                if cached_value:
                    logger.debug("cache_hit", log_event="cache_hit", key=cache_key, func=func.__name__)
                    _increment("resiliency.cache.hit", tags=metric_tags)
                    _observe("resiliency.cache.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "source": "hit"})
                    return json.loads(cached_value)
                
                # Cache miss, execute function
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                
                # Do not cache provider failures or empty payloads
                if result is None:
                    logger.debug("cache_skip_none", log_event="cache_skip", key=cache_key, func=func.__name__)
                    _increment("resiliency.cache.skip", tags={**metric_tags, "reason": "none"})
                    _observe("resiliency.cache.latency_seconds", duration, tags={**metric_tags, "source": "skip"})
                    return result
                if isinstance(result, (list, dict)) and len(result) == 0:
                    logger.debug("cache_skip_empty", log_event="cache_skip", key=cache_key, func=func.__name__)
                    _increment("resiliency.cache.skip", tags={**metric_tags, "reason": "empty"})
                    _observe("resiliency.cache.latency_seconds", duration, tags={**metric_tags, "source": "skip"})
                    return result
                # Store in cache
                redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug("cache_miss_stored", log_event="cache_miss", key=cache_key, func=func.__name__, ttl=ttl)
                _increment("resiliency.cache.miss", tags=metric_tags)
                _observe("resiliency.cache.latency_seconds", duration, tags={**metric_tags, "source": "miss"})
                
                return result
                
            except Exception as e:
                logger.warning("cache_fallback", log_event="cache_error", error=str(e), func=func.__name__)
                _increment("resiliency.cache.error", tags=metric_tags)
                result = func(*args, **kwargs)
                _observe("resiliency.cache.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "source": "error"})
                return result
        
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
            metric_tags = {"circuit": name, "func": func.__name__}
            start = time.perf_counter()

            if redis_client is None:
                # Redis not available, skip circuit breaker safeguards
                _increment("resiliency.circuit.bypass", tags=metric_tags)
                result = func(*args, **kwargs)
                _observe("resiliency.circuit.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "state": "bypass"})
                return result
            
            try:
                cb_key = f"cb:{name}"
                cb_state = redis_client.get(cb_key)
                
                if cb_state:
                    state = json.loads(cb_state)
                    now = time.time()
                    
                    if state.get("until", 0) > now:
                        # Circuit is open
                        logger.warning("circuit_open_block", log_event="circuit_open_block", name=name, until=state["until"])
                        _increment("resiliency.circuit.open_block", tags=metric_tags)
                        _observe("resiliency.circuit.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "state": "open_block"})
                        raise RuntimeError(f"Circuit breaker '{name}' is open")
                else:
                    state = {"fails": 0, "until": 0}
                
                # Execute function
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                
                # Success - reset failure count
                if state["fails"] > 0:
                    state["fails"] = 0
                    state["until"] = 0
                    redis_client.set(cb_key, json.dumps(state))
                    logger.info("circuit_reset", log_event="circuit_reset", name=name)
                _increment("resiliency.circuit.success", tags=metric_tags)
                _observe("resiliency.circuit.latency_seconds", duration, tags={**metric_tags, "state": "success"})
                
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
                    is_open_error = isinstance(e, RuntimeError) and str(e).startswith("Circuit breaker")
                    if not is_open_error:
                        logger.warning("circuit_failure", log_event="circuit_failure", name=name, error=str(e))
                        _increment("resiliency.circuit.failure", tags=metric_tags)
                        _observe("resiliency.circuit.latency_seconds", time.perf_counter() - start, tags={**metric_tags, "state": "failure"})
                    
                    if state["fails"] >= fail_threshold:
                        state["until"] = time.time() + reset_seconds
                        state["fails"] = 0  # Reset counter when opening circuit
                        logger.warning("circuit_opened", log_event="circuit_open", name=name, threshold=fail_threshold, reset_seconds=reset_seconds)
                        _increment("resiliency.circuit.open", tags=metric_tags)
                    
                    redis_client.set(cb_key, json.dumps(state))
                    
                except Exception as cb_error:
                    logger.error("Circuit breaker error", name=name, error=str(cb_error))
                
                raise
        
        return wrapper
    return decorator

def degraded_response(message: str = "Service temporarily unavailable", details: dict = None) -> dict:
    """Return a degraded response when services are down"""
    details = details or {}
    timestamp = time.time()
    payload = {
        "degraded": True,
        "message": message,
        "details": details,
        "timestamp": timestamp
    }
    logger.warning("degraded_response", log_event="degraded_response", message=message, details=details, timestamp=timestamp)
    _increment("resiliency.degraded.count", tags={"message": message})
    return payload
