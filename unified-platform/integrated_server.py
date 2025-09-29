#!/usr/bin/env python3
"""
Integrated Nocturnal Platform Server
Combines RStudio Extension's working Groq service with Unified Platform features
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request, Depends
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
        logging.FileHandler('nocturnal_platform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# GROQ API KEY MANAGEMENT (From RStudio Extension - WORKING!)
# =============================================================================

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

class GroqAPIKeyManager:
    """Manage multiple Groq API keys with rotation and load balancing"""
    
    def __init__(self):
        self.api_keys: List[APIKeyStatus] = []
        self.load_api_keys()
        logger.info(f"Initialized with {len(self.api_keys)} API keys")
    
    def load_api_keys(self):
        """Load API keys from environment variables"""
        keys = []
        
        # Load up to 3 API keys
        for i in range(1, 4):
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key and key.strip():
                keys.append(APIKeyStatus(
                    key_id=f"key_{i}",
                    api_key=key.strip(),
                    daily_limit=int(os.getenv(f"GROQ_API_KEY_{i}_DAILY_LIMIT", "14400")),
                    rate_limit=int(os.getenv(f"GROQ_API_KEY_{i}_RATE_LIMIT", "30"))
                ))
        
        self.api_keys = keys
    
    def get_available_key(self) -> Optional[APIKeyStatus]:
        """Get an available API key with load balancing"""
        now = datetime.now()
        
        # Reset daily counters if needed
        for key in self.api_keys:
            if key.last_reset_time.date() < now.date():
                key.requests_today = 0
                key.last_reset_time = now
                key.is_healthy = True
                key.error_count = 0
        
        # Find healthy keys with capacity
        available_keys = []
        for key in self.api_keys:
            if (key.is_healthy and 
                key.requests_today < key.daily_limit and 
                key.requests_per_minute < key.rate_limit):
                available_keys.append(key)
        
        if not available_keys:
            logger.warning("No available API keys")
            return None
        
        # Load balance by selecting key with least usage
        selected_key = min(available_keys, key=lambda k: k.requests_today)
        return selected_key
    
    def record_request(self, key: APIKeyStatus, success: bool = True):
        """Record a request for usage tracking"""
        now = datetime.now()
        key.requests_today += 1
        key.requests_per_minute += 1
        key.last_request_time = now
        
        if not success:
            key.error_count += 1
            if key.error_count >= 5:  # Mark unhealthy after 5 errors
                key.is_healthy = False
                logger.warning(f"Marked API key {key.key_id} as unhealthy after {key.error_count} errors")
    
    def get_key_status(self) -> Dict[str, Any]:
        """Get status of all API keys"""
        return {
            "total_keys": len(self.api_keys),
            "healthy_keys": sum(1 for k in self.api_keys if k.is_healthy),
            "keys": [
                {
                    "key_id": k.key_id,
                    "requests_today": k.requests_today,
                    "daily_limit": k.daily_limit,
                    "requests_per_minute": k.requests_per_minute,
                    "rate_limit": k.rate_limit,
                    "is_healthy": k.is_healthy,
                    "error_count": k.error_count,
                    "last_reset": k.last_reset_time.isoformat()
                }
                for k in self.api_keys
            ]
        }

# Global API key manager
api_manager = GroqAPIKeyManager()

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """Request model for chat assistance"""
    question: str
    model: Optional[str] = "llama-3.1-8b-instant"
    temperature: float = 0.5
    max_tokens: int = 1200
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat assistance"""
    answer: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    timestamp: str
    user_id: Optional[str] = None

class UnifiedSearchRequest(BaseModel):
    """Request model for unified search"""
    query: str
    modules: List[str] = ["assistant"]
    max_results: int = 10
    user_id: Optional[str] = None

class UnifiedSearchResponse(BaseModel):
    """Response model for unified search"""
    query: str
    results: Dict[str, List[Dict[str, Any]]]
    total_results: int
    modules_searched: List[str]
    timestamp: str

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Nocturnal Platform",
    description="Unified platform combining FinSight (Financial Data), Archive (Research), and Assistant (R/SQL)",
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

