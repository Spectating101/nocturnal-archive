"""
RFC 7807 Problem+JSON error handling
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
import uuid

class ProblemDetail(HTTPException):
    """RFC 7807 Problem+JSON error response"""
    
    def __init__(
        self,
        status_code: int,
        type: str,
        title: str,
        detail: str,
        instance: Optional[str] = None,
        **extensions: Any
    ):
        self.status_code = status_code
        self.type = type
        self.title = title
        self.detail = detail
        self.instance = instance
        self.extensions = extensions
        
        super().__init__(status_code=status_code, detail=detail)

def create_problem_response(
    request: Request,
    status_code: int,
    type: str,
    title: str,
    detail: str,
    **extensions: Any
) -> JSONResponse:
    """Create RFC 7807 Problem+JSON response"""
    
    # Get request ID from headers or generate one
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    problem = {
        "type": f"https://nocturnal.dev/errors/{type}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request_id,
        **extensions
    }
    
    return JSONResponse(
        status_code=status_code,
        content=problem,
        headers={"Content-Type": "application/problem+json"}
    )

# Standard error types
ERROR_TYPES = {
    "claims-not-grounded": {
        "title": "Claims not grounded",
        "detail": "Some numeric claims cannot be verified against available data."
    },
    "queue-full": {
        "title": "Job queue full",
        "detail": "The job queue is currently full. Please try again later."
    },
    "too-many-inflight": {
        "title": "Too many requests in progress",
        "detail": "You have reached the per-key concurrency limit. Please retry later."
    },
    "rate-limit-exceeded": {
        "title": "Rate limit exceeded", 
        "detail": "Too many requests. Please try again later."
    },
    "invalid-api-key": {
        "title": "Invalid API key",
        "detail": "The provided API key is invalid or expired."
    },
    "api-key-paused": {
        "title": "API key paused",
        "detail": "Your API key has been paused. Please contact support."
    },
    "admin-access-required": {
        "title": "Admin access required",
        "detail": "This endpoint requires admin privileges."
    },
    "request-too-large": {
        "title": "Request too large",
        "detail": "The request body exceeds the maximum allowed size."
    },
    "validation-error": {
        "title": "Validation error",
        "detail": "The request data is invalid."
    },
    "circuit-breaker-open": {
        "title": "Service temporarily unavailable",
        "detail": "External service is currently unavailable. Please try again later."
    },
    "job-not-found": {
        "title": "Job not found",
        "detail": "The requested job does not exist or has expired."
    },
    "job-queue-full": {
        "title": "Job queue full",
        "detail": "The job queue is currently full. Please try again later."
    }
}

def get_error_type(error_key: str) -> Dict[str, str]:
    """Get standard error type definition"""
    return ERROR_TYPES.get(error_key, {
        "title": "Internal server error",
        "detail": "An unexpected error occurred."
    })
