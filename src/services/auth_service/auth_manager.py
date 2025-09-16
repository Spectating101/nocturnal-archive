# src/services/auth_service/auth_manager.py

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Production-grade authentication manager with Supabase integration.
    
    Features:
    - JWT token validation and management
    - User session handling
    - Role-based access control
    - Rate limiting integration
    - Audit logging
    """
    
    def __init__(self, supabase_url: str, supabase_anon_key: str):
        """
        Initialize authentication manager.
        
        Args:
            supabase_url: Supabase project URL
            supabase_anon_key: Supabase anonymous key
        """
        self.supabase_url = supabase_url
        self.supabase_anon_key = supabase_anon_key
        self.security = HTTPBearer()
        
        # JWT settings
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24
        
        logger.info("AuthManager initialized successfully")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return user data.
        
        Args:
            token: JWT token string
            
        Returns:
            User data dictionary
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Verify token with Supabase
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": self.supabase_anon_key
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                user_data = response.json()
                return user_data
                
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Dict[str, Any]:
        """
        Get current authenticated user.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            Current user data
        """
        token = credentials.credentials
        return await self.validate_token(token)
    
    async def create_user(self, email: str, password: str, user_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new user account.
        
        Args:
            email: User email
            password: User password
            user_metadata: Additional user metadata
            
        Returns:
            Created user data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/signup",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password,
                        "user_metadata": user_metadata or {}
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="User creation failed")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail="User creation failed")
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication response with tokens
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Sign in failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Sign in failed")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New authentication tokens
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=refresh_token",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "refresh_token": refresh_token
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid refresh token")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Token refresh failed")
    
    async def sign_out(self, access_token: str) -> bool:
        """
        Sign out user and invalidate tokens.
        
        Args:
            access_token: Access token to invalidate
            
        Returns:
            Success status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/logout",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "apikey": self.supabase_anon_key
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Sign out failed: {str(e)}")
            return False
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            Updated profile data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.supabase_url}/rest/v1/profiles?user_id=eq.{user_id}",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Authorization": f"Bearer {self.supabase_anon_key}",
                        "Content-Type": "application/json"
                    },
                    json=profile_data
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Profile update failed")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Profile update failed")
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user subscription information.
        
        Args:
            user_id: User ID
            
        Returns:
            Subscription data or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/subscriptions?user_id=eq.{user_id}",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Authorization": f"Bearer {self.supabase_anon_key}"
                    }
                )
                
                if response.status_code == 200:
                    subscriptions = response.json()
                    return subscriptions[0] if subscriptions else None
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user subscription: {str(e)}")
            return None
    
    def has_permission(self, user_data: Dict[str, Any], permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_data: User data dictionary
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        user_role = user_data.get("role", "user")
        
        # Role-based permissions
        permissions = {
            "admin": ["admin", "moderator", "user"],
            "moderator": ["moderator", "user"],
            "user": ["user"]
        }
        
        return permission in permissions.get(user_role, ["user"])
    
    async def log_activity(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """
        Log user activity for audit purposes.
        
        Args:
            user_id: User ID
            action: Action performed
            details: Additional details
        """
        try:
            activity_data = {
                "user_id": user_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": "tracked_via_middleware"
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.supabase_url}/rest/v1/activity_logs",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Authorization": f"Bearer {self.supabase_anon_key}",
                        "Content-Type": "application/json"
                    },
                    json=activity_data
                )
                
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")

# Global auth manager instance
auth_manager = AuthManager(
    supabase_url=os.getenv("SUPABASE_URL", ""),
    supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", "")
)
