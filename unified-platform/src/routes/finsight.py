"""
FinSight routes placeholder
TODO: Integrate actual FinSight functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from config.settings import Settings, get_settings
from datetime import datetime

router = APIRouter()


@router.get("/status")
async def finsight_status(settings: Settings = Depends(get_settings)):
    """FinSight module status"""
    return {
        "module": "finsight",
        "enabled": settings.finsight_enabled,
        "status": "placeholder - not yet integrated",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def finsight_health():
    """FinSight health check"""
    return {
        "status": "placeholder",
        "message": "FinSight integration pending"
    }
