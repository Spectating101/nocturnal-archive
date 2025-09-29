"""
Request ID middleware for clean request tracing
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all requests for tracing.
    If X-Request-Id header is provided by client, use it; otherwise generate one.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Use provided request ID or generate new one
        rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = rid
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-Id"] = rid
        
        return response
