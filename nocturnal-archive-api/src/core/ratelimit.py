"""
Simple in-process rate limiting for pilot/demo use
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

# Configuration
WINDOW = 60      # seconds
LIMIT = 120      # max requests per key per WINDOW
_hits: Dict[str, List[float]] = defaultdict(list)
_lock = threading.Lock()  # Thread safety for concurrent requests

def rate_limit(request: Request):
    """
    Simple rate limiting based on API key or IP address.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    # Get rate limit key (API key or IP)
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if api_key and api_key.startswith("Bearer "):
        api_key = api_key[7:]  # Remove "Bearer " prefix
    
    key = api_key or f"anon:{request.client.host if request.client else 'unknown'}"
    
    now = time.time()
    
    # Thread-safe access to rate limit data
    with _lock:
        q = _hits[key]
        
        # Clean old entries outside the window
        while q and now - q[0] > WINDOW:
            q.pop(0)
        
        # Check if limit exceeded
        if len(q) >= LIMIT:
            retry_after = int(WINDOW - (now - q[0])) if q else WINDOW
            remaining = LIMIT - len(q)
            
            # Create error response with proper headers
            error_response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded. Maximum {LIMIT} requests per {WINDOW} seconds.",
                    "retry_after": retry_after
                }
            )
            
            # Add rate limit headers to error response
            error_response.headers["X-RateLimit-Limit"] = str(LIMIT)
            error_response.headers["X-RateLimit-Remaining"] = str(remaining)
            error_response.headers["X-RateLimit-Reset"] = str(int(q[0] + WINDOW) if q else int(now + WINDOW))
            error_response.headers["Retry-After"] = str(retry_after)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded. Maximum {LIMIT} requests per {WINDOW} seconds.",
                    "retry_after": retry_after
                }
            )
        
        # Record this request
        q.append(now)
    
    # Add rate limit headers to response
    remaining = LIMIT - len(q)
    reset_time = int(q[0] + WINDOW) if q else int(now + WINDOW)
    
    # Store in request state for middleware to add headers
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_time

def get_rate_limit_stats(key: str) -> Dict[str, int]:
    """
    Get rate limit statistics for a given key.
    
    Args:
        key: API key or IP address
        
    Returns:
        Dictionary with rate limit stats
    """
    now = time.time()
    
    with _lock:
        q = _hits[key]
        
        # Clean old entries
        while q and now - q[0] > WINDOW:
            q.pop(0)
        
        return {
            "requests_in_window": len(q),
            "limit": LIMIT,
            "remaining": LIMIT - len(q),
            "window_seconds": WINDOW,
            "reset_at": int(q[0] + WINDOW) if q else int(now + WINDOW)
        }

def clear_rate_limits():
    """Clear all rate limit data (useful for testing)"""
    global _hits
    _hits.clear()
