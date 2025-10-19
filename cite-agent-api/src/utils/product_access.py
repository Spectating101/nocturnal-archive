"""
Product access utilities for checking API key permissions
Lightweight dependency injection for product separation
"""

from fastapi import Request, HTTPException, Header
from typing import Optional
import structlog
import os
import asyncpg

logger = structlog.get_logger(__name__)

# Feature flag for enforcement (can disable quickly if issues arise)
ENFORCE_PRODUCT_SEPARATION = os.getenv("ENFORCE_PRODUCT_SEPARATION", "true").lower() == "true"


async def _get_db_connection():
    """Get database connection (same as auth.py pattern)"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    try:
        return await asyncpg.connect(db_url)
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return None


async def check_finsight_access(
    request: Request,
    x_request_source: Optional[str] = Header(None, alias="X-Request-Source")
) -> dict:
    """
    FastAPI dependency to check FinSight API access

    With enforcement enabled, this checks:
    - API key validity
    - Product type (Cite-Agent vs FinSight)
    - Request source (agent-mediated vs direct API)
    - Rate limits (daily for Cite-Agent, monthly for FinSight)

    Args:
        request: FastAPI request object
        x_request_source: Optional header to indicate request source (e.g., "agent")

    Returns:
        dict: Key info if access granted

    Raises:
        HTTPException: If access denied
    """

    # Get API key from request state (set by APIKeyAuthMiddleware)
    api_key = getattr(request.state, "api_key", None)

    if not api_key:
        logger.warning("FinSight access attempt without API key")
        raise HTTPException(401, "API key required")

    # Log request for analytics
    logger.debug(
        "FinSight request",
        api_key=api_key[:10] if api_key else None,
        request_source=x_request_source,
        endpoint=request.url.path,
        enforcement_enabled=ENFORCE_PRODUCT_SEPARATION
    )

    # If enforcement disabled, allow all requests (backward compatible)
    if not ENFORCE_PRODUCT_SEPARATION:
        logger.info("Product separation enforcement disabled, allowing request")
        return {
            "api_key": api_key,
            "request_source": x_request_source,
            "endpoint": request.url.path
        }

    # Enable enforcement - check product access
    try:
        from src.middleware.product_auth import check_product_access

        conn = await _get_db_connection()
        if not conn:
            # Database unavailable - fail open for demo key, fail closed otherwise
            if api_key == "demo-key-123":
                logger.warning("Database unavailable, allowing demo key")
                return {"api_key": api_key, "request_source": x_request_source}
            else:
                logger.error("Database unavailable, blocking non-demo request")
                raise HTTPException(503, "Service temporarily unavailable")

        try:
            # Check product access with full enforcement
            key_info = await check_product_access(
                conn=conn,
                api_key=api_key,
                endpoint=request.url.path,
                request_source=x_request_source
            )
            return key_info
        finally:
            await conn.close()

    except HTTPException:
        # Re-raise HTTP exceptions (403, 429, etc.) from product_auth
        raise
    except Exception as e:
        # Unexpected error - log and fail gracefully
        logger.error("Product access check failed", error=str(e), api_key=api_key[:10])
        # Fail open for demo key to avoid breaking existing functionality
        if api_key == "demo-key-123":
            logger.warning("Enforcement error, allowing demo key as fallback")
            return {"api_key": api_key, "request_source": x_request_source}
        raise HTTPException(500, "Internal server error")


async def check_archive_access(request: Request) -> dict:
    """
    FastAPI dependency to check Archive API access

    Args:
        request: FastAPI request object

    Returns:
        dict: Key info if access granted

    Raises:
        HTTPException: If access denied
    """

    api_key = getattr(request.state, "api_key", None)

    if not api_key:
        logger.warning("Archive access attempt without API key")
        raise HTTPException(401, "API key required")

    logger.debug(
        "Archive request",
        api_key=api_key[:10],
        endpoint=request.url.path
    )

    return {
        "api_key": api_key,
        "endpoint": request.url.path
    }
