"""
Soft quota tracking for pilot/demo use (in-memory)
"""

import time
import threading
from collections import defaultdict
from typing import Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

# Configuration
SOFT_CAP = 500  # per key per day
_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: {"count": 0, "last_reset": time.time()})
_lock = threading.Lock()  # Thread safety for concurrent requests

def soft_quota(request: Request):
    """
    Simple quota tracking based on API key or IP address.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 402 if quota exhausted
    """
    # Get quota key (API key or IP)
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if api_key and api_key.startswith("Bearer "):
        api_key = api_key[7:]  # Remove "Bearer " prefix
    
    key = api_key or f"anon:{request.client.host if request.client else 'unknown'}"
    
    now = time.time()
    day_start = int(now // 86400) * 86400  # Start of current day
    
    # Thread-safe access to quota data
    with _lock:
        # Reset daily counter if new day
        if _usage[key]["last_reset"] < day_start:
            _usage[key] = {"count": 0, "last_reset": day_start}
        
        # Check quota
        if _usage[key]["count"] >= SOFT_CAP:
            quota_used = _usage[key]["count"]
            reset_at = int(day_start + 86400)  # Next day
            
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "quota_exhausted",
                    "message": f"Daily quota exhausted. Limit: {SOFT_CAP} requests per day.",
                    "quota_used": quota_used,
                    "quota_limit": SOFT_CAP,
                    "reset_at": reset_at
                }
            )
        
        # Increment usage
        _usage[key]["count"] += 1
        
        # Store quota info in request state
        request.state.quota_used = _usage[key]["count"]
        request.state.quota_remaining = SOFT_CAP - _usage[key]["count"]

def get_quota_stats(key: str) -> Dict[str, int]:
    """
    Get quota statistics for a given key.
    
    Args:
        key: API key or IP address
        
    Returns:
        Dictionary with quota stats
    """
    now = time.time()
    day_start = int(now // 86400) * 86400
    
    with _lock:
        # Reset if new day
        if _usage[key]["last_reset"] < day_start:
            _usage[key] = {"count": 0, "last_reset": day_start}
        
        return {
            "quota_used": _usage[key]["count"],
            "quota_remaining": SOFT_CAP - _usage[key]["count"],
            "quota_limit": SOFT_CAP,
            "reset_at": int(day_start + 86400)
        }

def clear_quotas():
    """Clear all quota data (useful for testing)"""
    global _usage
    _usage.clear()
