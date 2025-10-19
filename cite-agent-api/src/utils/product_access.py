"""
Product access utilities for checking API key permissions
Lightweight dependency injection for product separation
"""

from fastapi import Request, HTTPException, Header
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


async def check_finsight_access(
    request: Request,
    x_request_source: Optional[str] = Header(None, alias="X-Request-Source")
) -> dict:
    """
    FastAPI dependency to check FinSight API access

    This is a simplified version that reads from request.state
    (set by existing APIKeyAuthMiddleware)

    Full implementation will use product_auth.check_product_access()
    when database migrations are deployed

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

    # For now, just log the request source for analytics
    # Full product separation will be enforced after migration deployment
    if x_request_source:
        logger.debug(
            "FinSight request",
            api_key=api_key[:10],
            request_source=x_request_source,
            endpoint=request.url.path
        )

    # TODO: After migration deployed, integrate full product_auth check:
    # from src.middleware.product_auth import check_product_access
    # from src.database.connection import get_connection
    #
    # async with get_connection() as conn:
    #     key_info = await check_product_access(
    #         conn=conn,
    #         api_key=api_key,
    #         endpoint=request.url.path,
    #         request_source=x_request_source
    #     )
    #     return key_info

    # For now, return mock key_info
    return {
        "api_key": api_key,
        "request_source": x_request_source,
        "endpoint": request.url.path
    }


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
