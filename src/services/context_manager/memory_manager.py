"""
Memory Manager - Long-term memory management
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """Memory manager for long-term interaction storage."""
    
    def __init__(self):
        self.memories = []
        logger.info("Memory Manager initialized")
    
    async def store_interaction(self, interaction: Dict[str, Any]):
        """Store interaction in memory."""
        self.memories.append(interaction)
    
    async def search_interactions(self, query: str, limit: int = 10) -> List[Dict]:
        """Search interactions in memory."""
        results = []
        query_lower = query.lower()
        
        for memory in self.memories:
            if (query_lower in memory.get("user_input", "").lower() or 
                query_lower in memory.get("response", "").lower()):
                results.append({
                    "content": f"User: {memory.get('user_input', '')}",
                    "relevance_score": 0.7,
                    "metadata": memory
                })
        
        return results[:limit]
    
    async def get_entry_count(self) -> int:
        """Get total number of memory entries."""
        return len(self.memories)
