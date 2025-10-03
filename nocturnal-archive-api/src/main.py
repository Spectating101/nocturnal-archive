"""
Nocturnal Archive API - Main FastAPI application
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
try:
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
from prometheus_fastapi_instrumentator import Instrumentator

from src.config.settings import get_settings
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.tracing import TracingMiddleware
from src.middleware.admin_auth import AdminAuthMiddleware
from src.middleware.api_auth import APIKeyAuthMiddleware
from src.middleware.security import SecurityMiddleware
from src.middleware.pilot_guards import PilotGuardsMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.routes import health, search, format, synthesize, analytics, diagnostics, finance, jobs, admin, papers_demo, finance_filings, finance_calc, finance_kpis, finance_segments, finance_status, finance_reports, nlp, qa, quota, ops
from src import errors
from src.utils.logger import setup_logging

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Initialize enterprise components
from src.utils.resiliency import init_redis
from src.jobs.queue import init_job_queue

# Initialize Redis and job queue
init_redis()
init_job_queue()

# Get settings
settings = get_settings()

# Initialize Sentry
if SENTRY_AVAILABLE and settings.sentry_dsn and settings.sentry_dsn != "your-sentry-dsn-here":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
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
    allowed_hosts=["*"] if settings.environment in {"development", "test"} else ["api.nocturnal-archive.com"]
)

app.add_middleware(SecurityMiddleware)
app.add_middleware(TracingMiddleware)
app.add_middleware(RequestIdMiddleware)  # Add request ID middleware
app.add_middleware(PilotGuardsMiddleware)  # Add pilot guards middleware
app.add_middleware(APIKeyAuthMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_hour=18000,  # 5 req/s = 18,000 per hour
    burst_limit=20,           # Allow burst of 20 requests
    per_ip_limit=50           # Global per-IP fuse: 50 req/s
)
app.add_middleware(AdminAuthMiddleware)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)


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
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(diagnostics.router, prefix="/v1/diag", tags=["Diagnostics"])

# Versioned API routes
app.include_router(health.router, prefix="/v1/api", tags=["System v1"])
app.include_router(search.router, prefix="/v1/api", tags=["Search v1"])
app.include_router(format.router, prefix="/v1/api", tags=["Format v1"])
app.include_router(synthesize.router, prefix="/v1/api", tags=["Synthesis v1"])

# New enterprise features
app.include_router(finance.router, tags=["Finance v1"])
app.include_router(jobs.router, tags=["Jobs v1"])
app.include_router(admin.router, tags=["Admin v1"])

# Papers Demo API (frozen)
app.include_router(papers_demo.router, tags=["Papers Demo"])

# FinSight API (commercial) - routers already have prefixes
app.include_router(finance_filings.router, tags=["FinSight"])
app.include_router(finance_calc.router, tags=["FinSight"])
app.include_router(finance_kpis.router, tags=["FinSight"])
app.include_router(finance_segments.router, tags=["FinSight"])
app.include_router(finance_status.router, tags=["FinSight"])
app.include_router(finance_reports.router, tags=["FinSight"])
app.include_router(nlp.router, tags=["FinSight"])

# RAG Q&A API (feature flag controlled)
if settings.enable_rag:
    app.include_router(qa.router, tags=["FinSight"])

# Quota management API (pilot mode)
app.include_router(quota.router, tags=["FinSight"])

# Operational endpoints (pilot mode)
app.include_router(ops.router, tags=["FinSight"])

# Integrated Analysis API (cross-system research + finance)
try:
    from src.routes.integrated_analysis import router as integrated_analysis_router
    app.include_router(integrated_analysis_router, tags=["Integrated Analysis"])
    logger.info("Integrated Analysis routes loaded successfully")
except ImportError as e:
    logger.warning(f"Integrated Analysis routes not available: {e}")

# Wire up structured error handling
errors.wire_errors(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nocturnal Archive API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/livez")
async def livez():
    """Kubernetes liveness probe - process is alive"""
    return {"status": "alive"}

@app.get("/readyz")
async def readyz():
    """Kubernetes readiness probe - dependencies are OK"""
    try:
        # Quick check if core services are responsive
        from src.engine.research_engine import sophisticated_engine
        
        # Check if engine is loaded
        if sophisticated_engine.enhanced_research is None:
            raise HTTPException(status_code=503, detail="Engine not ready")
        
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
