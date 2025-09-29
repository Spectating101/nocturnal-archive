"""
API key authentication and rate limiting middleware
"""

import time
import hashlib
import structlog
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        # Simple in-memory storage for demo (replace with DB in production)
        self.api_keys = {
            "demo-key-123": {
                "owner": "demo",
                "tier": "free",
                "rate_limit": 100,  # requests per hour
                "created_at": time.time(),
                "active": True
            },
            "pro-key-456": {
                "owner": "pro-user",
                "tier": "pro", 
                "rate_limit": 1000,
                "created_at": time.time(),
                "active": True
            }
        }
        
        # Rate limiting storage (in-memory for demo)
        self.rate_limits: Dict[str, Dict[str, float]] = {}
        
        # API endpoints that require authentication
        self.protected_paths = [
            "/api/search",
            "/api/synthesize", 
            "/api/format"
        ]
    
    def _get_rate_limit_key(self, api_key: str) -> str:
        """Get rate limit key for current hour"""
        current_hour = int(time.time() // 3600)
        return f"{api_key}:{current_hour}"
    
    def _check_rate_limit(self, api_key: str, key_info: Dict) -> tuple[bool, Optional[int]]:
        """Check if request is within rate limit"""
        rate_key = self._get_rate_limit_key(api_key)
        current_time = time.time()
        
        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = {
                "count": 0,
                "reset_time": current_time + 3600  # Reset in 1 hour
            }
        
        rate_data = self.rate_limits[rate_key]
        
        # Reset if hour has passed
        if current_time >= rate_data["reset_time"]:
            rate_data["count"] = 0
            rate_data["reset_time"] = current_time + 3600
        
        # Check if within limit
        if rate_data["count"] >= key_info["rate_limit"]:
            retry_after = int(rate_data["reset_time"] - current_time)
            return False, retry_after
        
        # Increment counter
        rate_data["count"] += 1
        return True, None
    
    async def dispatch(self, request: Request, call_next):
        # Check if this endpoint requires authentication
        if any(request.url.path.startswith(path) for path in self.protected_paths):
            # Get API key from header
            api_key = request.headers.get("Authorization")
            if api_key and api_key.startswith("Bearer "):
                api_key = api_key[7:]  # Remove "Bearer " prefix
            else:
                api_key = request.headers.get("X-API-Key")
            
            if not api_key:
                from src.utils.error_handling import create_problem_response, get_error_type
                error_info = get_error_type("invalid-api-key")
                return create_problem_response(
                    request, status.HTTP_401_UNAUTHORIZED,
                    "invalid-api-key", error_info["title"], error_info["detail"]
                )
            
            # Validate API key
            if api_key not in self.api_keys:
                logger.warning(
                    "Invalid API key attempt",
                    api_key_hash=hashlib.sha256(api_key.encode()).hexdigest()[:8],
                    ip=request.client.host if request.client else "unknown"
                )
                from src.utils.error_handling import create_problem_response, get_error_type
                error_info = get_error_type("invalid-api-key")
                return create_problem_response(
                    request, status.HTTP_401_UNAUTHORIZED,
                    "invalid-api-key", error_info["title"], error_info["detail"]
                )
            
            key_info = self.api_keys[api_key]
            if not key_info["active"]:
                from src.utils.error_handling import create_problem_response, get_error_type
                error_info = get_error_type("api-key-paused")
                return create_problem_response(
                    request, status.HTTP_403_FORBIDDEN,
                    "api-key-paused", error_info["title"], error_info["detail"]
                )
            
            # Check rate limit
            allowed, retry_after = self._check_rate_limit(api_key, key_info)
            if not allowed:
                from src.utils.error_handling import create_problem_response, get_error_type
                error_info = get_error_type("rate-limit-exceeded")
                response = create_problem_response(
                    request, status.HTTP_429_TOO_MANY_REQUESTS,
                    "rate-limit-exceeded", error_info["title"], error_info["detail"],
                    retry_after=retry_after
                )
                response.headers["Retry-After"] = str(retry_after)
                return response
            
            # Add key info to request state
            request.state.api_key = api_key
            request.state.key_info = key_info
            
            # Calculate usage stats
            rate_key = self._get_rate_limit_key(api_key)
            rate_data = self.rate_limits.get(rate_key, {"count": 0, "reset_time": time.time() + 3600})
            remaining = max(0, key_info["rate_limit"] - rate_data["count"])
            
            # Process request
            response = await call_next(request)
            
            # Add usage headers (RFC 6585 compliant)
            response.headers["X-Request-ID"] = getattr(request.state, "trace_id", "unknown")
            response.headers["X-RateLimit-Limit"] = str(key_info["rate_limit"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(rate_data["reset_time"]))
            response.headers["X-Usage-Today"] = str(rate_data["count"])
            
            return response
        
        # No authentication required for this endpoint
        response = await call_next(request)
        return response
