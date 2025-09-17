"""
Response models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .paper import SearchResult, SynthesisResult


class FormatResponse(BaseModel):
    """Format response model"""
    formatted: str = Field(..., description="Formatted citations")
    format: str = Field(..., description="Citation format used")
    count: int = Field(..., description="Number of papers formatted")
    trace_id: str = Field(..., description="Request trace ID for debugging")


class HealthResponse(BaseModel):
    """Health response model"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, str] = Field(..., description="Status of individual services")
    version: str = Field(..., description="API version")
    issues: Optional[list] = Field(None, description="List of current issues (if any)")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    trace_id: Optional[str] = Field(None, description="Request trace ID for debugging")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
