#!/usr/bin/env python3
"""
R/SQL Assistant Server with API Key Rotation
Handles multiple Groq API keys with load balancing and failover
"""

import os
import json
import time
import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from groq import Groq, RateLimitError, APIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assistant_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class APIKeyStatus:
    """Track API key usage and health"""
    key_id: str
    api_key: str
    requests_today: int = 0
    requests_per_minute: int = 0
    last_request_time: Optional[datetime] = None
    is_healthy: bool = True
    error_count: int = 0
    daily_limit: int = 14400  # Groq free tier limit
    rate_limit: int = 30  # requests per minute
    last_reset_time: datetime = None

    def __post_init__(self):
        if self.last_reset_time is None:
            self.last_reset_time = datetime.now()

    def can_handle_request(self) -> bool:
        """Check if this API key can handle another request"""
        now = datetime.now()
        
        # Reset daily counter if it's a new day
        if now.date() > self.last_reset_time.date():
            self.requests_today = 0
            self.last_reset_time = now
        
        # Check daily limit
        if self.requests_today >= self.daily_limit:
            return False
        
        # Check rate limit (requests per minute)
        if self.last_request_time:
            time_diff = (now - self.last_request_time).total_seconds()
            if time_diff < 60:  # Within the last minute
                if self.requests_per_minute >= self.rate_limit:
                    return False
            else:
                # Reset per-minute counter
                self.requests_per_minute = 0
        
        return self.is_healthy

    def record_request(self):
        """Record a successful request"""
        now = datetime.now()
        self.requests_today += 1
        self.requests_per_minute += 1
        self.last_request_time = now
        self.error_count = 0  # Reset error count on success

    def record_error(self):
        """Record an error and potentially mark as unhealthy"""
        self.error_count += 1
        if self.error_count >= 5:  # Mark unhealthy after 5 consecutive errors
            self.is_healthy = False
            logger.warning(f"API key {self.key_id} marked as unhealthy after {self.error_count} errors")

class APIKeyManager:
    """Manages multiple API keys with rotation and load balancing"""
    
    def __init__(self):
        self.api_keys: List[APIKeyStatus] = []
        self.load_balancer = deque()
        self.health_check_interval = 300  # 5 minutes
        self._load_api_keys()
        self._initialize_load_balancer()
    
    def _load_api_keys(self):
        """Load API keys from environment variables"""
        key_count = 0
        while True:
            key_id = f"GROQ_API_KEY_{key_count + 1}"
            api_key = os.getenv(key_id)
            if not api_key:
                break
            
            # Check for custom limits
            daily_limit = int(os.getenv(f"{key_id}_DAILY_LIMIT", "14400"))
            rate_limit = int(os.getenv(f"{key_id}_RATE_LIMIT", "30"))
            
            key_status = APIKeyStatus(
                key_id=key_id,
                api_key=api_key,
                daily_limit=daily_limit,
                rate_limit=rate_limit
            )
            
            self.api_keys.append(key_status)
            key_count += 1
            logger.info(f"Loaded API key {key_id} with limits: {daily_limit}/day, {rate_limit}/min")
        
        if not self.api_keys:
            # Fallback to single GROQ_API_KEY
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                key_status = APIKeyStatus(
                    key_id="GROQ_API_KEY",
                    api_key=api_key
                )
                self.api_keys.append(key_status)
                logger.info("Using fallback GROQ_API_KEY")
            else:
                raise ValueError("No API keys found! Set GROQ_API_KEY_1, GROQ_API_KEY_2, etc.")
    
    def _initialize_load_balancer(self):
        """Initialize round-robin load balancer"""
        self.load_balancer = deque(self.api_keys)
        random.shuffle(self.load_balancer)  # Randomize initial order
    
    def get_available_key(self) -> Optional[APIKeyStatus]:
        """Get an available API key using round-robin with health checks"""
        if not self.api_keys:
            return None
        
        # Try to find a healthy key
        attempts = 0
        while attempts < len(self.api_keys):
            key_status = self.load_balancer[0]
            self.load_balancer.rotate(-1)  # Move to next key
            
            if key_status.can_handle_request():
                return key_status
            
            attempts += 1
        
        # If no healthy keys found, try any key (might be rate limited but not broken)
        for key_status in self.api_keys:
            if key_status.is_healthy:
                return key_status
        
        return None
    
    def get_key_status(self) -> List[Dict]:
        """Get status of all API keys"""
        return [asdict(key) for key in self.api_keys]
    
    def reset_daily_limits(self):
        """Reset daily limits for all keys (call this daily)"""
        for key in self.api_keys:
            key.requests_today = 0
            key.last_reset_time = datetime.now()
        logger.info("Daily limits reset for all API keys")

