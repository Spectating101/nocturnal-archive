"""
Unified Groq Service for Nocturnal Platform
Replaces OpenAI, Anthropic, and other LLM providers across all modules
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import structlog
from groq import Groq, RateLimitError, APIError

logger = structlog.get_logger(__name__)


@dataclass
class GroqAPIKey:
    """Groq API key with usage tracking"""
    api_key: str
    daily_limit: int = 14400  # Free tier limit
    rate_limit: int = 30  # Requests per minute
    daily_usage: int = 0
    rate_usage: List[float] = None
    last_reset: datetime = None
    is_healthy: bool = True
    error_count: int = 0
    
    def __post_init__(self):
        if self.rate_usage is None:
            self.rate_usage = []
        if self.last_reset is None:
            self.last_reset = datetime.now()


class GroqService:
    """Unified Groq service with API key rotation and load balancing"""
    
    def __init__(self, api_keys: List[str], default_model: str = "llama-3.1-70b-versatile"):
        self.api_keys: List[GroqAPIKey] = []
        self.default_model = default_model
        self.request_stats = defaultdict(int)
        self.user_stats = defaultdict(lambda: {"requests": 0, "last_request": None})
        
        # Initialize API keys
        for key in api_keys:
            if key and key.strip():
                self.api_keys.append(GroqAPIKey(api_key=key.strip()))
        
        logger.info(f"Initialized Groq service with {len(self.api_keys)} API keys")
    
    def _cleanup_rate_usage(self, key: GroqAPIKey):
        """Remove old rate limit entries"""
        now = time.time()
        key.rate_usage = [timestamp for timestamp in key.rate_usage if now - timestamp < 60]
    
    def _reset_daily_usage(self, key: GroqAPIKey):
        """Reset daily usage if it's a new day"""
        now = datetime.now()
        if key.last_reset.date() < now.date():
            key.daily_usage = 0
            key.last_reset = now
            key.is_healthy = True
            key.error_count = 0
            logger.info(f"Reset daily usage for API key")
    
    def get_available_key(self) -> Optional[GroqAPIKey]:
        """Get an available API key with load balancing"""
        now = datetime.now()
        
        # Clean up and reset keys
        for key in self.api_keys:
            self._cleanup_rate_usage(key)
            self._reset_daily_usage(key)
        
        # Find healthy keys with capacity
        available_keys = []
        for key in self.api_keys:
            if (key.is_healthy and 
                key.daily_usage < key.daily_limit and 
                len(key.rate_usage) < key.rate_limit):
                available_keys.append(key)
        
        if not available_keys:
            logger.warning("No available API keys")
            return None
        
        # Load balance by selecting key with least usage
        selected_key = min(available_keys, key=lambda k: k.daily_usage)
        return selected_key
    
    def record_request(self, key: GroqAPIKey, success: bool = True):
        """Record a request for usage tracking"""
        now = time.time()
        key.rate_usage.append(now)
        key.daily_usage += 1
        
        if not success:
            key.error_count += 1
            if key.error_count >= 5:  # Mark unhealthy after 5 errors
                key.is_healthy = False
                logger.warning(f"Marked API key as unhealthy after {key.error_count} errors")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a chat completion request with automatic retry and key rotation"""
        
        model = model or self.default_model
        max_retries = 3
        
        for attempt in range(max_retries):
            key = self.get_available_key()
            if not key:
                raise Exception("No available API keys")
            
            try:
                # Track user stats
                if user_id:
                    self.user_stats[user_id]["requests"] += 1
                    self.user_stats[user_id]["last_request"] = datetime.now().isoformat()
                
                # Create Groq client
                client = Groq(api_key=key.api_key)
                
                # Make API call
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Record successful request
                self.record_request(key, success=True)
                self.request_stats[f"{model}_success"] += 1
                
                return {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "usage": response.usage.dict() if response.usage else None,
                    "api_key_used": key.api_key[:8] + "...",
                    "timestamp": datetime.now().isoformat()
                }
                
            except RateLimitError as e:
                logger.warning(f"Rate limit error with key {key.api_key[:8]}...: {e}")
                self.record_request(key, success=False)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Rate limit exceeded after {max_retries} attempts")
            
            except APIError as e:
                logger.error(f"API error with key {key.api_key[:8]}...: {e}")
                self.record_request(key, success=False)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"API error after {max_retries} attempts: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.record_request(key, success=False)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Unexpected error after {max_retries} attempts: {e}")
        
        raise Exception("All retry attempts failed")
    
    async def finsight_analysis(
        self,
        financial_data: str,
        analysis_type: str = "general",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized financial analysis using Groq"""
        
        system_prompt = """You are a financial analysis expert. Analyze the provided financial data and provide insights.
        
        Focus on:
        - Key financial metrics and trends
        - Risk assessment
        - Growth indicators
        - Comparative analysis
        - Regulatory compliance insights
        
        Provide clear, actionable insights with specific data points."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this {analysis_type} financial data:\n\n{financial_data}"}
        ]
        
        return await self.chat_completion(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=1500,
            user_id=user_id
        )
    
    async def research_synthesis(
        self,
        research_papers: List[Dict[str, Any]],
        synthesis_prompt: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized research synthesis using Groq"""
        
        # Format research papers
        papers_text = ""
        for i, paper in enumerate(research_papers[:10], 1):  # Limit to 10 papers
            papers_text += f"\n{i}. {paper.get('title', 'Unknown Title')}\n"
            papers_text += f"   Authors: {paper.get('authors', 'Unknown')}\n"
            papers_text += f"   Abstract: {paper.get('abstract', 'No abstract')[:500]}...\n"
        
        system_prompt = """You are a research synthesis expert. Analyze the provided research papers and create a comprehensive synthesis.
        
        Focus on:
        - Key findings and insights
        - Common themes and patterns
        - Contradictions or gaps
        - Future research directions
        - Practical applications
        
        Provide a well-structured synthesis with clear conclusions."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Synthesis prompt: {synthesis_prompt}\n\nResearch papers:\n{papers_text}"}
        ]
        
        return await self.chat_completion(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.4,
            max_tokens=2000,
            user_id=user_id
        )
    
    async def r_sql_assistance(
        self,
        question: str,
        context: str = "",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized R/SQL assistance using Groq"""
        
        system_prompt = """You are a helpful assistant for R and SQL programming. 
        
        Provide clear, concise answers with code examples when appropriate.
        Focus on practical solutions and best practices.
        
        For R questions:
        - Provide R code examples
        - Explain data manipulation, visualization, and analysis
        - Include package recommendations
        
        For SQL questions:
        - Provide SQL code examples
        - Explain query optimization
        - Include best practices for database design
        
        Always explain what the code does and provide context."""
        
        user_content = question
        if context:
            user_content = f"Context: {context}\n\nQuestion: {question}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return await self.chat_completion(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=1200,
            user_id=user_id
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status and statistics"""
        now = datetime.now()
        
        # Clean up and reset keys
        for key in self.api_keys:
            self._cleanup_rate_usage(key)
            self._reset_daily_usage(key)
        
        key_status = []
        for i, key in enumerate(self.api_keys):
            key_status.append({
                "index": i,
                "daily_usage": key.daily_usage,
                "daily_limit": key.daily_limit,
                "rate_usage": len(key.rate_usage),
                "rate_limit": key.rate_limit,
                "is_healthy": key.is_healthy,
                "error_count": key.error_count,
                "last_reset": key.last_reset.isoformat()
            })
        
        return {
            "service": "Groq Unified Service",
            "total_keys": len(self.api_keys),
            "healthy_keys": sum(1 for k in self.api_keys if k.is_healthy),
            "api_keys": key_status,
            "request_stats": dict(self.request_stats),
            "user_stats": dict(self.user_stats),
            "timestamp": now.isoformat()
        }


# Global instance
groq_service: Optional[GroqService] = None


def initialize_groq_service(api_keys: List[str], default_model: str = "llama-3.1-70b-versatile"):
    """Initialize the global Groq service"""
    global groq_service
    groq_service = GroqService(api_keys, default_model)
    logger.info("Groq service initialized globally")


def get_groq_service() -> GroqService:
    """Get the global Groq service instance"""
    if groq_service is None:
        raise Exception("Groq service not initialized. Call initialize_groq_service() first.")
    return groq_service
