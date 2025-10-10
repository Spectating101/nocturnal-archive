"""Simple health check without dependencies"""
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    """Simple health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
