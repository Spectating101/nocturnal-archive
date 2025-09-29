"""
Authentication models for API key management
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
import hashlib
import secrets
import structlog

logger = structlog.get_logger(__name__)

class ApiKey(BaseModel):
    id: str = Field(..., description="Public key prefix")
    hash: str = Field(..., description="Salted SHA-256 hash")
    owner: str = Field(..., description="Key owner identifier")
    tier: str = Field(default="free", description="Key tier (free, pro, enterprise)")
    status: Literal["active", "paused", "revoked"] = Field(default="active", description="Key status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    rate_limit: int = Field(default=100, description="Requests per hour")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ApiKeyCreate(BaseModel):
    owner: str
    tier: str = "free"
    rate_limit: Optional[int] = None

class ApiKeyResponse(BaseModel):
    id: str
    key: str  # Full key (only returned on creation)
    owner: str
    tier: str
    status: str
    created_at: datetime
    rate_limit: int

class ApiKeyUpdate(BaseModel):
    status: Optional[Literal["active", "paused", "revoked"]] = None
    rate_limit: Optional[int] = None

def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key
    
    Returns:
        Tuple of (full_key, key_id)
    """
    # Generate a secure random key
    full_key = f"noct_{secrets.token_urlsafe(32)}"
    
    # Extract ID (first 8 characters after prefix)
    key_id = full_key[:12]  # noct_ + 8 chars
    
    return full_key, key_id

def hash_api_key(key: str) -> str:
    """
    Hash an API key with salt
    
    Args:
        key: Full API key
    
    Returns:
        Salted SHA-256 hash
    """
    # Generate a random salt
    salt = secrets.token_hex(16)
    
    # Hash the key with salt
    hashed = hashlib.sha256(f"{salt}:{key}".encode()).hexdigest()
    
    # Return salt + hash for storage
    return f"{salt}:{hashed}"

def verify_api_key(key: str, stored_hash: str) -> bool:
    """
    Verify an API key against stored hash
    
    Args:
        key: API key to verify
        stored_hash: Stored hash (salt:hash format)
    
    Returns:
        True if key matches
    """
    try:
        salt, hash_part = stored_hash.split(":", 1)
        computed_hash = hashlib.sha256(f"{salt}:{key}".encode()).hexdigest()
        return computed_hash == hash_part
    except (ValueError, AttributeError):
        return False

# In-memory storage for demo (replace with database in production)
api_keys_db: dict[str, ApiKey] = {}

def create_api_key(owner: str, tier: str = "free", rate_limit: Optional[int] = None) -> ApiKeyResponse:
    """
    Create a new API key
    
    Args:
        owner: Key owner identifier
        tier: Key tier
        rate_limit: Custom rate limit (uses tier default if None)
    
    Returns:
        API key response with full key
    """
    # Set rate limits by tier
    tier_limits = {
        "free": 100,
        "pro": 1000,
        "enterprise": 10000
    }
    
    if rate_limit is None:
        rate_limit = tier_limits.get(tier, 100)
    
    # Generate key
    full_key, key_id = generate_api_key()
    key_hash = hash_api_key(full_key)
    
    # Create API key record
    api_key = ApiKey(
        id=key_id,
        hash=key_hash,
        owner=owner,
        tier=tier,
        rate_limit=rate_limit
    )
    
    # Store in database
    api_keys_db[key_id] = api_key
    
    logger.info("API key created", key_id=key_id, owner=owner, tier=tier)
    
    return ApiKeyResponse(
        id=key_id,
        key=full_key,  # Only returned on creation
        owner=owner,
        tier=tier,
        status="active",
        created_at=api_key.created_at,
        rate_limit=rate_limit
    )

def get_api_key(key_id: str) -> Optional[ApiKey]:
    """Get API key by ID"""
    return api_keys_db.get(key_id)

def update_api_key(key_id: str, updates: ApiKeyUpdate) -> Optional[ApiKey]:
    """Update API key"""
    if key_id not in api_keys_db:
        return None
    
    api_key = api_keys_db[key_id]
    
    if updates.status is not None:
        api_key.status = updates.status
    
    if updates.rate_limit is not None:
        api_key.rate_limit = updates.rate_limit
    
    logger.info("API key updated", key_id=key_id, updates=updates.model_dump())
    
    return api_key

def delete_api_key(key_id: str) -> bool:
    """Delete (revoke) API key"""
    if key_id not in api_keys_db:
        return False
    
    api_key = api_keys_db[key_id]
    api_key.status = "revoked"
    
    logger.info("API key revoked", key_id=key_id)
    
    return True

def verify_api_key_by_full_key(full_key: str) -> Optional[ApiKey]:
    """Verify API key and return key record"""
    if not full_key.startswith("noct_"):
        return None
    
    key_id = full_key[:12]
    api_key = api_keys_db.get(key_id)
    
    if not api_key or api_key.status != "active":
        return None
    
    if verify_api_key(full_key, api_key.hash):
        return api_key
    
    return None
