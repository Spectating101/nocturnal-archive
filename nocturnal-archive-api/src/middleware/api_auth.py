"""
API key authentication and rate limiting middleware
"""

import time
import hashlib
import structlog
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        # Simple in-memory storage for demo (replace with DB in production)
        self.api_keys = {
            "demo-key-123": {
                "owner": "demo",
                "tier": "free",
                "rate_limit": 100,  # requests per hour
                "burst_limit": 20,
                "created_at": time.time(),
                "active": True,
                "permissions": {"research", "finance:read"}
            },
            "pro-key-456": {
                "owner": "pro-user",
                "tier": "pro", 
                "rate_limit": 1000,
                "burst_limit": 60,
                "created_at": time.time(),
                "active": True,
                "permissions": {"research", "finance:read", "finance:write"}
            }
        }

        if self.settings.environment == "test":
            # High limits for testing - prevent rate limit failures in stress tests
            self.api_keys.update({
                "na_test_api_key_123": {
                    "owner": "pytest",
                    "tier": "sandbox",
                    "rate_limit": 500,  # 500 req/hour for testing
                    "burst_limit": 100,  # 100 req/min burst for stress tests
                    "created_at": time.time(),
                    "active": True,
                    "permissions": {"research", "finance:read", "finance:write"}
                },
                "na_read_only_key": {
                    "owner": "pytest-read",
                    "tier": "sandbox",
                    "rate_limit": 250,
                    "burst_limit": 50,
                    "created_at": time.time(),
                    "active": True,
                    "permissions": {"research", "finance:read"}
                }
            })
        
        
        # Rate limiting storage (in-memory for demo)
        self.rate_limits: Dict[str, Dict[str, float]] = {}
        
        # API endpoints that require authentication
        self.protected_paths = [
            "/api/search",
            "/api/synthesize", 
            "/api/format",
            "/v1/finance"
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
            rate_data.pop("recent", None)
        
        # Check if within limit
        if rate_data["count"] >= key_info["rate_limit"]:
            retry_after = int(rate_data["reset_time"] - current_time)
            return False, retry_after
        
        # Track burst usage in the last minute
        recent = rate_data.setdefault("recent", [])
        minute_ago = current_time - 60
        recent[:] = [timestamp for timestamp in recent if timestamp > minute_ago]

        burst_limit = key_info.get("burst_limit", self.settings.rate_limit_burst)
        if len(recent) >= burst_limit:
            retry_after = int(max(1, 60 - (current_time - recent[0]) if recent else 60))
            return False, retry_after

        recent.append(current_time)

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
                if self.settings.environment == "test" and request.url.path.startswith("/api/"):
                    api_key = "demo-key-123"
                else:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "authentication_error",
                            "message": "Missing API key. Provide X-API-Key header or Authorization: Bearer <key>",
                            "request_id": getattr(request.state, "trace_id", "unknown")
                        }
                    )

            # Validate API key
            if api_key not in self.api_keys:
                logger.warning(
                    "Invalid API key attempt",
                    api_key_hash=hashlib.sha256(api_key.encode()).hexdigest()[:8],
                    ip=request.client.host if request.client else "unknown"
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "authentication_error",
                        "message": "Invalid API key",
                        "request_id": getattr(request.state, "trace_id", "unknown")
                    }
                )

            key_info = self.api_keys[api_key]
            if not key_info["active"]:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "authentication_error",
                        "message": "API key is inactive",
                        "request_id": getattr(request.state, "trace_id", "unknown")
                    }
                )

            # Permission model: read access for GET, write access for mutating operations
            required_permission: Optional[str] = None
            if request.url.path.startswith("/v1/finance"):
                required_permission = "finance:write" if request.method.upper() not in {"GET", "HEAD", "OPTIONS"} else "finance:read"
            elif request.url.path.startswith("/api"):
                required_permission = "research"

            if required_permission and required_permission not in key_info.get("permissions", set()):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "permission_denied",
                        "message": f"Insufficient permissions. Required: {required_permission}",
                        "request_id": getattr(request.state, "trace_id", "unknown")
                    }
                )
            
            # Check rate limit
            allowed, retry_after = self._check_rate_limit(api_key, key_info)
            if not allowed:
                from fastapi.responses import JSONResponse
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "trace_id": getattr(request.state, "trace_id", None)
                    }
                )
                response.headers["Retry-After"] = str(max(1, retry_after or 1))
                response.headers["X-RateLimit-Limit"] = str(key_info["rate_limit"])
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + max(1, retry_after or 60))
                response.headers["X-Usage-Today"] = str(key_info.get("rate_limit", 0))
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
