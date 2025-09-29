"""
Entity Tracker - Entity and relationship extraction
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EntityTracker:
    """Entity tracker for extracting entities and relationships."""
    
    def __init__(self):
        logger.info("Entity Tracker initialized")
    
    async def extract_entities(self, text: str) -> List[str]:
        """Extract entities from text."""
        # Simple entity extraction based on capitalization and patterns
        entities = []
        
        # Extract capitalized words (potential proper nouns)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.extend(capitalized_words)
        
        # Extract quoted strings
        quoted_strings = re.findall(r'"([^"]*)"', text)
        entities.extend(quoted_strings)
        
        # Remove duplicates and return
        return list(set(entities))
    
    async def extract_relationships(self, user_input: str, response: str) -> List[Dict]:
        """Extract relationships from interaction."""
        relationships = []
        
        # Simple relationship extraction based on keywords
        text = user_input + " " + response
        
        # Look for relationship patterns
        if "is a" in text.lower():
            relationships.append({
                "source": "entity1",
                "target": "entity2", 
                "type": "is_a",
                "confidence": 0.8
            })
        
        if "has" in text.lower():
            relationships.append({
                "source": "entity1",
                "target": "entity2",
                "type": "has",
                "confidence": 0.7
            })
        
        return relationships
