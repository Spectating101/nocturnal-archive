"""
Nocturnal Archive API - Main FastAPI application
"""

import logging
import time
from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncGenerator, Optional

import structlog
from structlog.stdlib import LoggerFactory
from fastapi import APIRouter, FastAPI, Request, HTTPException
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
from src.middleware.api_auth import APIKeyAuthMiddleware
from src.middleware.security import SecurityMiddleware
from src.middleware.tracing import TracingMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.middleware.pilot_guards import PilotGuardsMiddleware
from src.middleware.admin_auth import AdminAuthMiddleware
from src.utils.resiliency import init_redis
from src import errors


def _configure_logging(log_level: str) -> None:
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Get settings and configure logging
settings = get_settings()
_configure_logging(settings.log_level)
logger = structlog.get_logger(__name__)

# Initialize optional dependencies
init_redis()

# Initialize job queue
try:
    from src.jobs.queue import init_job_queue
    init_job_queue()
except Exception as e:
    logger.warning("Job queue initialization skipped", error=str(e))


def _load_router(name: str) -> Optional[APIRouter]:
    """Best-effort import of a route module, logging and skipping on failure."""

    try:
        module = import_module(f"src.routes.{name}")
        router = getattr(module, "router", None)
        if router is None:
            logger.warning("Route module missing router attribute", module=name)
        return router
    except Exception as exc:  # pragma: no cover - diagnostic logging
        logger.warning("Route module unavailable", module=name, error=str(exc))
        return None

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
app.add_middleware(RequestIdMiddleware)
app.add_middleware(PilotGuardsMiddleware)
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions (auth errors, validation, etc.)"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        trace_id=getattr(request.state, "trace_id", "unknown")
    )

    detail_payload = exc.detail
    if not isinstance(detail_payload, dict):
        detail_payload = {
            "error": "authentication_error" if exc.status_code in (401, 403) else "http_error",
            "message": detail_payload,
        }

    body = {
        "detail": detail_payload,
        "request_id": getattr(request.state, "trace_id", "unknown"),
    }

    # Preserve legacy top-level keys for backward compatibility
    if "error" not in body and "error" in detail_payload:
        body["error"] = detail_payload["error"]
    if "message" not in body and "message" in detail_payload:
        body["message"] = detail_payload["message"]

    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
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


# Include routers (optional modules are skipped gracefully)
_routers = {
    name: _load_router(name)
    for name in (
        "auth",           # NEW: Authentication endpoints
        "query",          # NEW: Secure query proxy
        "downloads",      # NEW: Download tracking
        "accuracy",       # NEW: Accuracy/citation metrics
        "workflow",       # NEW: Workflow integration
        "simple_health",  # Simplified health without deps
        "search",
        "format",
        "synthesize",
        "analytics",
        "diagnostics",
        "finance",
        "finance_calc",
        "finance_kpis",
        "finance_reports",
        "finance_filings",
        "finance_segments",
        "finance_status",
        "admin",
        "jobs",
        "ops",
        "quota",
        "nlp",
        "telemetry",
        "papers_demo",
    )
}


def _include(name: str, **kwargs) -> None:
    router = _routers.get(name)
    if router is not None:
        app.include_router(router, **kwargs)


_include("auth", prefix="/api", tags=["Authentication"])       # NEW
_include("query", prefix="/api", tags=["Query"])             # NEW
_include("nocturnal", prefix="/api", tags=["Nocturnal"])     # NEW - Specialized Cite-Agent
_include("downloads", prefix="/api", tags=["Downloads"])     # NEW
_include("accuracy", prefix="/api", tags=["Accuracy"])       # NEW
_include("workflow", prefix="/api", tags=["Workflow"])       # NEW
_include("simple_health", prefix="/api/health", tags=["System"])
_include("search", prefix="/api", tags=["Search"])
_include("format", prefix="/api", tags=["Format"])
_include("synthesize", prefix="/api", tags=["Synthesis"])
_include("analytics", prefix="/api", tags=["Analytics"])
_include("diagnostics", prefix="/v1/diag", tags=["Diagnostics"])

# Versioned API routes
_include("health", prefix="/v1/api", tags=["System v1"])
_include("search", prefix="/v1/api", tags=["Search v1"])
_include("format", prefix="/v1/api", tags=["Format v1"])
_include("synthesize", prefix="/v1/api", tags=["Synthesis v1"])

# Finance synthesis (numeric grounding)
_include("finance", tags=["FinSight"])

_include("finance_calc", tags=["FinSight"])
_include("finance_kpis", prefix="/v1/finance", tags=["FinSight"])
_include("finance_reports", prefix="/v1/finance", tags=["FinSight"])
_include("finance_filings", prefix="/v1/finance", tags=["FinSight"])
_include("finance_segments", prefix="/v1/finance", tags=["FinSight"])
_include("finance_status", prefix="/v1/finance", tags=["FinSight"])
_include("admin", prefix="/v1/admin", tags=["Admin"])
_include("jobs", prefix="/v1/jobs", tags=["Jobs"])
_include("ops", prefix="/v1/ops", tags=["Operations"])
_include("quota", prefix="/v1/quota", tags=["Quota"])
_include("nlp", tags=["FinSight"])
_include("telemetry", prefix="/api", tags=["Telemetry"])

# Papers Demo API (public, frozen)
_include("papers_demo", tags=["Papers Demo"])

# RAG Q&A API (feature flag controlled)
if settings.enable_rag:
    qa_router = _load_router("qa")
    if qa_router is not None:
        app.include_router(qa_router, tags=["FinSight"])

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
        from src.engine.research_engine import sophisticated_engine, ADVANCED_ENGINE_AVAILABLE  # Lazy import to avoid circulars
        from src.utils.resiliency import redis_client

        issues = []

        if not ADVANCED_ENGINE_AVAILABLE or sophisticated_engine.enhanced_research is None:
            issues.append("advanced_engine_unavailable")

        if redis_client is None:
            issues.append("redis_unavailable")

        status = "ready" if not issues else "degraded"

        return {"status": status, "issues": issues or None}

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
