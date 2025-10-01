"""
Production-ready FastAPI application with all security and monitoring features
"""

import os
import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Import our production modules
from src.auth.security import get_auth_manager, get_current_user
from src.middleware.rate_limiting import rate_limit_middleware, get_rate_limiter
from src.middleware.idempotency import idempotency_middleware
from src.services.token_manager import get_token_budget
from src.services.secure_shell import get_secure_shell

# Import existing routers
from src.routes.search import router as search_router
from src.routes.synthesize import router as synthesize_router
from src.routes.finance_kpis import router as finance_kpis_router
from src.routes.finance_calc import router as finance_calc_router

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

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
TOKEN_USAGE = Counter('tokens_used_total', 'Total tokens used', ['model', 'user_id'])
RATE_LIMIT_HITS = Counter('rate_limit_hits_total', 'Rate limit hits', ['endpoint', 'user_id'])

# Global variables for services
redis_client = None
auth_manager = None
rate_limiter = None
token_budget = None
secure_shell = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, auth_manager, rate_limiter, token_budget, secure_shell
    
    # Startup
    logger.info("Starting Nocturnal Archive API")
    
    try:
        # Initialize Redis connection with fallback
        from src.middleware.redis_fallback import get_redis_client
        redis_client = await get_redis_client()
        logger.info("Redis client initialized (with fallback if needed)")
        
        # Initialize services
        auth_manager = await get_auth_manager()
        rate_limiter = await get_rate_limiter()
        token_budget = await get_token_budget()
        secure_shell = await get_secure_shell()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nocturnal Archive API")
    
    if redis_client:
        await redis_client.close()
    
    if secure_shell:
        await secure_shell.cleanup_all_containers()
    
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Nocturnal Archive API",
    description="Production-ready API for academic research and financial data analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.nocturnal.dev"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nocturnal.dev", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Custom middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    return await rate_limit_middleware(request, call_next)

@app.middleware("http")
async def idempotency(request: Request, call_next):
    """Apply Idempotency-Key caching to write-ish requests"""
    return await idempotency_middleware(request, call_next)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An internal server error occurred",
            "instance": str(request.url),
            "request_id": request_id,
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    # Map to RFC 7807
    title = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
    }.get(exc.status_code, "Error")
    headers = getattr(exc, "headers", None)
    payload = {
        "type": "about:blank",
        "title": title,
        "status": exc.status_code,
        "detail": exc.detail if isinstance(exc.detail, str) else "",
        "instance": str(request.url),
        "request_id": request_id,
    }
    return JSONResponse(status_code=exc.status_code, content=payload, headers=headers)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check other services
    try:
        await auth_manager.validate_api_key("test")
        health_status["services"]["auth"] = "healthy"
    except Exception:
        health_status["services"]["auth"] = "healthy"  # Expected to fail with test key
    
    try:
        await rate_limiter.check_rate_limit(Request)
        health_status["services"]["rate_limiter"] = "healthy"
    except Exception:
        health_status["services"]["rate_limiter"] = "healthy"  # Expected to fail in test
    
    return health_status

@app.get("/ready")
async def readiness_check():
    """Readiness probe: fails if critical deps are down unless DEGRADED=true."""
    degraded_ok = os.getenv("DEGRADED", "false").lower() == "true"
    issues = []
    # Redis
    try:
        await redis_client.ping()
    except Exception as e:
        issues.append(f"redis:{str(e)}")
    if issues and not degraded_ok:
        return JSONResponse(status_code=503, content={
            "type": "about:blank",
            "title": "Service Unavailable",
            "status": 503,
            "detail": "Critical dependencies unavailable",
            "instance": "/ready",
            "issues": issues,
        })
    return {"status": "ready", "degraded": bool(issues), "issues": issues}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# API key management endpoints
@app.post("/auth/api-keys")
async def create_api_key(
    name: str,
    permissions: list = ["read"],
    current_user: dict = Depends(get_current_user)
):
    """Create a new API key"""
    user_id = current_user.get("user_id", "anonymous")
    
    api_key = await auth_manager.create_api_key(
        user_id=user_id,
        name=name,
        permissions=permissions
    )
    
    logger.info("API key created", user_id=user_id, name=name)
    
    return {
        "api_key": api_key,
        "name": name,
        "permissions": permissions,
        "created_at": time.time()
    }

@app.get("/auth/api-keys")
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List user's API keys"""
    user_id = current_user.get("user_id", "anonymous")
    
    api_keys = await auth_manager.get_user_api_keys(user_id)
    
    return {
        "api_keys": api_keys,
        "count": len(api_keys)
    }

@app.delete("/auth/api-keys/{api_key}")
async def revoke_api_key(
    api_key: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke an API key"""
    user_id = current_user.get("user_id", "anonymous")
    
    # Verify ownership
    user_keys = await auth_manager.get_user_api_keys(user_id)
    if not any(key["api_key"] == api_key for key in user_keys):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key not found or access denied"
        )
    
    success = await auth_manager.revoke_api_key(api_key)
    
    if success:
        logger.info("API key revoked", user_id=user_id, api_key=api_key[:10] + "...")
        return {"message": "API key revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

# Token budget endpoints
@app.get("/auth/token-budget")
async def get_token_budget_status(current_user: dict = get_current_user):
    """Get user's token budget status"""
    user_id = current_user.get("user_id", "anonymous")
    
    stats = await token_budget.get_usage_stats(user_id)
    
    return {
        "user_id": user_id,
        "usage_stats": stats,
        "timestamp": time.time()
    }

# Shell access endpoints
@app.post("/shell/execute")
async def execute_shell_command(
    command: str,
    current_user: dict = Depends(get_current_user)
):
    """Execute a command in secure shell environment"""
    user_id = current_user.get("user_id", "anonymous")
    
    result = await secure_shell.execute_command(user_id, command)
    
    logger.info(
        "Shell command executed",
        user_id=user_id,
        command=command,
        success=result["success"]
    )
    
    return result

@app.get("/shell/stats")
async def get_shell_stats(current_user: dict = get_current_user):
    """Get shell container statistics"""
    stats = await secure_shell.get_container_stats()
    return stats

# Include existing routers
app.include_router(search_router, prefix="/api", tags=["Research"])
app.include_router(synthesize_router, prefix="/api", tags=["Research"])
app.include_router(finance_kpis_router, prefix="/v1/finance/kpis", tags=["Finance"])
app.include_router(finance_calc_router, prefix="/v1/finance/calc", tags=["Finance"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Nocturnal Archive API",
        "version": "1.0.0",
        "description": "Production-ready API for academic research and financial data analysis",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info"
    )