# Global API key manager
api_manager = APIKeyManager()

# Request models
class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    response: str
    key_used: str
    timestamp: str
    request_id: str

# FastAPI app
app = FastAPI(
    title="R/SQL Assistant Server",
    description="Server with API key rotation for R/SQL AI Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking
request_stats = defaultdict(int)
user_stats = defaultdict(lambda: {"requests": 0, "last_request": None})

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request statistics"""
    start_time = time.time()
    
    # Track by endpoint
    endpoint = request.url.path
    request_stats[endpoint] += 1
    
    response = await call_next(request)
    
    # Log request time
    process_time = time.time() - start_time
    logger.info(f"{request.method} {endpoint} - {response.status_code} - {process_time:.3f}s")
    
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "R/SQL Assistant Server",
        "timestamp": datetime.now().isoformat(),
        "api_keys_loaded": len(api_manager.api_keys)
    }

@app.get("/status")
async def get_status():
    """Get detailed server status"""
    return {
        "server_status": "healthy",
        "api_keys": api_manager.get_key_status(),
        "request_stats": dict(request_stats),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests with API key rotation"""
    # Get available API key
    key_status = api_manager.get_available_key()
    if not key_status:
        raise HTTPException(
            status_code=503,
            detail="No available API keys. All keys may be rate limited or unhealthy."
        )
    
    # Track user stats
    if request.user_id:
        user_stats[request.user_id]["requests"] += 1
        user_stats[request.user_id]["last_request"] = datetime.now().isoformat()
    
    try:
        # Create Groq client
        client = Groq(api_key=key_status.api_key)
        
        # Make API call
        response = client.chat.completions.create(
            model=request.model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant for R and SQL programming. 
                    Provide clear, concise answers with code examples when appropriate.
                    Focus on practical solutions and best practices.
                    If asked about R, provide R code examples.
                    If asked about SQL, provide SQL examples.
                    Always explain what the code does."""
                },
                {
                    "role": "user", 
                    "content": request.question
                }
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Record successful request
        key_status.record_request()
        
        # Generate response
        request_id = f"req_{int(time.time() * 1000)}"
        chat_response = ChatResponse(
            response=response.choices[0].message.content,
            key_used=key_status.key_id,
            timestamp=datetime.now().isoformat(),
            request_id=request_id
        )
        
        logger.info(f"Request {request_id} completed using {key_status.key_id}")
        return chat_response
        
    except RateLimitError as e:
        key_status.record_error()
        logger.warning(f"Rate limit hit for {key_status.key_id}: {e}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {key_status.key_id}. Please try again later."
        )
    except APIError as e:
        key_status.record_error()
        logger.error(f"API error for {key_status.key_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"API error: {str(e)}"
        )
    except Exception as e:
        key_status.record_error()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/stats")
async def get_stats():
    """Get usage statistics"""
    return {
        "request_stats": dict(request_stats),
        "user_stats": dict(user_stats),
        "api_key_status": api_manager.get_key_status(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/reset-daily-limits")
async def reset_daily_limits():
    """Admin endpoint to reset daily limits"""
    api_manager.reset_daily_limits()
    return {"message": "Daily limits reset successfully"}

@app.post("/admin/health-check")
async def health_check():
    """Admin endpoint to check API key health"""
    healthy_keys = [key for key in api_manager.api_keys if key.is_healthy]
    return {
        "total_keys": len(api_manager.api_keys),
        "healthy_keys": len(healthy_keys),
        "unhealthy_keys": len(api_manager.api_keys) - len(healthy_keys),
        "key_details": api_manager.get_key_status()
    }

# Background task for daily reset
async def daily_reset_task():
    """Background task to reset daily limits"""
    while True:
        await asyncio.sleep(3600)  # Check every hour
        current_hour = datetime.now().hour
        if current_hour == 0:  # Reset at midnight
            api_manager.reset_daily_limits()
            logger.info("Daily limits reset via background task")

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("Starting R/SQL Assistant Server")
    logger.info(f"Loaded {len(api_manager.api_keys)} API keys")
    
    # Start background task
    asyncio.create_task(daily_reset_task())

if __name__ == "__main__":
    # Configuration
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    workers = int(os.getenv("SERVER_WORKERS", "1"))
    
    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
