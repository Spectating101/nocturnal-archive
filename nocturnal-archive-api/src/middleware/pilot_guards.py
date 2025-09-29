"""
Middleware for pilot guards - adds rate limit and quota headers to responses
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.ratelimit import get_rate_limit_stats
from src.core.soft_quota import get_quota_stats

class PilotGuardsMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit and quota headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Get API key for stats
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix
        
        key = api_key or f"anon:{request.client.host if request.client else 'unknown'}"
        
        # Add rate limit headers if available
        if hasattr(request.state, 'rate_limit_remaining'):
            response.headers["X-RateLimit-Limit"] = "120"
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
        
        # Add quota headers if available
        if hasattr(request.state, 'quota_remaining'):
            response.headers["X-Quota-Limit"] = "500"
            response.headers["X-Quota-Used"] = str(request.state.quota_used)
            response.headers["X-Quota-Remaining"] = str(request.state.quota_remaining)
        
        # Add request timing
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        
        # Add pilot mode indicator
        response.headers["X-Pilot-Mode"] = "true"
        response.headers["X-Guards"] = "rate-limit,soft-quota"
        
        return response
