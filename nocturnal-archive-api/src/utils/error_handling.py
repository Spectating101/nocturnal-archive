"""Lightweight error response helpers used by legacy routes."""

from __future__ import annotations

from typing import Any, Dict, Optional


def create_problem_response(detail: str, status: int = 500, code: Optional[str] = None) -> Dict[str, Any]:
    """Return a simple RFC 7807-style problem response payload."""
    payload: Dict[str, Any] = {
        "status": status,
        "title": "Request failed",
        "detail": detail,
    }
    if code:
        payload["code"] = code
    return payload


def get_error_type(status: int) -> str:
    """Map HTTP status codes to a coarse error type string."""
    if status >= 500:
        return "server_error"
    if status == 404:
        return "not_found"
    if status == 401:
        return "auth_error"
    if status == 400:
        return "validation_error"
    return "unknown_error"
