"""
Analytics and monitoring endpoints
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from src.config.settings import Settings, get_settings
from src.services.analytics import analytics_service

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/analytics/metrics")
async def get_metrics(
    format: str = Query("json", description="Output format (json, csv)"),
    settings: Settings = Depends(get_settings)
):
    """Get comprehensive analytics metrics"""
    
    try:
        if format == "json":
            return analytics_service.get_metrics_summary()
        elif format == "csv":
            csv_data = await analytics_service.export_metrics("csv")
            return {"data": csv_data, "format": "csv"}
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_format", "message": "Format must be 'json' or 'csv'"}
            )
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "metrics_failed", "message": "Failed to retrieve metrics"}
        )


@router.get("/analytics/real-time")
async def get_real_time_metrics(
    settings: Settings = Depends(get_settings)
):
    """Get real-time metrics for monitoring"""
    
    try:
        return await analytics_service.get_real_time_metrics()
    
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "realtime_metrics_failed", "message": "Failed to retrieve real-time metrics"}
        )


@router.get("/analytics/performance")
async def get_performance_metrics(
    settings: Settings = Depends(get_settings)
):
    """Get performance-specific metrics"""
    
    try:
        metrics = analytics_service.get_metrics_summary()
        
        return {
            "performance": {
                "response_times": metrics.get("response_times", {}),
                "api_usage": metrics.get("api_usage", {}),
                "performance_stats": metrics.get("performance", {}),
                "top_endpoints": metrics.get("top_endpoints", []),
                "timestamp": metrics["summary"]["timestamp"]
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "performance_metrics_failed", "message": "Failed to retrieve performance metrics"}
        )


@router.get("/analytics/errors")
async def get_error_metrics(
    settings: Settings = Depends(get_settings)
):
    """Get error metrics and analysis"""
    
    try:
        metrics = analytics_service.get_metrics_summary()
        
        return {
            "errors": {
                "error_rates": metrics.get("error_rates", {}),
                "total_errors": metrics["summary"]["total_errors"],
                "error_percentage": (metrics["summary"]["total_errors"] / max(1, metrics["summary"]["total_requests"])) * 100,
                "timestamp": metrics["summary"]["timestamp"]
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get error metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "error_metrics_failed", "message": "Failed to retrieve error metrics"}
        )


@router.get("/analytics/users")
async def get_user_metrics(
    settings: Settings = Depends(get_settings)
):
    """Get user activity metrics"""
    
    try:
        metrics = analytics_service.get_metrics_summary()
        
        return {
            "users": {
                "active_users": metrics["summary"]["active_users"],
                "top_users": metrics.get("top_users", []),
                "timestamp": metrics["summary"]["timestamp"]
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get user metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "user_metrics_failed", "message": "Failed to retrieve user metrics"}
        )


@router.post("/analytics/export")
async def export_metrics(
    format: str = Query("json", description="Export format (json, csv)"),
    settings: Settings = Depends(get_settings)
):
    """Export all metrics data"""
    
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_format", "message": "Format must be 'json' or 'csv'"}
            )
        
        exported_data = await analytics_service.export_metrics(format)
        
        return {
            "data": exported_data,
            "format": format,
            "timestamp": analytics_service.get_metrics_summary()["summary"]["timestamp"]
        }
    
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "export_failed", "message": "Failed to export metrics"}
        )
