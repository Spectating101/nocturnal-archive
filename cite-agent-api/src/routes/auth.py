"""
Authentication routes for user registration, login, and token management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import structlog
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, EmailStr, Field
import asyncpg
import os
import hashlib
import base64
from jose import JWTError, jwt
import secrets

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 30-day sessions

# Password hashing - Use SHA256 with salt (bcrypt has issues on Heroku Python 3.13)
def hash_password(password: str, salt: str = None) -> str:
    """Hash password with SHA256 + salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    salted = f"{salt}:{password}".encode('utf-8')
    hashed = hashlib.sha256(salted).hexdigest()
    return f"{salt}${hashed}"

def verify_password_hash(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, expected_hash = stored_hash.split('$', 1)
        computed_hash = hash_password(password, salt)
        return computed_hash == stored_hash
    except:
        return False

# Database connection
async def get_db():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    return await asyncpg.connect(db_url)

# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

class AuthResponse(BaseModel):
    user_id: str
    email: str
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    daily_token_limit: int = 25000
    temp_api_key: Optional[str] = None
    temp_key_expires: Optional[str] = None
    temp_key_provider: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

# Helper functions (using SHA256 instead of bcrypt)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return verify_password_hash(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Routes
def is_academic_email(email: str) -> bool:
    """Validate that email is from an academic domain"""
    if "@" not in email:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain:
        return False
    domain = domain.lower()
    # Accept domains containing edu/ac anywhere (edu.mx, ac.uk, stanford.edu, etc.)
    parts = domain.split(".")
    if len(parts) < 2:
        return False
    academic_markers = {"edu", "ac"}
    return any(part in academic_markers for part in parts)

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user with email and password
    Requires academic email domain (.edu, .ac.uk, etc.)
    """
    # Validate academic email
    if not is_academic_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration requires an academic email address (e.g., .edu, .ac.uk)"
        )

    conn = await get_db()

    try:
        # Check if email already exists
        existing = await conn.fetchrow(
            "SELECT user_id FROM users WHERE email = $1",
            request.email
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = get_password_hash(request.password)
        
        # Create user
        user_id = secrets.token_urlsafe(16)
        await conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, created_at, tokens_used_today, last_token_reset)
            VALUES ($1, $2, $3, $4, 0, CURRENT_DATE)
            """,
            user_id, request.email, password_hash, datetime.now(timezone.utc)
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id, "email": request.email}
        )
        
        # Create session
        session_id = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        
        await conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, token, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id, user_id, access_token, datetime.now(timezone.utc), expires_at
        )
        
        logger.info("User registered", user_id=user_id, email=request.email)
        
        return AuthResponse(
            user_id=user_id,
            email=request.email,
            access_token=access_token,
            expires_at=expires_at.isoformat(),
            daily_token_limit=25000
        )
        
    finally:
        await conn.close()

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password hash
    Compatible with existing client that sends SHA256 hash
    """
    conn = await get_db()
    
    try:
        # Get user
        user = await conn.fetchrow(
            "SELECT user_id, email, password_hash FROM users WHERE email = $1",
            request.email
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login = $1 WHERE user_id = $2",
            datetime.now(timezone.utc), user['user_id']
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user['user_id'], "email": user['email']}
        )
        
        # Create session
        session_id = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        
        await conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, token, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id, user['user_id'], access_token, datetime.now(timezone.utc), expires_at
        )
        
        logger.info("User logged in", user_id=user['user_id'], email=user['email'])

        # Generate temporary API key (2 weeks)
        temp_key = (
            os.getenv("CEREBRAS_API_KEY") or
            os.getenv("CEREBRAS_API_KEY_1") or
            os.getenv("CEREBRAS_API_KEY_2") or
            os.getenv("CEREBRAS_API_KEY_3")
        )
        temp_key_expires = datetime.now(timezone.utc) + timedelta(days=14)

        return AuthResponse(
            user_id=user['user_id'],
            email=user['email'],
            access_token=access_token,
            expires_at=expires_at.isoformat(),
            daily_token_limit=25000,
            temp_api_key=temp_key,
            temp_key_expires=temp_key_expires.isoformat(),
            temp_key_provider="cerebras"
        )
        
    finally:
        await conn.close()

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh an access token"""
    conn = await get_db()
    
    try:
        # Verify token
        payload = await verify_token(request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        # Check if user still exists
        user = await conn.fetchrow(
            "SELECT user_id FROM users WHERE user_id = $1",
            user_id
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        new_token = create_access_token(
            data={"sub": user_id, "email": email}
        )
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        
        logger.info("Token refreshed", user_id=user_id)
        
        return AuthResponse(
            user_id=user_id,
            email=email,
            access_token=new_token,
            expires_at=expires_at.isoformat(),
            daily_token_limit=25000
        )
        
    finally:
        await conn.close()

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = await verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    conn = await get_db()
    try:
        user = await conn.fetchrow(
            """
            SELECT user_id, email, created_at, last_login, tokens_used_today, last_token_reset
            FROM users WHERE user_id = $1
            """,
            payload.get("sub")
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user_id": user['user_id'],
            "email": user['email'],
            "created_at": user['created_at'].isoformat(),
            "last_login": user['last_login'].isoformat() if user['last_login'] else None,
            "tokens_used_today": user['tokens_used_today'],
            "tokens_remaining": 25000 - user['tokens_used_today'],
            "last_token_reset": user['last_token_reset'].isoformat()
        }
        
    finally:
        await conn.close()

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user and invalidate token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    conn = await get_db()
    try:
        # Delete session
        await conn.execute(
            "DELETE FROM sessions WHERE token = $1",
            token
        )
        
        logger.info("User logged out")
        
        return {"message": "Successfully logged out"}
        
    finally:
        await conn.close()

