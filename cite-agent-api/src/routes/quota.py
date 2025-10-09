"""
Quota management routes for pilot mode
"""

from fastapi import APIRouter, Request, HTTPException
from src.core.ratelimit import get_rate_limit_stats
from src.core.soft_quota import get_quota_stats

router = APIRouter(prefix="/v1/quota", tags=["quota"])

@router.get("/status")
def get_quota_status(request: Request):
    """
    Get current quota and rate limit status for the API key
    
    Returns rate limit and quota information for the current API key.
    """
    # Get API key
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if api_key and api_key.startswith("Bearer "):
        api_key = api_key[7:]  # Remove "Bearer " prefix
    
    key = api_key or f"anon:{request.client.host if request.client else 'unknown'}"
    
    try:
        # Get rate limit stats
        rate_stats = get_rate_limit_stats(key)
        
        # Get quota stats
        quota_stats = get_quota_stats(key)
        
        return {
            "api_key_hash": key[:8] + "..." if len(key) > 8 else key,
            "rate_limit": {
                "requests_in_window": rate_stats["requests_in_window"],
                "limit": rate_stats["limit"],
                "remaining": rate_stats["remaining"],
                "window_seconds": rate_stats["window_seconds"],
                "reset_at": rate_stats["reset_at"]
            },
            "quota": {
                "used": quota_stats["quota_used"],
                "remaining": quota_stats["quota_remaining"],
                "limit": quota_stats["quota_limit"],
                "reset_at": quota_stats["reset_at"]
            },
            "pilot_mode": True,
            "guards": ["rate_limit", "soft_quota"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving quota status: {str(e)}"
        )

@router.get("/limits")
def get_limits():
    """
    Get current pilot mode limits and configuration
    
    Returns information about rate limits and quotas for pilot mode.
    """
    return {
        "rate_limit": {
            "requests_per_window": 120,
            "window_seconds": 60,
            "description": "Maximum requests per minute"
        },
        "quota": {
            "requests_per_day": 500,
            "description": "Maximum requests per day"
        },
        "pilot_mode": True,
        "note": "These are soft limits for pilot mode. Production will have user-specific quotas."
    }