# =============================================================================
# REAL MODULE ROUTES
# =============================================================================

# Include real FinSight routes
try:
    from src.routes.finsight_real import router as finsight_router
    app.include_router(finsight_router)
    logger.info("FinSight routes included successfully")
except ImportError as e:
    logger.warning(f"Could not include FinSight routes: {e}")

# Include real Archive routes  
try:
    from src.routes.archive_real import router as archive_router
    app.include_router(archive_router)
    logger.info("Archive routes included successfully")
except ImportError as e:
    logger.warning(f"Could not include Archive routes: {e}")

# =============================================================================
# CORE ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check and platform overview"""
    return {
        "status": "healthy",
        "platform": "Nocturnal Platform",
        "version": "1.0.0",
        "modules": {
            "assistant": {
                "enabled": True,
                "description": "R/SQL programming assistance"
            },
            "finsight": {
                "enabled": True,
                "description": "Financial data analysis and SEC EDGAR integration"
            },
            "archive": {
                "enabled": True,
                "description": "Academic research and synthesis platform"
            }
        },
        "groq_service": api_manager.get_key_status(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    groq_status = api_manager.get_key_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "groq": {
                "status": "healthy" if groq_status["healthy_keys"] > 0 else "unhealthy",
                "healthy_keys": groq_status["healthy_keys"],
                "total_keys": groq_status["total_keys"]
            }
        },
        "request_stats": dict(request_stats)
    }

