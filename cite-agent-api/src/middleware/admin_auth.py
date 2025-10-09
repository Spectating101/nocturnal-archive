"""
Admin authentication middleware for protecting operational endpoints
"""

import os
import structlog
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect admin/operational endpoints"""
    
    def __init__(self, app, admin_key: str = None):
        super().__init__(app)
        self.admin_key = admin_key or os.getenv("ADMIN_KEY", "admin-key-change-me")
        self.protected_paths = [
            "/v1/diag/",
            "/metrics",
            "/docs",
            "/redoc", 
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a protected endpoint
        if any(request.url.path.startswith(path) for path in self.protected_paths):
            # Check for admin key in header
            admin_key = request.headers.get("X-Admin-Key")
            if not admin_key or admin_key != self.admin_key:
                logger.warning(
                    "Unauthorized access attempt to protected endpoint",
                    path=request.url.path,
                    ip=request.client.host if request.client else "unknown"
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Admin access required"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        response = await call_next(request)
        return response
