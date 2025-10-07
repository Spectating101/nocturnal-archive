"""
Knowledge Graph - Entity relationship management
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

class KnowledgeGraph:
    """Knowledge graph for entity relationship management."""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        logger.info("Knowledge Graph initialized")
    
    async def add_interaction(self, interaction_id: str, user_input: str, response: str, 
                            entities: List[str], relationships: List[Dict]):
        """Add interaction to knowledge graph."""
        # Add entities as nodes
        for entity in entities:
            if entity not in self.nodes:
                self.nodes[entity] = {
                    "id": entity,
                    "type": "entity",
                    "created_at": _utc_now(),
                    "interactions": []
                }
            self.nodes[entity]["interactions"].append(interaction_id)
        
        # Add relationships as edges
        for relationship in relationships:
            self.edges.append({
                "source": relationship.get("source"),
                "target": relationship.get("target"),
                "relationship": relationship.get("type"),
                "interaction_id": interaction_id,
                "created_at": _utc_now()
            })
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Perform semantic search in knowledge graph."""
        # Simple keyword-based search
        results = []
        query_lower = query.lower()
        
        for node_id, node_data in self.nodes.items():
            if query_lower in node_id.lower():
                results.append({
                    "content": f"Entity: {node_id}",
                    "relevance_score": 0.8,
                    "metadata": node_data
                })
        
        return results[:limit]
    
    async def get_node_count(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)
    
    async def get_edge_count(self) -> int:
        """Get total number of edges."""
        return len(self.edges)
