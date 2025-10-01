"""
Production-ready authentication and authorization system
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
import redis.asyncio as redis

logger = structlog.get_logger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY_EXPIRE_DAYS = 90

# Password hashing - using argon2 for better compatibility
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthManager:
    """Production-ready authentication manager"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.api_keys = {}  # In production, this would be in database
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def create_api_key(self, user_id: str, name: str, permissions: list = None) -> str:
        """Create a new API key for a user"""
        if permissions is None:
            permissions = ["read"]
        
        # Generate secure API key
        api_key = f"na_{secrets.token_urlsafe(32)}"
        
        # Store in Redis with expiration
        key_data = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "usage_count": 0
        }
        
        await self.redis.setex(
            f"api_key:{api_key}",
            API_KEY_EXPIRE_DAYS * 24 * 3600,  # 90 days
            str(key_data)
        )
        
        logger.info("API key created", user_id=user_id, name=name, permissions=permissions)
        return api_key
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user data"""
        if not api_key or not api_key.startswith("na_"):
            return None
        
        # Check Redis cache first
        key_data = await self.redis.get(f"api_key:{api_key}")
        if not key_data:
            return None
        
        try:
            import ast
            data = ast.literal_eval(key_data.decode())
            
            # Update usage statistics
            data["last_used"] = datetime.utcnow().isoformat()
            data["usage_count"] = data.get("usage_count", 0) + 1
            
            await self.redis.setex(
                f"api_key:{api_key}",
                API_KEY_EXPIRE_DAYS * 24 * 3600,
                str(data)
            )
            
            return data
            
        except Exception as e:
            logger.error("Error validating API key", error=str(e))
            return None
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        result = await self.redis.delete(f"api_key:{api_key}")
        logger.info("API key revoked", api_key=api_key[:10] + "...", success=bool(result))
        return bool(result)
    
    async def get_user_api_keys(self, user_id: str) -> list:
        """Get all API keys for a user"""
        keys = []
        async for key in self.redis.scan_iter(match=f"api_key:na_*"):
            key_data = await self.redis.get(key)
            if key_data:
                try:
                    import ast
                    data = ast.literal_eval(key_data.decode())
                    if data.get("user_id") == user_id:
                        keys.append({
                            "api_key": key.decode().replace("api_key:", ""),
                            "name": data.get("name"),
                            "permissions": data.get("permissions", []),
                            "created_at": data.get("created_at"),
                            "last_used": data.get("last_used"),
                            "usage_count": data.get("usage_count", 0)
                        })
                except Exception as e:
                    logger.error("Error parsing API key data", error=str(e))
                    continue
        
        return keys

# Global auth manager instance
auth_manager = None

async def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance"""
    global auth_manager
    if auth_manager is None:
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        auth_manager = AuthManager(redis_client)
    return auth_manager

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    auth_mgr = await get_auth_manager()
    
    # Try API key first
    if credentials.credentials.startswith("na_"):
        user_data = await auth_mgr.validate_api_key(credentials.credentials)
        if user_data:
            return user_data
    
    # Try JWT token
    user_data = auth_mgr.verify_token(credentials.credentials)
    if user_data:
        return user_data
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_checker(current_user: Dict[str, Any] = get_current_user):
        user = await current_user
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    return permission_checker

# Permission decorators
require_read = require_permission("read")
require_write = require_permission("write")
require_admin = require_permission("admin")
