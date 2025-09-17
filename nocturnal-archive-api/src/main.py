"""
Nocturnal Archive API - Main FastAPI application
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
import sentry_sdk

from src.config.settings import get_settings
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.tracing import TracingMiddleware
from src.routes import health, search, format, synthesize
from src.utils.logger import setup_logging

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize Sentry
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(auto_enabling_instrumentations=False)],
        traces_sample_rate=0.1,
        environment=settings.environment,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Nocturnal Archive API", version="1.0.0")
    
    # Initialize services here if needed
    # await initialize_services()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nocturnal Archive API")


# Create FastAPI app
app = FastAPI(
    title="Nocturnal Archive API",
    description="API-first backend for academic research. Find, format, and synthesize academic papers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.environment == "development" else ["api.nocturnal-archive.com"]
)

app.add_middleware(TracingMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        exception=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "trace_id": getattr(request.state, "trace_id", None)
        }
    )


# Include routers
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(format.router, prefix="/api", tags=["Format"])
app.include_router(synthesize.router, prefix="/api", tags=["Synthesis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nocturnal Archive API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
