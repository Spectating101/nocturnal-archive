"""
Advanced Context Manager - Sophisticated context and memory management
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from .knowledge_graph import KnowledgeGraph
from .memory_manager import MemoryManager
from .entity_tracker import EntityTracker

logger = logging.getLogger(__name__)

class AdvancedContextManager:
    """
    Advanced context manager with sophisticated memory and knowledge management.
    
    Features:
    - Long-term memory persistence
    - Knowledge graph construction and traversal
    - Entity relationship tracking
    - Context-aware conversation management
    - Semantic search and retrieval
    - Cross-session context continuity
    """
    
    def __init__(self, redis_url: str = None):
        self.knowledge_graph = KnowledgeGraph()
        self.memory_manager = MemoryManager()
        self.entity_tracker = EntityTracker()
        
        # Active contexts
        self.active_contexts: Dict[str, Dict] = {}
        
        # Context history
        self.context_history: List[Dict] = []
        
        logger.info("Advanced Context Manager initialized")
    
    async def process_interaction(self, user_input: str, response: str, 
                                session_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Process an interaction and update context.
        
        Args:
            user_input: User's input
            response: System's response
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Context processing result
        """
        try:
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Extract entities and relationships
            entities = await self.entity_tracker.extract_entities(user_input)
            relationships = await self.entity_tracker.extract_relationships(user_input, response)
            
            # Update knowledge graph
            await self.knowledge_graph.add_interaction(
                interaction_id, user_input, response, entities, relationships
            )
            
            # Store in memory
            memory_entry = {
                "interaction_id": interaction_id,
                "session_id": session_id,
                "user_id": user_id,
                "user_input": user_input,
                "response": response,
                "entities": entities,
                "relationships": relationships,
                "timestamp": timestamp,
                "context_metadata": await self._extract_context_metadata(user_input, response)
            }
            
            await self.memory_manager.store_interaction(memory_entry)
            
            # Update active context
            if session_id:
                await self._update_session_context(session_id, memory_entry)
            
            logger.info(f"Processed interaction {interaction_id}")
            
            return {
                "status": "success",
                "interaction_id": interaction_id,
                "entities_extracted": len(entities),
                "relationships_found": len(relationships),
                "context_updated": True,
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def retrieve_relevant_context(self, query: str, session_id: str = None, 
                                      user_id: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Search query
            session_id: Session identifier
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            Relevant context information
        """
        try:
            # Semantic search in knowledge graph
            graph_results = await self.knowledge_graph.semantic_search(query, limit)
            
            # Memory-based search
            memory_results = await self.memory_manager.search_interactions(query, limit)
            
            # Session-specific context
            session_context = None
            if session_id and session_id in self.active_contexts:
                session_context = self.active_contexts[session_id]
            
            # Combine and rank results
            combined_context = await self._combine_context_results(
                graph_results, memory_results, session_context, query
            )
            
            return {
                "status": "success",
                "query": query,
                "relevant_context": combined_context,
                "sources": {
                    "knowledge_graph": len(graph_results),
                    "memory": len(memory_results),
                    "session": 1 if session_context else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get current session context."""
        if session_id not in self.active_contexts:
            return {
                "status": "not_found",
                "message": "Session not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        context = self.active_contexts[session_id]
        return {
            "status": "success",
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def create_session_context(self, session_id: str, user_id: str = None, 
                                   initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new session context."""
        context = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "interactions": [],
            "entities": set(),
            "topics": set(),
            "context_data": initial_context or {}
        }
        
        self.active_contexts[session_id] = context
        
        logger.info(f"Created session context {session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def update_session_context(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update session context."""
        if session_id not in self.active_contexts:
            return {
                "status": "not_found",
                "message": "Session not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        context = self.active_contexts[session_id]
        context.update(updates)
        context["last_updated"] = datetime.utcnow()
        
        return {
            "status": "success",
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _update_session_context(self, session_id: str, interaction: Dict[str, Any]):
        """Update session context with new interaction."""
        if session_id not in self.active_contexts:
            await self.create_session_context(session_id)
        
        context = self.active_contexts[session_id]
        context["interactions"].append(interaction)
        context["entities"].update(interaction.get("entities", []))
        context["last_updated"] = datetime.utcnow()
    
    async def _extract_context_metadata(self, user_input: str, response: str) -> Dict[str, Any]:
        """Extract metadata from interaction."""
        return {
            "input_length": len(user_input),
            "response_length": len(response),
            "input_type": "question" if "?" in user_input else "statement",
            "response_type": "answer" if "?" in user_input else "information",
            "complexity_score": len(user_input.split()) / 10,  # Simple complexity metric
            "topics": await self._extract_topics(user_input + " " + response)
        }
    
    async def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        # Simple topic extraction based on keywords
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            "technology": ["code", "programming", "software", "tech", "computer"],
            "science": ["research", "study", "experiment", "data", "analysis"],
            "business": ["company", "market", "finance", "strategy", "management"],
            "education": ["learn", "teach", "student", "course", "knowledge"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    async def _combine_context_results(self, graph_results: List, memory_results: List, 
                                     session_context: Dict, query: str) -> List[Dict]:
        """Combine and rank context results."""
        combined = []
        
        # Add knowledge graph results
        for result in graph_results:
            combined.append({
                "source": "knowledge_graph",
                "relevance_score": result.get("relevance_score", 0.5),
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {})
            })
        
        # Add memory results
        for result in memory_results:
            combined.append({
                "source": "memory",
                "relevance_score": result.get("relevance_score", 0.5),
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {})
            })
        
        # Add session context
        if session_context:
            combined.append({
                "source": "session",
                "relevance_score": 0.8,  # High relevance for current session
                "content": f"Current session context: {len(session_context.get('interactions', []))} interactions",
                "metadata": {"session_id": session_context.get("session_id")}
            })
        
        # Sort by relevance score
        combined.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return combined
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24):
        """Clean up old context data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean up active contexts
        sessions_to_remove = []
        for session_id, context in self.active_contexts.items():
            if context["last_updated"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_contexts[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old contexts")
    
    async def get_context_statistics(self) -> Dict[str, Any]:
        """Get context management statistics."""
        return {
            "active_sessions": len(self.active_contexts),
            "total_interactions": len(self.context_history),
            "knowledge_graph_nodes": await self.knowledge_graph.get_node_count(),
            "knowledge_graph_edges": await self.knowledge_graph.get_edge_count(),
            "memory_entries": await self.memory_manager.get_entry_count(),
            "timestamp": datetime.utcnow().isoformat()
        }
