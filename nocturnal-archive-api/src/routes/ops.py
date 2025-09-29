"""
Operational endpoints for monitoring and system health
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/ping")
def ping() -> Dict[str, str]:
    """
    Simple liveness check that hits minimal code path
    
    Returns:
        Simple OK response for health checks
    """
    return {"ok": "true", "status": "alive"}


@router.get("/guards")
def guards_status() -> Dict[str, Any]:
    """
    Get current guard status and in-memory counters
    
    Returns:
        Current rate limit and soft quota status with statistics
    """
    try:
        from src.core.ratelimit import LIMIT, WINDOW, get_rate_limit_stats
        from src.core.soft_quota import SOFT_CAP, get_quota_stats
        
        # Get sample stats (using a test key)
        test_key = "ops-check"
        rate_stats = get_rate_limit_stats(test_key)
        quota_stats = get_quota_stats(test_key)
        
        return {
            "rate_limit": {
                "limit": LIMIT,
                "window_seconds": WINDOW,
                "description": f"Maximum {LIMIT} requests per {WINDOW} seconds per API key"
            },
            "soft_quota": {
                "limit": SOFT_CAP,
                "description": f"Maximum {SOFT_CAP} requests per day per API key"
            },
            "sample_stats": {
                "rate_limit": rate_stats,
                "quota": quota_stats
            },
            "pilot_mode": True,
            "guards_enabled": ["rate_limit", "soft_quota"]
        }
        
    except Exception as e:
        return {
            "error": "Failed to retrieve guard status",
            "details": str(e),
            "pilot_mode": True
        }


@router.get("/system")
def system_info() -> Dict[str, Any]:
    """
    Get basic system information and configuration
    
    Returns:
        System configuration and status information
    """
    try:
        import os
        from src.config.settings import get_settings
        
        settings = get_settings()
        
        return {
            "environment": settings.environment,
            "fingpt_enabled": bool(getattr(settings, 'fingpt_base_model', None)),
            "rag_enabled": settings.enable_rag,
            "embed_model": settings.rag_embed_model if settings.enable_rag else None,
            "version": "1.0.0-pilot",
            "features": {
                "sentiment_analysis": True,
                "rag_qa": settings.enable_rag,
                "rate_limiting": True,
                "soft_quotas": True,
                "batch_endpoints": True,
                "request_tracing": True
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to retrieve system info",
            "details": str(e)
        }
