"""
Product-based authentication middleware
Separates Cite-Agent and FinSight API access controls
"""

from enum import Enum
from typing import Optional
from fastapi import HTTPException
import structlog
from datetime import date

logger = structlog.get_logger(__name__)

class ProductType(Enum):
    """Product types with different access patterns"""
    CITE_AGENT = "cite_agent"      # Students/researchers - agent-mediated access
    FINSIGHT = "finsight"          # Developers - direct API access
    ADMIN = "admin"                # Internal use

class Tier(Enum):
    """Pricing tiers for both products"""
    # Cite-Agent tiers (daily limits, agent-only)
    STUDENT = "student"            # $9/mo: 100 FinSight calls/day via agent
    CITE_PRO = "cite_pro"          # $29/mo: 500 FinSight calls/day via agent

    # FinSight tiers (monthly limits, direct API)
    FREE = "free"                  # $0: 1,000 calls/month
    STARTER = "starter"            # $29/mo: 10,000 calls/month
    FINSIGHT_PRO = "finsight_pro"  # $99/mo: 100,000 calls/month
    ENTERPRISE = "enterprise"      # Custom: unlimited

    # Admin
    ADMIN = "admin"                # Unlimited everything

# Tier limits configuration
TIER_LIMITS = {
    # Cite-Agent (daily FinSight limits, agent-mediated only)
    Tier.STUDENT: {
        "daily_finsight": 100,
        "direct_api": False,
        "archive_access": True,
        "llm_access": True
    },
    Tier.CITE_PRO: {
        "daily_finsight": 500,
        "direct_api": False,
        "archive_access": True,
        "llm_access": True
    },

    # FinSight (monthly limits, direct API only)
    Tier.FREE: {
        "monthly_calls": 1000,
        "direct_api": True,
        "archive_access": False,
        "llm_access": False
    },
    Tier.STARTER: {
        "monthly_calls": 10000,
        "direct_api": True,
        "archive_access": False,
        "llm_access": False
    },
    Tier.FINSIGHT_PRO: {
        "monthly_calls": 100000,
        "direct_api": True,
        "archive_access": False,
        "llm_access": False
    },
    Tier.ENTERPRISE: {
        "monthly_calls": -1,  # unlimited
        "direct_api": True,
        "archive_access": False,
        "llm_access": False
    },

    # Admin
    Tier.ADMIN: {
        "monthly_calls": -1,
        "daily_finsight": -1,
        "direct_api": True,
        "archive_access": True,
        "llm_access": True
    }
}

async def get_key_info(conn, api_key: str) -> Optional[dict]:
    """
    Get API key info from database or in-memory storage

    Note: Currently using in-memory keys from APIKeyAuthMiddleware
    Database lookup will be enabled once keys are properly migrated
    """

    # TEMPORARY: Use in-memory key info from APIKeyAuthMiddleware
    # This matches the existing demo-key-123 setup
    IN_MEMORY_KEYS = {
        "demo-key-123": {
            "id": "demo-key-123",
            "key_type": "cite_agent",  # Default: Cite-Agent product
            "tier": "student",         # Student tier (100 FinSight calls/day)
            "user_id": "demo-user",
            "is_active": True
        },
        "pro-key-456": {
            "id": "pro-key-456",
            "key_type": "cite_agent",
            "tier": "cite_pro",        # Pro tier (500 FinSight calls/day)
            "user_id": "pro-user",
            "is_active": True
        }
    }

    # Check in-memory first
    if api_key in IN_MEMORY_KEYS:
        return IN_MEMORY_KEYS[api_key]

    # TODO: Database lookup for production keys
    # Currently database uses key_hash, not plaintext keys
    # Need to either:
    # 1. Hash the api_key and look up by key_hash, OR
    # 2. Store plaintext keys (less secure but simpler)
    #
    # For now, return None for unknown keys (will fail auth)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                key_id as id,
                key_type,
                tier,
                user_id,
                is_active
            FROM api_keys
            WHERE key_id = $1 AND is_active = TRUE
            """,
            api_key
        )

        if not row:
            return None

        return {
            "id": row["id"],
            "key_type": row["key_type"] or "cite_agent",
            "tier": row["tier"] or "student",
            "user_id": row["user_id"],
            "is_active": row["is_active"]
        }
    except Exception as e:
        logger.error("Failed to fetch API key info from database", error=str(e))
        return None

async def get_daily_finsight_usage(conn, api_key_id: int, today: date) -> int:
    """Get FinSight usage count for today (for Cite-Agent users)"""
    try:
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) as count
            FROM api_usage
            WHERE api_key_id = $1
              AND DATE(timestamp) = $2
              AND endpoint LIKE '/v1/finance%'
            """,
            api_key_id,
            today
        )
        return row["count"] if row else 0
    except Exception as e:
        logger.error("Failed to fetch daily usage", error=str(e))
        return 0

