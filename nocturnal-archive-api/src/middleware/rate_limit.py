"""
Rate limiting middleware
"""

import time
import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_hour: int = 100, burst_limit: int = 10):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if not self._check_rate_limit(client_id):
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "trace_id": getattr(request.state, "trace_id", None)
                }
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits"""
        
        current_time = time.time()
        
        # Initialize client requests if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests (older than 1 hour)
        hour_ago = current_time - 3600
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > hour_ago
        ]
        
        # Check hourly limit
        if len(self.requests[client_id]) >= self.requests_per_hour:
            return False
        
        # Check burst limit (requests in last minute)
        minute_ago = current_time - 60
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        if len(recent_requests) >= self.burst_limit:
            return False
        
        # Add current request
        self.requests[client_id].append(current_time)
        return True
