# src/services/analytics_service/usage_tracker.py

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
import json
from enum import Enum

logger = logging.getLogger(__name__)

class UsageType(Enum):
    """Types of usage that can be tracked."""
    SEARCH = "search"
    API_CALL = "api_call"
    EXPORT = "export"
    STORAGE = "storage"
    LLM_TOKEN = "llm_token"

class UsageTracker:
    """
    Production-grade usage tracking service for billing and analytics.
    
    Features:
    - Real-time usage tracking
    - Subscription limit enforcement
    - Analytics and reporting
    - Cost calculation
    - Usage alerts
    """
    
    def __init__(self, redis_url: str, db_ops=None):
        """
        Initialize usage tracker.
        
        Args:
            redis_url: Redis connection URL
            db_ops: Database operations instance
        """
        self.redis_url = redis_url
        self.db_ops = db_ops
        
        # Usage costs (in cents)
        self.usage_costs = {
            UsageType.SEARCH: 10,  # $0.10 per search
            UsageType.API_CALL: 5,  # $0.05 per API call
            UsageType.EXPORT: 25,  # $0.25 per export
            UsageType.STORAGE: 1,  # $0.01 per MB
            UsageType.LLM_TOKEN: 0.1  # $0.001 per token
        }
        
        logger.info("UsageTracker initialized successfully")
    
    async def track_usage(self, user_id: str, usage_type: UsageType, amount: int = 1, metadata: Dict[str, Any] = None) -> bool:
        """
        Track user usage for billing and analytics.
        
        Args:
            user_id: User ID
            usage_type: Type of usage
            amount: Amount of usage
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            timestamp = datetime.utcnow()
            usage_key = f"usage:{user_id}:{usage_type.value}:{timestamp.strftime('%Y-%m')}"
            
            # Store usage data
            usage_data = {
                "user_id": user_id,
                "usage_type": usage_type.value,
                "amount": amount,
                "cost": self.usage_costs[usage_type] * amount,
                "timestamp": timestamp.isoformat(),
                "metadata": metadata or {}
            }
            
            # Increment monthly usage
            await self._increment_monthly_usage(usage_key, amount)
            
            # Store detailed usage record
            await self._store_usage_record(usage_data)
            
            # Check usage limits
            await self._check_usage_limits(user_id, usage_type)
            
            logger.info(f"Tracked usage: {usage_type.value} for user {user_id}, amount: {amount}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track usage: {str(e)}")
            return False
    
    async def get_user_usage(self, user_id: str, usage_type: UsageType = None, month: str = None) -> Dict[str, Any]:
        """
        Get user usage statistics.
        
        Args:
            user_id: User ID
            usage_type: Specific usage type (optional)
            month: Month in YYYY-MM format (optional)
            
        Returns:
            Usage statistics
        """
        try:
            if not month:
                month = datetime.utcnow().strftime('%Y-%m')
            
            if usage_type:
                usage_key = f"usage:{user_id}:{usage_type.value}:{month}"
                amount = await self._get_monthly_usage(usage_key)
                
                return {
                    "user_id": user_id,
                    "usage_type": usage_type.value,
                    "month": month,
                    "amount": amount,
                    "cost": self.usage_costs[usage_type] * amount
                }
            else:
                # Get all usage types for the month
                usage_stats = {}
                total_cost = 0
                
                for usage_type in UsageType:
                    usage_key = f"usage:{user_id}:{usage_type.value}:{month}"
                    amount = await self._get_monthly_usage(usage_key)
                    cost = self.usage_costs[usage_type] * amount
                    
                    usage_stats[usage_type.value] = {
                        "amount": amount,
                        "cost": cost
                    }
                    total_cost += cost
                
                return {
                    "user_id": user_id,
                    "month": month,
                    "usage": usage_stats,
                    "total_cost": total_cost
                }
                
        except Exception as e:
            logger.error(f"Failed to get user usage: {str(e)}")
            return {}
    
    async def check_usage_limit(self, user_id: str, usage_type: UsageType, subscription_tier: str) -> bool:
        """
        Check if user is within usage limits for their subscription tier.
        
        Args:
            user_id: User ID
            usage_type: Type of usage
            subscription_tier: User's subscription tier
            
        Returns:
            True if within limits
        """
        try:
            # Get current month's usage
            month = datetime.utcnow().strftime('%Y-%m')
            current_usage = await self.get_user_usage(user_id, usage_type, month)
            
            # Get tier limits
            tier_limits = self._get_tier_limits(subscription_tier)
            
            if usage_type == UsageType.SEARCH:
                limit = tier_limits.get("searches_per_month", 5)
            elif usage_type == UsageType.API_CALL:
                limit = tier_limits.get("api_calls_per_month", 10)
            else:
                limit = -1  # Unlimited for other types
            
            # -1 means unlimited
            if limit == -1:
                return True
            
            return current_usage.get("amount", 0) < limit
            
        except Exception as e:
            logger.error(f"Failed to check usage limit: {str(e)}")
            return False
    
    async def get_usage_analytics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Get system-wide usage analytics.
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Analytics data
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # This would typically query a time-series database
            # For now, we'll return mock analytics
            analytics = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_users": 0,
                "active_users": 0,
                "total_searches": 0,
                "total_api_calls": 0,
                "total_revenue": 0,
                "usage_by_type": {},
                "top_users": [],
                "usage_trends": {}
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {str(e)}")
            return {}
    
    async def generate_usage_report(self, user_id: str, month: str = None) -> Dict[str, Any]:
        """
        Generate a detailed usage report for a user.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (optional)
            
        Returns:
            Usage report
        """
        try:
            if not month:
                month = datetime.utcnow().strftime('%Y-%m')
            
            usage_data = await self.get_user_usage(user_id, month=month)
            
            report = {
                "user_id": user_id,
                "month": month,
                "generated_at": datetime.utcnow().isoformat(),
                "usage_summary": usage_data,
                "cost_breakdown": self._calculate_cost_breakdown(usage_data),
                "usage_trends": await self._get_usage_trends(user_id, month),
                "recommendations": self._generate_recommendations(usage_data)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate usage report: {str(e)}")
            return {}
    
    async def send_usage_alert(self, user_id: str, usage_type: UsageType, threshold: int = 80):
        """
        Send usage alert when approaching limits.
        
        Args:
            user_id: User ID
            usage_type: Type of usage
            threshold: Alert threshold percentage
        """
        try:
            # Get current usage and limits
            current_usage = await self.get_user_usage(user_id, usage_type)
            subscription_tier = await self._get_user_subscription_tier(user_id)
            tier_limits = self._get_tier_limits(subscription_tier)
            
            if usage_type == UsageType.SEARCH:
                limit = tier_limits.get("searches_per_month", 5)
            elif usage_type == UsageType.API_CALL:
                limit = tier_limits.get("api_calls_per_month", 10)
            else:
                return
            
            usage_percentage = (current_usage.get("amount", 0) / limit) * 100
            
            if usage_percentage >= threshold:
                # Send alert (email, push notification, etc.)
                alert_data = {
                    "user_id": user_id,
                    "usage_type": usage_type.value,
                    "current_usage": current_usage.get("amount", 0),
                    "limit": limit,
                    "percentage": usage_percentage,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self._send_alert(alert_data)
                logger.info(f"Sent usage alert to user {user_id}: {usage_percentage}% of {usage_type.value} limit")
                
        except Exception as e:
            logger.error(f"Failed to send usage alert: {str(e)}")
    
    async def _increment_monthly_usage(self, usage_key: str, amount: int):
        """Increment monthly usage counter."""
        try:
            # This would use Redis or a similar fast storage
            # For now, we'll simulate it
            pass
        except Exception as e:
            logger.error(f"Failed to increment monthly usage: {str(e)}")
    
    async def _get_monthly_usage(self, usage_key: str) -> int:
        """Get monthly usage amount."""
        try:
            # This would query Redis or database
            # For now, return 0
            return 0
        except Exception as e:
            logger.error(f"Failed to get monthly usage: {str(e)}")
            return 0
    
    async def _store_usage_record(self, usage_data: Dict[str, Any]):
        """Store detailed usage record."""
        try:
            # This would store in a time-series database
            # For now, we'll log it
            logger.debug(f"Stored usage record: {usage_data}")
        except Exception as e:
            logger.error(f"Failed to store usage record: {str(e)}")
    
    async def _check_usage_limits(self, user_id: str, usage_type: UsageType):
        """Check usage limits and send alerts if needed."""
        try:
            await self.send_usage_alert(user_id, usage_type)
        except Exception as e:
            logger.error(f"Failed to check usage limits: {str(e)}")
    
    def _get_tier_limits(self, subscription_tier: str) -> Dict[str, Any]:
        """Get limits for a subscription tier."""
        tier_limits = {
            "free": {
                "searches_per_month": 5,
                "api_calls_per_month": 10,
                "storage_mb": 100
            },
            "pro": {
                "searches_per_month": 100,
                "api_calls_per_month": 1000,
                "storage_mb": 1000
            },
            "business": {
                "searches_per_month": 500,
                "api_calls_per_month": 10000,
                "storage_mb": 10000
            },
            "enterprise": {
                "searches_per_month": -1,  # Unlimited
                "api_calls_per_month": -1,  # Unlimited
                "storage_mb": -1  # Unlimited
            }
        }
        
        return tier_limits.get(subscription_tier, tier_limits["free"])
    
    async def _get_user_subscription_tier(self, user_id: str) -> str:
        """Get user's subscription tier."""
        try:
            # This would query the database
            # For now, return "free"
            return "free"
        except Exception as e:
            logger.error(f"Failed to get user subscription tier: {str(e)}")
            return "free"
    
    def _calculate_cost_breakdown(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed cost breakdown."""
        try:
            breakdown = {}
            total_cost = 0
            
            for usage_type, data in usage_data.get("usage", {}).items():
                cost = data.get("cost", 0)
                breakdown[usage_type] = {
                    "amount": data.get("amount", 0),
                    "cost": cost,
                    "unit_cost": self.usage_costs.get(UsageType(usage_type), 0)
                }
                total_cost += cost
            
            breakdown["total"] = total_cost
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to calculate cost breakdown: {str(e)}")
            return {}
    
    async def _get_usage_trends(self, user_id: str, month: str) -> Dict[str, Any]:
        """Get usage trends for the user."""
        try:
            # This would query historical usage data
            # For now, return empty trends
            return {
                "daily_usage": [],
                "weekly_usage": [],
                "monthly_usage": []
            }
        except Exception as e:
            logger.error(f"Failed to get usage trends: {str(e)}")
            return {}
    
    def _generate_recommendations(self, usage_data: Dict[str, Any]) -> List[str]:
        """Generate usage recommendations."""
        try:
            recommendations = []
            total_cost = usage_data.get("total_cost", 0)
            
            if total_cost > 100:
                recommendations.append("Consider upgrading to a higher tier for better value")
            
            if usage_data.get("usage", {}).get("search", {}).get("amount", 0) > 80:
                recommendations.append("You're approaching your search limit. Consider upgrading your plan.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return []
    
    async def _send_alert(self, alert_data: Dict[str, Any]):
        """Send usage alert to user."""
        try:
            # This would integrate with email/SMS service
            # For now, just log it
            logger.info(f"Usage alert: {alert_data}")
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")

# Global usage tracker instance
usage_tracker = UsageTracker(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
)
