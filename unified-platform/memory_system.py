#!/usr/bin/env python3
"""
Memory System - Context Awareness for LLM Agent
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ConversationTurn:
    timestamp: str
    user_id: str
    conversation_id: str
    user_message: str
    agent_response: str
    tools_used: List[str]
    topics: List[str]
    entities: List[str]

@dataclass
class UserProfile:
    user_id: str
    style_preferences: Dict[str, Any]
    expertise_level: str  # "student", "expert", "executive"
    preferred_format: str  # "bullets", "narrative", "technical"
    verbosity: str  # "low", "medium", "high"
    last_updated: str

class MemorySystem:
    """Manages conversation memory and user context"""
    
    def __init__(self, memory_file: str = "memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "conversations": {},
            "user_profiles": {},
            "topic_relationships": {},
            "entity_context": {}
        }
    
    def _save_memory(self):
        """Save memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def add_conversation_turn(self, turn: ConversationTurn):
        """Add a new conversation turn to memory"""
        conv_id = turn.conversation_id
        
        if conv_id not in self.memory["conversations"]:
            self.memory["conversations"][conv_id] = {
                "turns": [],
                "created_at": turn.timestamp,
                "last_updated": turn.timestamp
            }
        
        self.memory["conversations"][conv_id]["turns"].append(asdict(turn))
        self.memory["conversations"][conv_id]["last_updated"] = turn.timestamp
        
        # Update topic relationships
        self._update_topic_relationships(turn)
        
        # Update entity context
        self._update_entity_context(turn)
        
        self._save_memory()
    
    def get_short_context(self, conversation_id: str, max_turns: int = 3) -> str:
        """Get recent conversation context"""
        if conversation_id not in self.memory["conversations"]:
            return ""
        
        turns = self.memory["conversations"][conversation_id]["turns"]
        recent_turns = turns[-max_turns:] if len(turns) > max_turns else turns
        
        context = []
        for turn in recent_turns:
            context.append(f"User: {turn['user_message']}")
            context.append(f"Agent: {turn['agent_response'][:200]}...")
        
        return "\n".join(context)
    
    def get_long_context(self, user_id: str, conversation_id: str, max_items: int = 5) -> Dict[str, Any]:
        """Get broader context including user profile and related topics"""
        context = {
            "user_profile": self.memory["user_profiles"].get(user_id, {}),
            "related_topics": self._get_related_topics(conversation_id),
            "entity_context": self._get_entity_context(conversation_id),
            "conversation_summary": self._get_conversation_summary(conversation_id)
        }
        
        return context
    
    def update_user_profile(self, user_id: str, profile: UserProfile):
        """Update user profile"""
        self.memory["user_profiles"][user_id] = asdict(profile)
        self._save_memory()
    
    def _update_topic_relationships(self, turn: ConversationTurn):
        """Update topic relationships based on conversation"""
        for topic in turn.topics:
            if topic not in self.memory["topic_relationships"]:
                self.memory["topic_relationships"][topic] = {
                    "related_topics": [],
                    "frequency": 0,
                    "last_mentioned": turn.timestamp
                }
            
            self.memory["topic_relationships"][topic]["frequency"] += 1
            self.memory["topic_relationships"][topic]["last_mentioned"] = turn.timestamp
            
            # Add related topics from the same turn
            for other_topic in turn.topics:
                if other_topic != topic and other_topic not in self.memory["topic_relationships"][topic]["related_topics"]:
                    self.memory["topic_relationships"][topic]["related_topics"].append(other_topic)
    
    def _update_entity_context(self, turn: ConversationTurn):
        """Update entity context"""
        for entity in turn.entities:
            if entity not in self.memory["entity_context"]:
                self.memory["entity_context"][entity] = {
                    "mentions": [],
                    "context": [],
                    "last_mentioned": turn.timestamp
                }
            
            self.memory["entity_context"][entity]["mentions"].append({
                "timestamp": turn.timestamp,
                "conversation_id": turn.conversation_id,
                "context": turn.user_message
            })
            self.memory["entity_context"][entity]["last_mentioned"] = turn.timestamp
    
    def _get_related_topics(self, conversation_id: str) -> List[str]:
        """Get topics related to current conversation"""
        if conversation_id not in self.memory["conversations"]:
            return []
        
        turns = self.memory["conversations"][conversation_id]["turns"]
        all_topics = []
        for turn in turns:
            all_topics.extend(turn.get("topics", []))
        
        # Get related topics
        related = []
        for topic in set(all_topics):
            if topic in self.memory["topic_relationships"]:
                related.extend(self.memory["topic_relationships"][topic]["related_topics"])
        
        return list(set(related))
    
    def _get_entity_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get entity context for current conversation"""
        if conversation_id not in self.memory["conversations"]:
            return {}
        
        turns = self.memory["conversations"][conversation_id]["turns"]
        all_entities = []
        for turn in turns:
            all_entities.extend(turn.get("entities", []))
        
        entity_context = {}
        for entity in set(all_entities):
            if entity in self.memory["entity_context"]:
                entity_context[entity] = self.memory["entity_context"][entity]
        
        return entity_context
    
    def _get_conversation_summary(self, conversation_id: str) -> str:
        """Get conversation summary"""
        if conversation_id not in self.memory["conversations"]:
            return ""
        
        turns = self.memory["conversations"][conversation_id]["turns"]
        if not turns:
            return ""
        
        # Simple summary based on topics and entities
        topics = set()
        entities = set()
        for turn in turns:
            topics.update(turn.get("topics", []))
            entities.update(turn.get("entities", []))
        
        summary_parts = []
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(list(topics)[:3])}")
        if entities:
            summary_parts.append(f"Entities mentioned: {', '.join(list(entities)[:3])}")
        
        return "; ".join(summary_parts)

# Utility functions for extracting topics and entities
def extract_topics_and_entities(text: str) -> tuple[List[str], List[str]]:
    """Extract topics and entities from text"""
    topics = []
    entities = []
    
    # Simple keyword-based extraction (can be enhanced with NLP)
    topic_keywords = {
        "tesla": ["tesla", "tsla", "electric vehicle", "ev"],
        "apple": ["apple", "aapl", "iphone", "ios"],
        "microsoft": ["microsoft", "msft", "azure", "windows"],
        "google": ["google", "googl", "alphabet", "search"],
        "amazon": ["amazon", "amzn", "aws", "e-commerce"],
        "machine learning": ["machine learning", "ml", "ai", "artificial intelligence"],
        "finance": ["financial", "revenue", "earnings", "stock", "market"],
        "research": ["research", "papers", "academic", "study", "literature"]
    }
    
    entity_keywords = {
        "companies": ["tesla", "apple", "microsoft", "google", "amazon", "meta", "netflix"],
        "tickers": ["tsla", "aapl", "msft", "googl", "amzn", "meta", "nflx"],
        "concepts": ["machine learning", "artificial intelligence", "electric vehicles", "cloud computing"]
    }
    
    text_lower = text.lower()
    
    # Extract topics
    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    # Extract entities
    for entity_type, keywords in entity_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                entities.append(keyword)
    
    return topics, entities