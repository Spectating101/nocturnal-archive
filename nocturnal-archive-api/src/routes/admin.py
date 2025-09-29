"""
Admin API routes for key management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from src.auth.models import (
    ApiKeyCreate, ApiKeyResponse, ApiKeyUpdate,
    create_api_key, get_api_key, update_api_key, delete_api_key,
    api_keys_db
)

router = APIRouter(prefix="/v1/admin", tags=["Admin"])

def verify_admin_key(admin_key: str = Depends(lambda: None)):
    """Verify admin key (placeholder - implement proper admin auth)"""
    # TODO: Implement proper admin authentication
    return True

@router.post("/keys", response_model=ApiKeyResponse)
async def create_key(req: ApiKeyCreate, admin: bool = Depends(verify_admin_key)):
    """
    Create a new API key
    
    Returns the full key only once - store it securely!
    """
    try:
        api_key = create_api_key(
            owner=req.owner,
            tier=req.tier,
            rate_limit=req.rate_limit
        )
        
        return api_key
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@router.get("/keys", response_model=List[dict])
async def list_keys(admin: bool = Depends(verify_admin_key)):
    """
    List all API keys (without full keys)
    """
    try:
        keys = []
        for key_id, api_key in api_keys_db.items():
            keys.append({
                "id": api_key.id,
                "owner": api_key.owner,
                "tier": api_key.tier,
                "status": api_key.status,
                "created_at": api_key.created_at,
                "last_used": api_key.last_used,
                "rate_limit": api_key.rate_limit
            })
        
        return keys
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@router.get("/keys/{key_id}")
async def get_key(key_id: str, admin: bool = Depends(verify_admin_key)):
    """
    Get API key details (without full key)
    """
    try:
        api_key = get_api_key(key_id)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "id": api_key.id,
            "owner": api_key.owner,
            "tier": api_key.tier,
            "status": api_key.status,
            "created_at": api_key.created_at,
            "last_used": api_key.last_used,
            "rate_limit": api_key.rate_limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API key: {str(e)}")

@router.patch("/keys/{key_id}")
async def update_key(key_id: str, updates: ApiKeyUpdate, admin: bool = Depends(verify_admin_key)):
    """
    Update API key (status, rate limit)
    """
    try:
        api_key = update_api_key(key_id, updates)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "id": api_key.id,
            "owner": api_key.owner,
            "tier": api_key.tier,
            "status": api_key.status,
            "created_at": api_key.created_at,
            "last_used": api_key.last_used,
            "rate_limit": api_key.rate_limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")

@router.post("/keys/{key_id}/pause")
async def pause_key(key_id: str, admin: bool = Depends(verify_admin_key)):
    """
    Pause an API key
    """
    try:
        updates = ApiKeyUpdate(status="paused")
        api_key = update_api_key(key_id, updates)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause API key: {str(e)}")

@router.post("/keys/{key_id}/resume")
async def resume_key(key_id: str, admin: bool = Depends(verify_admin_key)):
    """
    Resume a paused API key
    """
    try:
        updates = ApiKeyUpdate(status="active")
        api_key = update_api_key(key_id, updates)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume API key: {str(e)}")

@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, admin: bool = Depends(verify_admin_key)):
    """
    Revoke an API key
    """
    try:
        success = delete_api_key(key_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str, admin: bool = Depends(verify_admin_key)):
    """
    Rotate an API key (create new, revoke old)
    """
    try:
        old_key = get_api_key(key_id)
        
        if not old_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Create new key with same properties
        new_key = create_api_key(
            owner=old_key.owner,
            tier=old_key.tier,
            rate_limit=old_key.rate_limit
        )
        
        # Revoke old key
        delete_api_key(key_id)
        
        return {
            "message": "API key rotated successfully",
            "old_key_id": key_id,
            "new_key": new_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rotate API key: {str(e)}")
