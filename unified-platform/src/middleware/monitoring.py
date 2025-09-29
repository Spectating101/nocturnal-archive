"""
Monitoring middleware for Nocturnal Platform
Provides Prometheus metrics and request tracking
"""

import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime

logger = structlog.get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Monitoring and metrics middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        self.start_time = time.time()
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Get normalized endpoint name for metrics"""
        path = request.url.path
        
        # Normalize paths for metrics
        if path.startswith("/api/v1/finsight"):
            return "finsight"
        elif path.startswith("/api/v1/archive"):
            return "archive"
        elif path.startswith("/api/v1/assistant"):
            return "assistant"
        elif path.startswith("/api/v1/unified"):
            return "unified"
        elif path in ["/", "/health", "/status"]:
            return "system"
        else:
            return "unknown"
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = self._get_endpoint_name(request)
        method = request.method
        
        # Track request
        self.request_count[f"{method}_{endpoint}"] += 1
        
        try:
            # Process request
            response = await call_next(request)
            
            # Track duration
            duration = time.time() - start_time
            self.request_duration[f"{method}_{endpoint}"].append(duration)
            
            # Keep only last 1000 durations per endpoint
            if len(self.request_duration[f"{method}_{endpoint}"]) > 1000:
                self.request_duration[f"{method}_{endpoint}"] = self.request_duration[f"{method}_{endpoint}"][-1000:]
            
            # Track errors
            if response.status_code >= 400:
                self.error_count[f"{method}_{endpoint}_{response.status_code}"] += 1
            
            # Add monitoring headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Endpoint"] = endpoint
            
            return response
            
        except Exception as e:
            # Track exceptions
            duration = time.time() - start_time
            self.error_count[f"{method}_{endpoint}_exception"] += 1
            
            logger.error(
                "Request exception",
                endpoint=endpoint,
                method=method,
                duration=duration,
                exception=str(e),
                exc_info=True
            )
            
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        uptime = time.time() - self.start_time
        
        # Calculate average durations
        avg_durations = {}
        for endpoint, durations in self.request_duration.items():
            if durations:
                avg_durations[endpoint] = sum(durations) / len(durations)
        
        # Calculate total requests by module
        module_requests = defaultdict(int)
        for key, count in self.request_count.items():
            method, endpoint = key.split("_", 1)
            module_requests[endpoint] += count
        
        # Calculate error rates
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "uptime_human": f"{uptime/3600:.1f} hours",
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "requests_per_second": round(total_requests / uptime, 2) if uptime > 0 else 0,
            "module_requests": dict(module_requests),
            "endpoint_requests": dict(self.request_count),
            "average_durations": avg_durations,
            "error_breakdown": dict(self.error_count),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        metrics = self.get_metrics()
        lines = []
        
        # Uptime
        lines.append(f"nocturnal_platform_uptime_seconds {metrics['uptime_seconds']}")
        
        # Total requests
        lines.append(f"nocturnal_platform_requests_total {metrics['total_requests']}")
        
        # Module requests
        for module, count in metrics["module_requests"].items():
            lines.append(f'nocturnal_platform_module_requests_total{{module="{module}"}} {count}')
        
        # Endpoint requests
        for endpoint, count in metrics["endpoint_requests"].items():
            lines.append(f'nocturnal_platform_endpoint_requests_total{{endpoint="{endpoint}"}} {count}')
        
        # Average durations
        for endpoint, duration in metrics["average_durations"].items():
            lines.append(f'nocturnal_platform_request_duration_seconds{{endpoint="{endpoint}"}} {duration}')
        
        # Error counts
        for error_type, count in metrics["error_breakdown"].items():
            lines.append(f'nocturnal_platform_errors_total{{error_type="{error_type}"}} {count}')
        
        return "\n".join(lines) + "\n"