@app.get("/status")
async def get_status():
    """Get detailed platform status"""
    return {
        "platform_status": "operational",
        "modules": {
            "assistant": {
                "enabled": True,
                "endpoints": ["/assistant/*"]
            },
            "finsight": {
                "enabled": False,
                "endpoints": ["/finsight/* (coming soon)"]
            },
            "archive": {
                "enabled": False,
                "endpoints": ["/archive/* (coming soon)"]
            },
            "unified": {
                "enabled": True,
                "endpoints": ["/unified/*"]
            }
        },
        "groq_service": api_manager.get_key_status(),
        "request_stats": dict(request_stats),
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# ASSISTANT MODULE (R/SQL) - WORKING FROM RSTUDIO EXTENSION
# =============================================================================

@app.post("/assistant/chat", response_model=ChatResponse)
async def chat_assistance(request: ChatRequest):
    """Get R/SQL programming assistance"""
    
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
        # Create Groq client (explicitly avoid any proxy settings)
        import os
        # Remove any proxy-related environment variables that might interfere
        proxy_vars = ['PROXIES', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
        
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
        api_manager.record_request(key_status, success=True)
        
        # Generate response
        return ChatResponse(
            answer=response.choices[0].message.content,
            model=request.model,
            usage=response.usage.dict() if response.usage else None,
            timestamp=datetime.now().isoformat(),
            user_id=request.user_id
        )
        
    except RateLimitError as e:
        logger.warning(f"Rate limit error: {e}")
        api_manager.record_request(key_status, success=False)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    except APIError as e:
        logger.error(f"API error: {e}")
        api_manager.record_request(key_status, success=False)
        raise HTTPException(
            status_code=500,
            detail="API error occurred. Please try again."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        api_manager.record_request(key_status, success=False)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        )

@app.get("/assistant/chat")
async def chat_assistance_get(
    question: str,
    model: Optional[str] = "llama-3.1-8b-instant",
    temperature: float = 0.5,
    max_tokens: int = 1200,
    user_id: Optional[str] = None
):
    """Get R/SQL programming assistance via GET request"""
    
    request = ChatRequest(
        question=question,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id
    )
    
    return await chat_assistance(request)

@app.get("/assistant/status")
async def assistant_status():
    """Get assistant module status"""
    return {
        "module": "assistant",
        "enabled": True,
        "status": "healthy",
        "groq_service": api_manager.get_key_status(),
        "endpoints": [
            "POST /assistant/chat",
            "GET /assistant/chat",
            "GET /assistant/status"
        ],
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# UNIFIED MODULE (Cross-module features)
# =============================================================================

@app.post("/unified/search", response_model=UnifiedSearchResponse)
async def unified_search(request: UnifiedSearchRequest):
    """Unified search across all enabled modules"""
    
    results = {}
    total_results = 0
    modules_searched = []
    
    # Search each module
    for module in request.modules:
        try:
            if module == "assistant":
                # Search R/SQL knowledge using Groq
                try:
                    # Create a chat request for the assistant
                    chat_request = ChatRequest(
                        question=f"Search for: {request.query}",
                        model="llama-3.1-8b-instant",
                        max_tokens=200
                    )
                    
                    # Get response from assistant
                    assistant_response = await chat_assistance(chat_request)
                    
                    results[module] = [
                        {
                            "title": f"R/SQL help for {request.query}",
                            "type": "code_example",
                            "relevance": 0.9,
                            "source": "assistant",
                            "content": assistant_response.answer[:200] + "..." if len(assistant_response.answer) > 200 else assistant_response.answer
                        }
                    ]
                    total_results += 1
                    modules_searched.append(module)
                    
                except Exception as e:
                    logger.warning(f"Assistant search failed: {e}")
                    results[module] = []
                    
            elif module == "finsight":
                # Search FinSight financial data
                try:
                    # Make internal request to FinSight search
                    import httpx
                    async with httpx.AsyncClient() as client:
                        finsight_response = await client.post(
                            "http://localhost:8000/finsight/kpis/search",
                            json={
                                "ticker": "AAPL",  # Default ticker for demo
                                "kpi": "revenue",
                                "freq": "Q",
                                "limit": 5
                            },
                            timeout=10.0
                        )
                        
                        if finsight_response.status_code == 200:
                            finsight_data = finsight_response.json()
                            results[module] = [
                                {
                                    "title": f"Financial data for {request.query}",
                                    "type": "financial_data",
                                    "relevance": 0.8,
                                    "source": "finsight",
                                    "content": f"Found {finsight_data.get('count', 0)} financial records"
                                }
                            ]
                            total_results += 1
                            modules_searched.append(module)
                        else:
                            results[module] = []
                            
                except Exception as e:
                    logger.warning(f"FinSight search failed: {e}")
                    results[module] = []
                    
            elif module == "archive":
                # Search Archive research papers
                try:
                    # Make internal request to Archive search
                    import httpx
                    async with httpx.AsyncClient() as client:
                        archive_response = await client.post(
                            "http://localhost:8000/archive/search",
                            json={
                                "query": request.query,
                                "limit": 5,
                                "sources": ["openalex"]
                            },
                            timeout=10.0
                        )
                        
                        if archive_response.status_code == 200:
                            archive_data = archive_response.json()
                            results[module] = [
                                {
                                    "title": f"Research papers about {request.query}",
                                    "type": "research_paper",
                                    "relevance": 0.85,
                                    "source": "archive",
                                    "content": f"Found {archive_data.get('count', 0)} research papers"
                                }
                            ]
                            total_results += 1
                            modules_searched.append(module)
                        else:
                            results[module] = []
                            
                except Exception as e:
                    logger.warning(f"Archive search failed: {e}")
                    results[module] = []
                    
        except Exception as e:
            logger.error(f"Module {module} search failed: {e}")
            results[module] = []
    
    if not modules_searched:
        raise HTTPException(status_code=400, detail="No modules could be searched")
    
    return UnifiedSearchResponse(
        query=request.query,
        results=results,
        total_results=total_results,
        modules_searched=modules_searched,
        timestamp=datetime.now().isoformat()
    )

@app.get("/unified/search")
async def unified_search_get(
    query: str,
    modules: str = "assistant",
    max_results: int = 10,
    user_id: Optional[str] = None
):
    """Unified search via GET request"""
    
    request = UnifiedSearchRequest(
        query=query,
        modules=[m.strip() for m in modules.split(",") if m.strip()],
        max_results=max_results,
        user_id=user_id
    )
    
    return await unified_search(request)

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_exception",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    workers = int(os.getenv("SERVER_WORKERS", "1"))
    
    logger.info(f"Starting Nocturnal Platform on {host}:{port}")
    logger.info(f"API keys loaded: {len(api_manager.api_keys)}")
    
    uvicorn.run(
        "integrated_server:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
