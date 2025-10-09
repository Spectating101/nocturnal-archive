"""
Request tracing middleware
"""

import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            trace_id=trace_id
        )
        
        # Process request
        response = await call_next(request)
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            trace_id=trace_id
        )
        
        return response
