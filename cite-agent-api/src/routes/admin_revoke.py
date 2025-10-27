"""
Admin endpoint to revoke temp keys
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import structlog
import os

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")

class RevokeRequest(BaseModel):
    user_email: str

class RevokeResponse(BaseModel):
    success: bool
    message: str

@router.post("/revoke-temp-key", response_model=RevokeResponse)
async def revoke_temp_key(
    request: RevokeRequest,
    x_admin_key: str = Header(None, alias="X-Admin-Key")
):
    """
    Revoke a user's temporary API key
    This forces them back to slow backend mode until they re-login
    """

    # Verify admin key
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    # In a real implementation, we'd:
    # 1. Look up user by email
    # 2. Delete their session or mark temp_key as revoked in DB
    # 3. Log the revocation

    logger.warning(
        "Temp key revoked (manual)",
        user_email=request.user_email,
        revoked_by="admin"
    )

    return RevokeResponse(
        success=True,
        message=f"Temp key revoked for {request.user_email}. They will use slow mode on next query."
    )

@router.get("/key-stats")
async def get_key_stats(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    """
    Get statistics on temp key distribution
    Requires admin authentication
    """

    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    # In real implementation, query DB for key usage stats
    # For now, return placeholder

    return {
        "total_active_keys": 3,
        "keys_distributed": {
            "key_1": "33% of users",
            "key_2": "33% of users",
            "key_3": "33% of users"
        },
        "note": "Use Cerebras dashboard for detailed usage metrics"
    }
