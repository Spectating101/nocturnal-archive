"""
Structured error handling with request IDs
"""
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict

logger = structlog.get_logger(__name__)


def wire_errors(app: FastAPI) -> None:
    """
    Wire up structured error handling for the FastAPI application.
    All unhandled exceptions will return structured JSON responses with request IDs.
    """
    
    @app.exception_handler(Exception)
    async def handle_all_exceptions(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler that returns structured error responses.
        Never leaks secrets or internal details - keeps errors terse and safe.
        """
        rid = getattr(request.state, "request_id", getattr(request.state, "trace_id", "unknown"))
        
        # Log the full error details server-side (never sent to client)
        logger.error(
            "Unhandled exception",
            request_id=rid,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True
        )
        
        # Return safe, structured error response to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "request_id": rid,
                "message": "An internal error occurred. Please try again later."
            }
        )
    
    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        """Handle validation errors with 400 status"""
        rid = getattr(request.state, "request_id", getattr(request.state, "trace_id", "unknown"))
        
        logger.warning(
            "Validation error",
            request_id=rid,
            path=request.url.path,
            error_message=str(exc)
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "request_id": rid,
                "message": "Invalid input provided"
            }
        )
