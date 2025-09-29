"""
API Calls Tool - HTTP API integration capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)

class APICallsTool:
    """HTTP API calls tool with authentication and error handling."""
    
    def __init__(self):
        logger.info("API Calls Tool initialized")
    
    async def execute(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute API call based on task description."""
        if not AIOHTTP_AVAILABLE:
            return {
                "status": "error",
                "error": "aiohttp not available. Install with: pip install aiohttp",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        url = context.get("url", "")
        method = context.get("method", "GET")
        headers = context.get("headers", {})
        data = context.get("data", None)
        
        if not url:
            return {
                "status": "error",
                "error": "URL is required for API calls",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    return {
                        "status": "success",
                        "url": url,
                        "method": method,
                        "status_code": response.status,
                        "response": response_data,
                        "headers": dict(response.headers),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"API call failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