async def get_monthly_usage(conn, api_key_id: int, year: int, month: int) -> int:
    """Get API usage count for current month (for FinSight users)"""
    try:
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) as count
            FROM api_usage
            WHERE api_key_id = $1
              AND EXTRACT(YEAR FROM timestamp) = $2
              AND EXTRACT(MONTH FROM timestamp) = $3
            """,
            api_key_id,
            year,
            month
        )
        return row["count"] if row else 0
    except Exception as e:
        logger.error("Failed to fetch monthly usage", error=str(e))
        return 0

async def log_api_usage(
    conn,
    api_key_id: int,
    endpoint: str,
    response_time_ms: int = None,
    status_code: int = 200
):
    """Log API usage for rate limiting and billing"""
    try:
        await conn.execute(
            """
            INSERT INTO api_usage (api_key_id, endpoint, response_time_ms, status_code)
            VALUES ($1, $2, $3, $4)
            """,
            api_key_id,
            endpoint,
            response_time_ms,
            status_code
        )
    except Exception as e:
        logger.warning("Failed to log API usage", error=str(e))
        # Don't fail the request if logging fails

async def check_product_access(
    conn,
    api_key: str,
    endpoint: str,
    request_source: Optional[str] = None  # "agent" or "direct"
) -> dict:
    """
    Check if API key has access to requested endpoint

    Returns:
        dict with key_info if access granted

    Raises:
        HTTPException if access denied
    """

    # Get key info
    key_info = await get_key_info(conn, api_key)
    if not key_info:
        logger.warning("Invalid API key attempted", api_key=api_key[:10])
        raise HTTPException(401, "Invalid API key")

    try:
        product = ProductType(key_info["key_type"])
        tier = Tier(key_info["tier"])
    except ValueError as e:
        logger.error("Invalid product type or tier",
                    key_type=key_info["key_type"],
                    tier=key_info["tier"])
        raise HTTPException(500, "Invalid API key configuration")

    tier_config = TIER_LIMITS[tier]

    # Admin bypass
    if tier == Tier.ADMIN:
        logger.debug("Admin access granted", endpoint=endpoint)
        return key_info

    # ========================
    # FinSight API Endpoints
    # ========================
    if endpoint.startswith("/v1/finance"):

        # Cite-Agent users: agent-mediated only with daily limits
        if product == ProductType.CITE_AGENT:

            # Check if direct API access (not allowed)
            if request_source != "agent":
                logger.warning(
                    "Cite-Agent key attempted direct FinSight access",
                    api_key=api_key[:10],
                    endpoint=endpoint
                )
                raise HTTPException(
                    403,
                    {
                        "error": "direct_access_forbidden",
                        "message": "Direct FinSight API access not allowed with Cite-Agent subscription.",
                        "suggestion": "Use cite-agent CLI for financial queries, or upgrade to FinSight API for direct access.",
                        "upgrade_url": "https://finsight-api.com/pricing"
                    }
                )

            # Check daily quota
            today = date.today()
            daily_usage = await get_daily_finsight_usage(conn, key_info["id"], today)
            daily_limit = tier_config["daily_finsight"]

            if daily_usage >= daily_limit:
                logger.info(
                    "Cite-Agent daily FinSight quota exceeded",
                    api_key=api_key[:10],
                    usage=daily_usage,
                    limit=daily_limit
                )
                raise HTTPException(
                    429,
                    {
                        "error": "quota_exceeded",
                        "message": f"FinSight daily quota exceeded ({daily_limit} calls/day).",
                        "current_usage": daily_usage,
                        "limit": daily_limit,
                        "suggestion": "Upgrade to FinSight API for higher limits (1,000-100,000 calls/month).",
                        "upgrade_url": "https://finsight-api.com/pricing"
                    }
                )

            logger.debug(
                "Cite-Agent FinSight access granted",
                api_key=api_key[:10],
                usage=daily_usage,
                limit=daily_limit
            )
            return key_info

        # FinSight users: direct API with monthly limits
        elif product == ProductType.FINSIGHT:

            # Check monthly quota
            now = date.today()
            monthly_usage = await get_monthly_usage(conn, key_info["id"], now.year, now.month)
            monthly_limit = tier_config["monthly_calls"]

            # -1 = unlimited
            if monthly_limit > 0 and monthly_usage >= monthly_limit:
                logger.info(
                    "FinSight monthly quota exceeded",
                    api_key=api_key[:10],
                    usage=monthly_usage,
                    limit=monthly_limit,
                    tier=tier.value
                )
                raise HTTPException(
                    429,
                    {
                        "error": "quota_exceeded",
                        "message": f"Monthly quota exceeded ({monthly_limit} calls).",
                        "current_usage": monthly_usage,
                        "limit": monthly_limit,
                        "tier": tier.value,
                        "suggestion": "Upgrade to higher tier for more calls.",
                        "upgrade_url": "https://finsight-api.com/pricing"
                    }
                )

            logger.debug(
                "FinSight API access granted",
                api_key=api_key[:10],
                usage=monthly_usage,
                limit=monthly_limit if monthly_limit > 0 else "unlimited",
                tier=tier.value
            )
            return key_info

    # ========================
    # Archive API Endpoints
    # ========================
    elif endpoint.startswith("/api"):

        if tier_config.get("archive_access"):
            logger.debug("Archive access granted", api_key=api_key[:10])
            return key_info
        else:
            logger.warning(
                "Archive access denied for FinSight key",
                api_key=api_key[:10]
            )
            raise HTTPException(
                403,
                {
                    "error": "access_forbidden",
                    "message": "Archive API not included with FinSight subscription.",
                    "suggestion": "Archive API is available in Cite-Agent plans.",
                    "info_url": "https://cite-agent.com"
                }
            )

    # ========================
    # LLM Query Endpoints
    # ========================
    elif endpoint.startswith("/query"):

        if tier_config.get("llm_access"):
            logger.debug("LLM access granted", api_key=api_key[:10])
            return key_info
        else:
            logger.warning(
                "LLM access denied for FinSight key",
                api_key=api_key[:10]
            )
            raise HTTPException(
                403,
                {
                    "error": "access_forbidden",
                    "message": "LLM query endpoint not included with FinSight subscription.",
                    "suggestion": "LLM features are available in Cite-Agent plans.",
                    "info_url": "https://cite-agent.com"
                }
            )

    # Default: allow (for other endpoints like /health, /docs, etc.)
    return key_info
