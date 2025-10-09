"""
Production-ready rate limiting middleware with Redis backend
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
import structlog
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis

logger = structlog.get_logger(__name__)

class RateLimiter:
    """Production-ready rate limiter with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Rate limit configurations
        self.limits = {
            "search": {"requests": 30, "window": 60},      # 30 requests per minute
            "synthesize": {"requests": 10, "window": 60},  # 10 requests per minute
            "finance": {"requests": 60, "window": 60},     # 60 requests per minute
            "agent": {"requests": 20, "window": 60},       # 20 requests per minute
            "default": {"requests": 100, "window": 60}     # 100 requests per minute
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from auth first
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('user_id', 'anonymous')}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path
        
        if "/search" in path:
            return "search"
        elif "/synthesize" in path:
            return "synthesize"
        elif "/finance" in path:
            return "finance"
        elif "/agent" in path:
            return "agent"
        else:
            return "default"
    
    async def _get_rate_limit_key(self, client_id: str, endpoint_type: str) -> str:
        """Generate Redis key for rate limiting"""
        window = self.limits[endpoint_type]["window"]
        current_window = int(time.time() // window)
        return f"rate_limit:{endpoint_type}:{client_id}:{current_window}"
    
    async def _check_rate_limit(self, client_id: str, endpoint_type: str) -> Tuple[bool, Dict[str, int]]:
        """Check if client is within rate limits"""
        key = await self._get_rate_limit_key(client_id, endpoint_type)
        limit_config = self.limits[endpoint_type]
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, limit_config["window"])
        results = await pipe.execute()
        
        current_count = results[0]
        max_requests = limit_config["requests"]
        
        # Calculate remaining requests
        remaining = max(0, max_requests - current_count)
        reset_time = int(time.time() // limit_config["window"]) * limit_config["window"] + limit_config["window"]
        
        rate_limit_info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "window": limit_config["window"]
        }
        
        # Check if limit exceeded
        if current_count > max_requests:
            return False, rate_limit_info
        
        return True, rate_limit_info
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit for a request"""
        client_id = self._get_client_id(request)
        endpoint_type = self._get_endpoint_type(request)
        
        return await self._check_rate_limit(client_id, endpoint_type)
    
    async def get_rate_limit_headers(self, rate_limit_info: Dict[str, int]) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info["limit"]),
            "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_info["reset"]),
            "X-RateLimit-Window": str(rate_limit_info["window"])
        }
        # Add Retry-After if exhausted
        if rate_limit_info.get("remaining", 0) == 0:
            retry_after = max(0, int(rate_limit_info["reset"] - int(time.time())))
            headers["Retry-After"] = str(retry_after)
        return headers

# Global rate limiter instance
rate_limiter = None

async def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        from src.middleware.redis_fallback import get_redis_client
        redis_client = await get_redis_client()
        rate_limiter = RateLimiter(redis_client)
    return rate_limiter

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    limiter = await get_rate_limiter()
    
    # Check rate limit
    allowed, rate_limit_info = await limiter.check_rate_limit(request)
    
    if not allowed:
        # Rate limit exceeded
        headers = await limiter.get_rate_limit_headers(rate_limit_info)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "type": "rate_limit_exceeded",
                    "message": "Rate limit exceeded. Please try again later.",
                    "limit": rate_limit_info["limit"],
                    "remaining": rate_limit_info["remaining"],
                    "reset": rate_limit_info["reset"]
                }
            },
            headers=headers
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    headers = await limiter.get_rate_limit_headers(rate_limit_info)
    for header, value in headers.items():
        response.headers[header] = value
    
    return response

# Rate limit decorator for specific endpoints
def rate_limit(endpoint_type: str):
    """Decorator to apply rate limiting to specific endpoints"""
    async def decorator(request: Request, call_next):
        limiter = await get_rate_limiter()
        
        # Override endpoint type for this specific request
        original_path = request.url.path
        request.url.path = f"/{endpoint_type}/override"
        
        allowed, rate_limit_info = await limiter.check_rate_limit(request)
        
        # Restore original path
        request.url.path = original_path
        
        if not allowed:
            headers = await limiter.get_rate_limit_headers(rate_limit_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded for {endpoint_type} endpoint",
                        "limit": rate_limit_info["limit"],
                        "remaining": rate_limit_info["remaining"],
                        "reset": rate_limit_info["reset"]
                    }
                },
                headers=headers
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        headers = await limiter.get_rate_limit_headers(rate_limit_info)
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    return decorator
