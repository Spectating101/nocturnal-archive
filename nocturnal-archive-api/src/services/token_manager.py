"""
Production-ready token budget management system
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import structlog
import redis.asyncio as redis
from fastapi import HTTPException, status

logger = structlog.get_logger(__name__)

class TokenBudget:
    """Production-ready token budget manager"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Token budget configurations
        self.budgets = {
            "daily": 500_000,      # 500K tokens per day
            "hourly": 25_000,      # 25K tokens per hour
            "minute": 6_000,       # 6K tokens per minute (Groq limit)
            "per_request": 2_000   # 2K tokens per request
        }
        
        # Model-specific token costs (rough estimates)
        self.model_costs = {
            "llama-3.3-70b-versatile": {"input": 1.0, "output": 1.0},
            "llama-3.1-8b-instant": {"input": 0.1, "output": 0.1},
            "gpt-3.5-turbo": {"input": 0.5, "output": 0.5},
            "gpt-4": {"input": 1.5, "output": 1.5}
        }
    
    def _get_time_key(self, period: str) -> str:
        """Generate Redis key for time-based tracking"""
        now = datetime.utcnow()
        
        if period == "daily":
            return f"tokens:daily:{now.strftime('%Y-%m-%d')}"
        elif period == "hourly":
            return f"tokens:hourly:{now.strftime('%Y-%m-%d-%H')}"
        elif period == "minute":
            return f"tokens:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
        else:
            raise ValueError(f"Invalid period: {period}")
    
    def _get_user_key(self, user_id: str, period: str) -> str:
        """Generate Redis key for user-specific tracking"""
        time_key = self._get_time_key(period)
        return f"tokens:user:{user_id}:{time_key}"
    
    async def _get_current_usage(self, key: str) -> int:
        """Get current token usage for a key"""
        usage = await self.redis.get(key)
        return int(usage) if usage else 0
    
    async def _increment_usage(self, key: str, tokens: int, ttl: int) -> int:
        """Increment token usage atomically"""
        pipe = self.redis.pipeline()
        pipe.incrby(key, tokens)
        pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]
    
    def estimate_tokens(self, text: str, model: str = "llama-3.3-70b-versatile") -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for most models
        base_tokens = len(text) // 4
        
        # Apply model-specific multiplier
        if model in self.model_costs:
            multiplier = self.model_costs[model]["input"]
            return int(base_tokens * multiplier)
        
        return base_tokens
    
    async def check_budget(self, user_id: str, estimated_tokens: int, model: str = "llama-3.3-70b-versatile") -> Tuple[bool, Dict[str, int]]:
        """Check if user has enough token budget"""
        budget_info = {}
        
        # Check all time periods
        for period, limit in self.budgets.items():
            if period == "per_request":
                continue  # Checked separately
            
            key = self._get_user_key(user_id, period)
            current_usage = await self._get_current_usage(key)
            
            # Calculate TTL for the key
            if period == "daily":
                ttl = 86400  # 24 hours
            elif period == "hourly":
                ttl = 3600   # 1 hour
            elif period == "minute":
                ttl = 60     # 1 minute
            
            budget_info[period] = {
                "limit": limit,
                "used": current_usage,
                "remaining": max(0, limit - current_usage),
                "ttl": ttl
            }
            
            # Check if budget would be exceeded
            if current_usage + estimated_tokens > limit:
                logger.warning(
                    "Token budget exceeded",
                    user_id=user_id,
                    period=period,
                    limit=limit,
                    current_usage=current_usage,
                    estimated_tokens=estimated_tokens
                )
                return False, budget_info
        
        # Check per-request limit
        if estimated_tokens > self.budgets["per_request"]:
            logger.warning(
                "Per-request token limit exceeded",
                user_id=user_id,
                estimated_tokens=estimated_tokens,
                limit=self.budgets["per_request"]
            )
            return False, budget_info
        
        return True, budget_info
    
    async def reserve_tokens(self, user_id: str, estimated_tokens: int, model: str = "llama-3.3-70b-versatile") -> bool:
        """Reserve tokens for a request"""
        # Check budget first
        can_proceed, budget_info = await self.check_budget(user_id, estimated_tokens, model)
        
        if not can_proceed:
            return False
        
        # Reserve tokens in all time periods
        for period in ["daily", "hourly", "minute"]:
            key = self._get_user_key(user_id, period)
            ttl = budget_info[period]["ttl"]
            
            await self._increment_usage(key, estimated_tokens, ttl)
        
        logger.info(
            "Tokens reserved",
            user_id=user_id,
            tokens=estimated_tokens,
            model=model
        )
        
        return True
    
    async def record_actual_usage(self, user_id: str, actual_tokens: int, model: str = "llama-3.3-70b-versatile"):
        """Record actual token usage (for adjustment)"""
        # This could be used to adjust reservations based on actual usage
        # For now, we'll just log it
        logger.info(
            "Actual token usage recorded",
            user_id=user_id,
            tokens=actual_tokens,
            model=model
        )
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """Get comprehensive usage statistics for a user"""
        stats = {}
        
        for period in ["daily", "hourly", "minute"]:
            key = self._get_user_key(user_id, period)
            current_usage = await self._get_current_usage(key)
            
            stats[period] = {
                "limit": self.budgets[period],
                "used": current_usage,
                "remaining": max(0, self.budgets[period] - current_usage),
                "percentage": (current_usage / self.budgets[period]) * 100
            }
        
        return stats
    
    async def reset_user_budget(self, user_id: str, period: str = "daily"):
        """Reset user's token budget for a specific period"""
        key = self._get_user_key(user_id, period)
        await self.redis.delete(key)
        
        logger.info(
            "Token budget reset",
            user_id=user_id,
            period=period
        )

# Global token budget manager
token_budget = None

async def get_token_budget() -> TokenBudget:
    """Get the global token budget manager"""
    global token_budget
    if token_budget is None:
        redis_client = redis.Redis(host="localhost", port=6379, db=2)
        token_budget = TokenBudget(redis_client)
    return token_budget

# Token budget decorator
def require_token_budget(estimated_tokens: int, model: str = "llama-3.3-70b-versatile"):
    """Decorator to check token budget before processing request"""
    async def decorator(request: Request, call_next):
        # Get user from request state (set by auth middleware)
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("user_id", "anonymous")
        
        budget_manager = await get_token_budget()
        
        # Check and reserve tokens
        can_proceed = await budget_manager.reserve_tokens(user_id, estimated_tokens, model)
        
        if not can_proceed:
            # Get usage stats for error response
            stats = await budget_manager.get_usage_stats(user_id)
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "token_budget_exceeded",
                        "message": "Token budget exceeded. Please try again later.",
                        "estimated_tokens": estimated_tokens,
                        "model": model,
                        "usage_stats": stats
                    }
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Record actual usage (if available in response)
        if hasattr(response, "token_usage"):
            await budget_manager.record_actual_usage(user_id, response.token_usage, model)
        
        return response
    
    return decorator
