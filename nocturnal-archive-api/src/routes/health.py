"""
Health check endpoint
"""

import structlog
from datetime import datetime
from fastapi import APIRouter, Depends
from typing import Dict

from src.config.settings import Settings, get_settings
from src.models.response import HealthResponse

logger = structlog.get_logger(__name__)
router = APIRouter()


async def check_service_health(service_name: str) -> str:
    """Check health of a specific service"""
    try:
        if service_name == "openalex":
            # Check OpenAlex API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.openalex.org/works?search=test", timeout=5.0)
                return "ok" if response.status_code == 200 else "slow"
        
        elif service_name == "openai":
            # Check OpenAI API
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            # Simple test - just check if we can create a client
            return "ok"
        
        elif service_name == "database":
            # Check database connection
            # TODO: Implement actual database health check
            return "ok"
        
        else:
            return "unknown"
    
    except Exception as e:
        logger.warning(f"Service {service_name} health check failed", error=str(e))
        return "down"


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint"""
    
    # Check all services
    services = {}
    issues = []
    
    for service in ["openalex", "openai", "database"]:
        status = await check_service_health(service)
        services[service] = status
        
        if status == "down":
            issues.append(f"{service} service is down")
        elif status == "slow":
            issues.append(f"{service} service is slow")
    
    # Determine overall status
    if any(status == "down" for status in services.values()):
        overall_status = "down"
    elif any(status == "slow" for status in services.values()):
        overall_status = "degraded"
    else:
        overall_status = "ok"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services,
        version="1.0.0",
        issues=issues if issues else None
    )
