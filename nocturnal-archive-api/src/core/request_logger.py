"""
Basic request logging for demo value proof and monitoring
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional, List
from fastapi import Request

logger = logging.getLogger(__name__)


def _hash_key(key: str) -> str:
    """Hash API key for safe logging (first 12 chars of SHA256)"""
    return hashlib.sha256(key.encode()).hexdigest()[:12]

class RequestLogger:
    """Simple request logger for tracking API usage and performance"""
    
    @staticmethod
    def log_request(
        request: Request,
        endpoint: str,
        duration_ms: int,
        status_code: int,
        user_key: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log request details for monitoring and analytics
        
        Args:
            request: FastAPI request object
            endpoint: API endpoint called
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            user_key: API key or user identifier
            additional_data: Additional data to log (e.g., citation IDs)
        """
        # Extract key info
        ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        
        # Hash user key for privacy
        key_hash = "unknown"
        if user_key:
            key_hash = _hash_key(user_key)
        
        # Build log entry
        log_data = {
            "timestamp": time.time(),
            "method": method,
            "path": path,
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "ip": ip,
            "key_hash": key_hash,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Add additional data if provided
        if additional_data:
            log_data.update(additional_data)
        
        # Log based on status code
        if status_code >= 400:
            logger.warning(f"API request failed: {log_data}")
        else:
            logger.info(f"API request: {log_data}")
    
    @staticmethod
    def log_qa_request(
        request: Request,
        query: str,
        duration_ms: int,
        status_code: int,
        citations: Optional[list] = None,
        user_key: Optional[str] = None
    ):
        """
        Specialized logging for Q&A requests
        
        Args:
            request: FastAPI request object
            query: User query
            duration_ms: Request duration
            status_code: HTTP status code
            citations: List of citations returned
            user_key: API key or user identifier
        """
        additional_data = {
            "query_length": len(query),
            "query_hash": hash(query) % 1000000,  # Simple hash for tracking
            "citations_count": len(citations) if citations else 0,
            "top_citation_ids": [c.get("id", "")[:20] for c in citations[:3]] if citations else []
        }
        
        RequestLogger.log_request(
            request=request,
            endpoint="qa_filings",
            duration_ms=duration_ms,
            status_code=status_code,
            user_key=user_key,
            additional_data=additional_data
        )
    
    @staticmethod
    def log_sentiment_request(
        request: Request,
        text: str,
        duration_ms: int,
        status_code: int,
        sentiment_result: Optional[Dict[str, Any]] = None,
        user_key: Optional[str] = None
    ):
        """
        Specialized logging for sentiment requests
        
        Args:
            request: FastAPI request object
            text: Input text
            duration_ms: Request duration
            status_code: HTTP status code
            sentiment_result: Sentiment analysis result
            user_key: API key or user identifier
        """
        additional_data = {
            "text_length": len(text),
            "text_hash": hash(text) % 1000000,  # Simple hash for tracking
            "sentiment_label": sentiment_result.get("label") if sentiment_result else None,
            "sentiment_score": sentiment_result.get("score") if sentiment_result else None
        }
        
        RequestLogger.log_request(
            request=request,
            endpoint="nlp_sentiment",
            duration_ms=duration_ms,
            status_code=status_code,
            user_key=user_key,
            additional_data=additional_data
        )
