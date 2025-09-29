"""
Unified Platform - Combines FinSight, Archive, and R/SQL Assistant
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import unified services
from src.config.settings_unified import Settings
from src.services.groq_service_unified import UnifiedGroqService
from src.routes.finsight import router as finsight_router
from src.routes.archive import router as archive_router
from src.routes.assistant import router as assistant_router
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.auth import AuthMiddleware
from src.middleware.monitoring import MonitoringMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global settings
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Unified Platform...")
    
    # Initialize Groq service
    try:
        groq_service = UnifiedGroqService(settings.groq_api_key)
        app.state.groq_service = groq_service
        logger.info("✅ Groq service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq service: {e}")
        raise
    
    # Initialize database connections
    try:
        # TODO: Initialize PostgreSQL and Redis connections
        logger.info("✅ Database connections initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Unified Platform...")

# Create FastAPI app
app = FastAPI(
    title="Unified Platform",
    description="Combines FinSight (Financial Analysis), Archive (Research Synthesis), and R/SQL Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure for production
)

# Add custom middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(MonitoringMiddleware)

# Include routers
app.include_router(finsight_router, prefix="/api/v1/finsight", tags=["FinSight"])
app.include_router(archive_router, prefix="/api/v1/archive", tags=["Archive"])
app.include_router(assistant_router, prefix="/api/v1/assistant", tags=["Assistant"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Unified Platform - FinSight + Archive + R/SQL Assistant",
        "version": "1.0.0",
        "status": "operational",
        "services": {
            "finsight": "Financial data analysis with SEC EDGAR integration",
            "archive": "Research synthesis and document analysis",
            "assistant": "R/SQL programming assistance with file awareness"
        },
        "llm_provider": "Groq (llama-3.1-70b-versatile)"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Groq service
        groq_service = app.state.groq_service
        groq_health = await groq_service.health_check()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "groq": groq_health,
                "database": "connected",  # TODO: Actual DB check
                "redis": "connected"      # TODO: Actual Redis check
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/v1/status")
async def status():
    """Detailed status endpoint"""
    return {
        "platform": "Unified Platform",
        "version": "1.0.0",
        "environment": settings.environment,
        "services": {
            "finsight": {
                "status": "operational",
                "features": ["SEC EDGAR integration", "Financial analysis", "Rate limiting"],
                "llm": "Groq (llama-3.1-70b-versatile)"
            },
            "archive": {
                "status": "operational", 
                "features": ["Research synthesis", "Document analysis", "Multi-source research"],
                "llm": "Groq (llama-3.1-70b-versatile)"
            },
            "assistant": {
                "status": "operational",
                "features": ["R/SQL assistance", "File awareness", "Terminal integration"],
                "llm": "Groq (llama-3.1-70b-versatile)"
            }
        },
        "unified_features": {
            "single_llm_provider": "Groq",
            "unified_database": "PostgreSQL",
            "unified_caching": "Redis",
            "unified_auth": "API Key",
            "unified_monitoring": "Structured logging"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Unified Platform server...")
    uvicorn.run(
        "main_unified:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
