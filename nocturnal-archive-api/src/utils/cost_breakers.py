"""
Cost and abuse breakers for API protection
"""

import time
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)

@dataclass
class UsageStats:
    """Usage statistics for an API key"""
    requests_today: int = 0
    llm_calls_today: int = 0
    spend_today: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)
    baseline_rps: float = 0.0
    baseline_spend: float = 0.0
    anomaly_count: int = 0
    last_anomaly: Optional[datetime] = None

class CostBreaker:
    """Cost and abuse protection"""
    
    def __init__(self):
        self.usage_stats: Dict[str, UsageStats] = {}
        self.global_daily_spend_limit = 1000.0  # $1000/day global limit
        self.per_key_daily_spend_limit = 100.0  # $100/day per key
        self.anomaly_threshold = 10.0  # 10x baseline spike
        self.anomaly_cooldown = 3600  # 1 hour cooldown
        
    def _get_or_create_stats(self, api_key: str) -> UsageStats:
        """Get or create usage stats for an API key"""
        if api_key not in self.usage_stats:
            self.usage_stats[api_key] = UsageStats()
        return self.usage_stats[api_key]
    
    def _reset_daily_stats(self, stats: UsageStats):
        """Reset daily statistics"""
        now = datetime.now()
        if now.date() > stats.last_reset.date():
            stats.requests_today = 0
            stats.llm_calls_today = 0
            stats.spend_today = 0.0
            stats.last_reset = now
            logger.info("Daily usage stats reset", api_key_hash=hash(api_key)[:8])
    
    def check_daily_spend_limit(self, api_key: str, estimated_cost: float = 0.0) -> tuple[bool, str]:
        """Check if API key has exceeded daily spend limit"""
        stats = self._get_or_create_stats(api_key)
        self._reset_daily_stats(stats)
        
        # Check per-key limit
        if stats.spend_today + estimated_cost > self.per_key_daily_spend_limit:
            logger.warning(
                "Per-key daily spend limit exceeded",
                api_key_hash=hash(api_key)[:8],
                current_spend=stats.spend_today,
                limit=self.per_key_daily_spend_limit
            )
            return False, f"Daily spend limit exceeded: ${stats.spend_today:.2f}/${self.per_key_daily_spend_limit:.2f}"
        
        # Check global limit
        global_spend = sum(s.spend_today for s in self.usage_stats.values())
        if global_spend + estimated_cost > self.global_daily_spend_limit:
            logger.warning(
                "Global daily spend limit exceeded",
                global_spend=global_spend,
                limit=self.global_daily_spend_limit
            )
            return False, f"Global spend limit exceeded: ${global_spend:.2f}/${self.global_daily_spend_limit:.2f}"
        
        return True, ""
    
    def check_anomaly_detection(self, api_key: str, current_rps: float, current_spend: float) -> tuple[bool, str]:
        """Check for anomalous usage patterns"""
        stats = self._get_or_create_stats(api_key)
        self._reset_daily_stats(stats)
        
        # Update baseline if not set
        if stats.baseline_rps == 0.0:
            stats.baseline_rps = current_rps
            stats.baseline_spend = current_spend
            return True, ""
        
        # Check for RPS anomaly
        if current_rps > stats.baseline_rps * self.anomaly_threshold:
            stats.anomaly_count += 1
            stats.last_anomaly = datetime.now()
            
            logger.warning(
                "RPS anomaly detected",
                api_key_hash=hash(api_key)[:8],
                current_rps=current_rps,
                baseline_rps=stats.baseline_rps,
                threshold=self.anomaly_threshold
            )
            return False, f"RPS anomaly detected: {current_rps:.1f} > {stats.baseline_rps * self.anomaly_threshold:.1f}"
        
        # Check for spend anomaly
        if current_spend > stats.baseline_spend * self.anomaly_threshold:
            stats.anomaly_count += 1
            stats.last_anomaly = datetime.now()
            
            logger.warning(
                "Spend anomaly detected",
                api_key_hash=hash(api_key)[:8],
                current_spend=current_spend,
                baseline_spend=stats.baseline_spend,
                threshold=self.anomaly_threshold
            )
            return False, f"Spend anomaly detected: ${current_spend:.2f} > ${stats.baseline_spend * self.anomaly_threshold:.2f}"
        
        # Check cooldown period
        if stats.last_anomaly and (datetime.now() - stats.last_anomaly).seconds < self.anomaly_cooldown:
            return False, f"Anomaly cooldown active: {(self.anomaly_cooldown - (datetime.now() - stats.last_anomaly).seconds)}s remaining"
        
        return True, ""
    
    def record_usage(self, api_key: str, cost: float = 0.0, llm_call: bool = False):
        """Record API usage"""
        stats = self._get_or_create_stats(api_key)
        self._reset_daily_stats(stats)
        
        stats.requests_today += 1
        stats.spend_today += cost
        
        if llm_call:
            stats.llm_calls_today += 1
        
        # Update baseline (exponential moving average)
        if stats.baseline_rps == 0.0:
            stats.baseline_rps = 1.0
            stats.baseline_spend = cost
        else:
            alpha = 0.1  # Smoothing factor
            stats.baseline_rps = alpha * 1.0 + (1 - alpha) * stats.baseline_rps
            stats.baseline_spend = alpha * cost + (1 - alpha) * stats.baseline_spend
    
    def get_usage_stats(self, api_key: str) -> Dict[str, Any]:
        """Get usage statistics for an API key"""
        stats = self._get_or_create_stats(api_key)
        self._reset_daily_stats(stats)
        
        return {
            "requests_today": stats.requests_today,
            "llm_calls_today": stats.llm_calls_today,
            "spend_today": stats.spend_today,
            "baseline_rps": stats.baseline_rps,
            "baseline_spend": stats.baseline_spend,
            "anomaly_count": stats.anomaly_count,
            "last_anomaly": stats.last_anomaly.isoformat() if stats.last_anomaly else None
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global usage statistics"""
        total_requests = sum(s.requests_today for s in self.usage_stats.values())
        total_spend = sum(s.spend_today for s in self.usage_stats.values())
        total_llm_calls = sum(s.llm_calls_today for s in self.usage_stats.values())
        
        return {
            "total_requests_today": total_requests,
            "total_spend_today": total_spend,
            "total_llm_calls_today": total_llm_calls,
            "active_keys": len(self.usage_stats),
            "global_spend_limit": self.global_daily_spend_limit,
            "per_key_spend_limit": self.per_key_daily_spend_limit
        }

# Global cost breaker instance
cost_breaker = CostBreaker()

def check_cost_limits(api_key: str, estimated_cost: float = 0.0) -> tuple[bool, str]:
    """Check cost limits for an API key"""
    return cost_breaker.check_daily_spend_limit(api_key, estimated_cost)

def check_anomaly(api_key: str, current_rps: float, current_spend: float) -> tuple[bool, str]:
    """Check for anomalous usage patterns"""
    return cost_breaker.check_anomaly_detection(api_key, current_rps, current_spend)

def record_usage(api_key: str, cost: float = 0.0, llm_call: bool = False):
    """Record API usage"""
    cost_breaker.record_usage(api_key, cost, llm_call)

def get_usage_stats(api_key: str) -> Dict[str, Any]:
    """Get usage statistics for an API key"""
    return cost_breaker.get_usage_stats(api_key)

def get_global_stats() -> Dict[str, Any]:
    """Get global usage statistics"""
    return cost_breaker.get_global_stats()
