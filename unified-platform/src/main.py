"""
Unified Nocturnal Platform
Combines FinSight, Archive, and R/SQL Assistant into single FastAPI application
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from config.settings import get_settings, Settings
from services.groq_service import initialize_groq_service, get_groq_service
from middleware.rate_limit import RateLimitMiddleware
from middleware.monitoring import MonitoringMiddleware
from middleware.security import SecurityMiddleware
from routes import finsight, archive, assistant, unified

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    settings = get_settings()
    
    # Startup
    logger.info("Starting Nocturnal Platform", environment=settings.environment)
    
    # Initialize Groq service
    groq_keys = settings.get_groq_api_keys()
    if not groq_keys:
        logger.error("No Groq API keys configured")
        raise Exception("No Groq API keys configured")
    
    initialize_groq_service(groq_keys, settings.groq_default_model)
    logger.info(f"Initialized Groq service with {len(groq_keys)} API keys")
    
    # Initialize database connections
    # TODO: Add database initialization
    
    # Initialize cache
    # TODO: Add cache initialization
    
    logger.info("Nocturnal Platform startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nocturnal Platform")
    # TODO: Add cleanup tasks


# Create FastAPI application
app = FastAPI(
    title="Nocturnal Platform",
    description="Unified platform combining FinSight (Financial Data), Archive (Research), and Assistant (R/SQL)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().debug else None,
    redoc_url="/redoc" if get_settings().debug else None,
)

# Add middleware
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(SecurityMiddleware)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_hour=settings.rate_limit_per_hour,
    burst_limit=settings.rate_limit_burst
)

# Monitoring middleware
if settings.enable_metrics:
    app.add_middleware(MonitoringMiddleware)

# Trusted host middleware (production)
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )


# Global request tracking
request_stats = {
    "total_requests": 0,
    "module_requests": {"finsight": 0, "archive": 0, "assistant": 0, "unified": 0},
    "start_time": datetime.now().isoformat()
}


@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request statistics"""
    start_time = time.time()
    
    # Track total requests
    request_stats["total_requests"] += 1
    
    # Track module requests
    path = request.url.path
    if path.startswith("/api/v1/finsight"):
        request_stats["module_requests"]["finsight"] += 1
    elif path.startswith("/api/v1/archive"):
        request_stats["module_requests"]["archive"] += 1
    elif path.startswith("/api/v1/assistant"):
        request_stats["module_requests"]["assistant"] += 1
    elif path.startswith("/api/v1/unified"):
        request_stats["module_requests"]["unified"] += 1
    
    response = await call_next(request)
    
    # Log request
    process_time = time.time() - start_time
    logger.info(
        "Request processed",
        method=request.method,
        path=path,
        status_code=response.status_code,
        process_time=round(process_time, 3)
    )
    
    return response


# Root endpoints
@app.get("/")
async def root():
    """Health check and platform overview"""
    settings = get_settings()
    groq_service = get_groq_service()
    
    return {
        "status": "healthy",
        "platform": "Nocturnal Platform",
        "version": "1.0.0",
        "environment": settings.environment,
        "modules": {
            "finsight": {
                "enabled": settings.finsight_enabled,
                "description": "Financial data analysis and SEC EDGAR integration"
            },
            "archive": {
                "enabled": settings.archive_enabled,
                "description": "Academic research and synthesis platform"
            },
            "assistant": {
                "enabled": settings.assistant_enabled,
                "description": "R/SQL programming assistance"
            }
        },
        "groq_service": {
            "total_keys": len(groq_service.api_keys),
            "healthy_keys": sum(1 for k in groq_service.api_keys if k.is_healthy)
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    settings = get_settings()
    groq_service = get_groq_service()
    
    # Check Groq service health
    groq_status = groq_service.get_status()
    
    # Check database health
    # TODO: Add database health check
    
    # Check cache health
    # TODO: Add cache health check
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "groq": {
                "status": "healthy" if groq_status["healthy_keys"] > 0 else "unhealthy",
                "healthy_keys": groq_status["healthy_keys"],
                "total_keys": groq_status["total_keys"]
            },
            "database": {
                "status": "healthy",  # TODO: Implement actual check
                "url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "configured"
            },
            "cache": {
                "status": "healthy",  # TODO: Implement actual check
                "url": settings.redis_url
            }
        },
        "request_stats": request_stats
    }


@app.get("/status")
async def get_status():
    """Get detailed platform status"""
    settings = get_settings()
    groq_service = get_groq_service()
    
    return {
        "platform_status": "operational",
        "environment": settings.environment,
        "modules": {
            "finsight": {
                "enabled": settings.finsight_enabled,
                "endpoints": ["/api/v1/finsight/*"]
            },
            "archive": {
                "enabled": settings.archive_enabled,
                "endpoints": ["/api/v1/archive/*"]
            },
            "assistant": {
                "enabled": settings.assistant_enabled,
                "endpoints": ["/api/v1/assistant/*"]
            },
            "unified": {
                "enabled": True,
                "endpoints": ["/api/v1/unified/*"]
            }
        },
        "groq_service": groq_service.get_status(),
        "request_stats": request_stats,
        "timestamp": datetime.now().isoformat()
    }


# Include routers
if settings.finsight_enabled:
    app.include_router(finsight.router, prefix="/api/v1/finsight", tags=["FinSight"])

if settings.archive_enabled:
    app.include_router(archive.router, prefix="/api/v1/archive", tags=["Archive"])

if settings.assistant_enabled:
    app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["Assistant"])

# Always include unified router
app.include_router(unified.router, prefix="/api/v1/unified", tags=["Unified"])


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
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
    logger.error(
        "Unhandled exception",
        exception=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )


# Dependency for getting settings
def get_app_settings() -> Settings:
    """Dependency to get application settings"""
    return get_settings()


# Dependency for getting Groq service
def get_app_groq_service():
    """Dependency to get Groq service"""
    return get_groq_service()


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        workers=settings.server_workers,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
