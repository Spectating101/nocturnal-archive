"""
Security middleware for input validation and protection
"""

import json
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks and input validation"""
    
    def __init__(self, app):
        super().__init__(app)
        self.max_body_size = 2 * 1024 * 1024  # 2MB limit
        self.max_content_length = 10 * 1024 * 1024  # 10MB for file uploads
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            logger.warning(
                "Request body too large",
                content_length=content_length,
                max_allowed=self.max_content_length,
                ip=request.client.host if request.client else "unknown"
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"}
            )
        
        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-originating-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                logger.info(
                    "Suspicious header detected",
                    header=header,
                    value=request.headers[header],
                    ip=request.client.host if request.client else "unknown"
                )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
