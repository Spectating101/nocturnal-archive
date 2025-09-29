"""
Rate limiting middleware for Nocturnal Platform
Based on FinSight's production-grade rate limiting
"""

import time
import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
from collections import defaultdict

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Production-grade rate limiting middleware"""
    
    def __init__(
        self, 
        app, 
        requests_per_hour: int = 100, 
        burst_limit: int = 10, 
        per_ip_limit: int = 50
    ):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self.per_ip_limit = per_ip_limit  # Global per-IP fuse
        self.requests: Dict[str, list] = {}
        self.ip_requests: Dict[str, list] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (API key or IP)"""
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if api_key:
            # Clean up API key for logging
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]
            return f"api_key:{api_key[:8]}..."
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str, client_ip: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        
        # Clean up old requests (older than 1 hour)
        hour_ago = now - 3600
        minute_ago = now - 60
        
        # Clean up client requests
        if client_id in self.requests:
            self.requests[client_id] = [req_time for req_time in self.requests[client_id] if req_time > hour_ago]
        else:
            self.requests[client_id] = []
        
        # Clean up IP requests
        if client_ip in self.ip_requests:
            self.ip_requests[client_ip] = [req_time for req_time in self.ip_requests[client_ip] if req_time > hour_ago]
        else:
            self.ip_requests[client_ip] = []
        
        # Check hourly limit
        if len(self.requests[client_id]) >= self.requests_per_hour:
            logger.warning(
                "Hourly rate limit exceeded",
                client_id=client_id,
                requests=len(self.requests[client_id]),
                limit=self.requests_per_hour
            )
            return False
        
        # Check burst limit (requests in last minute)
        recent_requests = [req_time for req_time in self.requests[client_id] if req_time > minute_ago]
        if len(recent_requests) >= self.burst_limit:
            logger.warning(
                "Burst rate limit exceeded",
                client_id=client_id,
                recent_requests=len(recent_requests),
                limit=self.burst_limit
            )
            return False
        
        # Check global per-IP limit
        if len(self.ip_requests[client_ip]) >= self.per_ip_limit:
            logger.warning(
                "Per-IP rate limit exceeded",
                client_ip=client_ip,
                requests=len(self.ip_requests[client_ip]),
                limit=self.per_ip_limit
            )
            return False
        
        return True
    
    def _record_request(self, client_id: str, client_ip: str):
        """Record a request for rate limiting"""
        now = time.time()
        
        # Record for client
        if client_id not in self.requests:
            self.requests[client_id] = []
        self.requests[client_id].append(now)
        
        # Record for IP
        if client_ip not in self.ip_requests:
            self.ip_requests[client_ip] = []
        self.ip_requests[client_ip].append(now)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self._get_client_id(request)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limits
        if not self._check_rate_limit(client_id, client_ip):
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                client_ip=client_ip,
                path=request.url.path
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60,
                    "limits": {
                        "requests_per_hour": self.requests_per_hour,
                        "burst_limit": self.burst_limit,
                        "per_ip_limit": self.per_ip_limit
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Record successful request
        self._record_request(client_id, client_ip)
        
        # Add rate limit headers
        remaining_hourly = self.requests_per_hour - len(self.requests[client_id])
        remaining_burst = self.burst_limit - len([r for r in self.requests[client_id] if r > time.time() - 60])
        
        response.headers["X-RateLimit-Limit-Hourly"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hourly"] = str(max(0, remaining_hourly))
        response.headers["X-RateLimit-Limit-Burst"] = str(self.burst_limit)
        response.headers["X-RateLimit-Remaining-Burst"] = str(max(0, remaining_burst))
        
        return response
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        now = time.time()
        hour_ago = now - 3600
        
        # Count active clients
        active_clients = 0
        for client_id, requests in self.requests.items():
            recent_requests = [r for r in requests if r > hour_ago]
            if recent_requests:
                active_clients += 1
        
        # Count active IPs
        active_ips = 0
        for ip, requests in self.ip_requests.items():
            recent_requests = [r for r in requests if r > hour_ago]
            if recent_requests:
                active_ips += 1
        
        return {
            "active_clients": active_clients,
            "active_ips": active_ips,
            "total_clients": len(self.requests),
            "total_ips": len(self.ip_requests),
            "limits": {
                "requests_per_hour": self.requests_per_hour,
                "burst_limit": self.burst_limit,
                "per_ip_limit": self.per_ip_limit
            }
        }
