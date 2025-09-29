"""
Archive routes placeholder
TODO: Integrate actual Archive functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from config.settings import Settings, get_settings
from datetime import datetime

router = APIRouter()


@router.get("/status")
async def archive_status(settings: Settings = Depends(get_settings)):
    """Archive module status"""
    return {
        "module": "archive",
        "enabled": settings.archive_enabled,
        "status": "placeholder - not yet integrated",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def archive_health():
    """Archive health check"""
    return {
        "status": "placeholder",
        "message": "Archive integration pending"
    }
