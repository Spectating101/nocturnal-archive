"""
Advanced analytics and monitoring service
"""

import structlog
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Advanced analytics and monitoring service"""
    
    def __init__(self):
        self.metrics = {
            'requests': defaultdict(int),
            'response_times': defaultdict(list),
            'errors': defaultdict(int),
            'user_activity': defaultdict(int),
            'api_usage': defaultdict(int),
            'performance': defaultdict(list)
        }
        self.start_time = datetime.utcnow()
    
    def record_request(self, endpoint: str, method: str, user_id: Optional[str] = None):
        """Record API request"""
        key = f"{method}:{endpoint}"
        self.metrics['requests'][key] += 1
        
        if user_id:
            self.metrics['user_activity'][user_id] += 1
        
        logger.info(
            "Request recorded",
            endpoint=endpoint,
            method=method,
            user_id=user_id
        )
    
    def record_response_time(self, endpoint: str, response_time: float):
        """Record response time for an endpoint"""
        self.metrics['response_times'][endpoint].append(response_time)
        
        # Keep only last 1000 measurements
        if len(self.metrics['response_times'][endpoint]) > 1000:
            self.metrics['response_times'][endpoint] = self.metrics['response_times'][endpoint][-1000:]
    
    def record_error(self, endpoint: str, error_type: str, error_message: str):
        """Record API error"""
        key = f"{endpoint}:{error_type}"
        self.metrics['errors'][key] += 1
        
        logger.error(
            "Error recorded",
            endpoint=endpoint,
            error_type=error_type,
            error_message=error_message
        )
    
    def record_api_usage(self, api_name: str, tokens_used: int = 0, cost: float = 0.0):
        """Record external API usage"""
        self.metrics['api_usage'][api_name] += 1
        
        if api_name not in self.metrics['performance']:
            self.metrics['performance'][api_name] = {
                'total_tokens': 0,
                'total_cost': 0.0,
                'calls': 0
            }
        
        self.metrics['performance'][api_name]['total_tokens'] += tokens_used
        self.metrics['performance'][api_name]['total_cost'] += cost
        self.metrics['performance'][api_name]['calls'] += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        
        # Calculate average response times
        avg_response_times = {}
        for endpoint, times in self.metrics['response_times'].items():
            if times:
                avg_response_times[endpoint] = {
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        
        # Calculate error rates
        total_requests = sum(self.metrics['requests'].values())
        error_rates = {}
        for error_key, count in self.metrics['errors'].items():
            error_rates[error_key] = {
                'count': count,
                'rate': count / total_requests if total_requests > 0 else 0
            }
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
        return {
            'summary': {
                'uptime_hours': round(uptime_hours, 2),
                'total_requests': total_requests,
                'total_errors': sum(self.metrics['errors'].values()),
                'active_users': len(self.metrics['user_activity']),
                'timestamp': datetime.utcnow().isoformat()
            },
            'response_times': avg_response_times,
            'error_rates': error_rates,
            'api_usage': dict(self.metrics['api_usage']),
            'performance': dict(self.metrics['performance']),
            'top_endpoints': self._get_top_endpoints(),
            'top_users': self._get_top_users()
        }
    
    def _get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        endpoint_counts = defaultdict(int)
        
        for request_key, count in self.metrics['requests'].items():
            method, endpoint = request_key.split(':', 1)
            endpoint_counts[endpoint] += count
        
        return [
            {'endpoint': endpoint, 'requests': count}
            for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    def _get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by activity"""
        return [
            {'user_id': user_id, 'requests': count}
            for user_id, count in sorted(self.metrics['user_activity'].items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for monitoring"""
        
        # Get current minute metrics
        current_time = datetime.utcnow()
        minute_ago = current_time - timedelta(minutes=1)
        
        # This would typically query a time-series database
        # For now, return current metrics
        return {
            'timestamp': current_time.isoformat(),
            'requests_per_minute': sum(self.metrics['requests'].values()) // max(1, int((current_time - self.start_time).total_seconds() / 60)),
            'errors_per_minute': sum(self.metrics['errors'].values()) // max(1, int((current_time - self.start_time).total_seconds() / 60)),
            'active_connections': len(self.metrics['user_activity']),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage()
        }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def _get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage information"""
        try:
            import psutil
            return {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    async def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        
        metrics_data = self.get_metrics_summary()
        
        if format == 'json':
            return json.dumps(metrics_data, indent=2)
        elif format == 'csv':
            return self._export_csv(metrics_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self, metrics_data: Dict[str, Any]) -> str:
        """Export metrics as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary
        writer.writerow(['Metric', 'Value'])
        for key, value in metrics_data['summary'].items():
            writer.writerow([key, value])
        
        # Write response times
        writer.writerow([])
        writer.writerow(['Endpoint', 'Average Response Time', 'Min', 'Max', 'Count'])
        for endpoint, stats in metrics_data['response_times'].items():
            writer.writerow([endpoint, stats['average'], stats['min'], stats['max'], stats['count']])
        
        return output.getvalue()


# Global analytics instance
analytics_service = AnalyticsService()
