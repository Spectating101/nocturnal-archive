#!/usr/bin/env python3
"""
Local Memory System - No LLM calls for memory operations
Implements extractive summaries and local storage
"""

import re
import json
import sqlite3
import time
import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class MemoryEntry:
    user_id: str
    conversation_id: str
    timestamp: str
    content: str
    topics: List[str]
    entities: List[str]
    summary: str

class LocalMemorySystem:
    """Local memory system with extractive summaries (no LLM calls)"""
    
    def __init__(self, db_path: str = "local_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                topics TEXT NOT NULL,
                entities TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                expertise_level TEXT DEFAULT 'expert',
                preferred_format TEXT DEFAULT 'narrative',
                verbosity TEXT DEFAULT 'medium',
                last_updated INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        conn.commit()
        conn.close()
    
    def extractive_summary(self, text: str, max_sentences: int = 5) -> str:
        """Create extractive summary without LLM calls"""
        if not text or len(text.strip()) < 100:
            return text
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= max_sentences:
            return text
        
        # Calculate word frequencies
        word_freq = {}
        for word in re.findall(r'\w+', text.lower()):
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score sentences by word frequency
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 20:  # Skip very short sentences
                continue
            
            # Calculate score based on word frequencies
            words = re.findall(r'\w+', sentence.lower())
            score = sum(word_freq.get(word, 0) for word in words)
            
            # Boost score for sentences with important keywords
            important_keywords = ['tesla', 'apple', 'financial', 'analysis', 'data', 'results', 'conclusion']
            for keyword in important_keywords:
                if keyword in sentence.lower():
                    score *= 1.5
            
            sentence_scores.append((score, i, sentence))
        
        # Select top sentences
        top_sentences = sorted(sentence_scores, reverse=True)[:max_sentences]
        top_sentences.sort(key=lambda x: x[1])  # Sort by original order
        
        return ' '.join(sentence for _, _, sentence in top_sentences)
    
    def extract_topics_and_entities(self, text: str) -> tuple[List[str], List[str]]:
        """Extract topics and entities using simple heuristics"""
        text_lower = text.lower()
        
        # Topic keywords
        topic_keywords = {
            'finance': ['financial', 'revenue', 'profit', 'stock', 'market', 'earnings'],
            'technology': ['technology', 'tech', 'software', 'hardware', 'innovation'],
            'research': ['research', 'study', 'analysis', 'paper', 'academic'],
            'data': ['data', 'dataset', 'statistics', 'analysis', 'results'],
            'business': ['business', 'company', 'corporate', 'strategy', 'management']
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        # Entity extraction (simple)
        entities = []
        
        # Company names
        company_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|LLC|Company)\b',
            r'\b(?:Tesla|Apple|Microsoft|Google|Amazon|Meta|Netflix)\b'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Numbers and percentages
        number_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # Money
            r'\d+(?:\.\d+)?%',        # Percentages
            r'\d+(?:,\d{3})*(?:\.\d+)?'  # Large numbers
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return list(set(topics)), list(set(entities))
    
    def store_memory(self, user_id: str, conversation_id: str, content: str) -> str:
        """Store memory entry with local processing"""
        timestamp = datetime.now().isoformat()
        topics, entities = self.extract_topics_and_entities(content)
        summary = self.extractive_summary(content)
        
        entry = MemoryEntry(
            user_id=user_id,
            conversation_id=conversation_id,
            timestamp=timestamp,
            content=content,
            topics=topics,
            entities=entities,
            summary=summary
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO memory_entries 
            (user_id, conversation_id, timestamp, content, topics, entities, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.user_id,
            entry.conversation_id,
            entry.timestamp,
            entry.content,
            json.dumps(entry.topics),
            json.dumps(entry.entities),
            entry.summary
        ))
        conn.commit()
        conn.close()
        
        return entry.summary
    
    def retrieve_memory(self, user_id: str, conversation_id: str = None, 
                       topics: List[str] = None, entities: List[str] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memory entries based on criteria"""
        conn = sqlite3.connect(self.db_path)
        
        # Build query
        query = "SELECT * FROM memory_entries WHERE user_id = ?"
        params = [user_id]
        
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        if topics:
            topic_conditions = []
            for topic in topics:
                topic_conditions.append("topics LIKE ?")
                params.append(f'%"{topic}"%')
            if topic_conditions:
                query += " AND (" + " OR ".join(topic_conditions) + ")"
        
        if entities:
            entity_conditions = []
            for entity in entities:
                entity_conditions.append("(content LIKE ? OR entities LIKE ?)")
                params.extend([f'%{entity}%', f'%{entity}%'])
            if entity_conditions:
                query += " AND (" + " OR ".join(entity_conditions) + ")"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'user_id': row[1],
                'conversation_id': row[2],
                'timestamp': row[3],
                'content': row[4],
                'topics': json.loads(row[5]),
                'entities': json.loads(row[6]),
                'summary': row[7]
            })
        
        conn.close()
        return results
    
    def get_context_summary(self, user_id: str, conversation_id: str, 
                           max_entries: int = 3) -> str:
        """Get context summary for current conversation"""
        memories = self.retrieve_memory(user_id, conversation_id, limit=max_entries)
        
        if not memories:
            return "No previous context found."
        
        # Combine summaries with timestamps
        context_parts = []
        for mem in memories:
            timestamp = mem['timestamp'][:16]  # YYYY-MM-DD HH:MM
            summary = mem['summary']
            context_parts.append(f"[{timestamp}] {summary}")
        
        combined = ' | '.join(context_parts)
        
        # Create final summary
        return self.extractive_summary(combined, max_sentences=3)
    
    def update_user_profile(self, user_id: str, expertise_level: str = None,
                           preferred_format: str = None, verbosity: str = None):
        """Update user profile preferences"""
        conn = sqlite3.connect(self.db_path)
        
        # Get current profile
        cursor = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        current = cursor.fetchone()
        
        if current:
            # Update existing
            conn.execute("""
                UPDATE user_profiles 
                SET expertise_level = COALESCE(?, expertise_level),
                    preferred_format = COALESCE(?, preferred_format),
                    verbosity = COALESCE(?, verbosity),
                    last_updated = strftime('%s', 'now')
                WHERE user_id = ?
            """, (expertise_level, preferred_format, verbosity, user_id))
        else:
            # Create new
            conn.execute("""
                INSERT INTO user_profiles 
                (user_id, expertise_level, preferred_format, verbosity)
                VALUES (?, ?, ?, ?)
            """, (user_id, expertise_level or 'expert', 
                  preferred_format or 'narrative', verbosity or 'medium'))
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'expertise_level': row[1],
                'preferred_format': row[2],
                'verbosity': row[3],
                'last_updated': row[4]
            }
        else:
            return {
                'user_id': user_id,
                'expertise_level': 'expert',
                'preferred_format': 'narrative',
                'verbosity': 'medium',
                'last_updated': None
            }

# Example usage
if __name__ == "__main__":
    memory = LocalMemorySystem()
    
    # Test memory storage
    print("🧠 LOCAL MEMORY SYSTEM TEST")
    print("=" * 50)
    
    # Store some test memories
    test_content = """
    We analyzed Tesla's financial performance for Q4 2024. The company reported 
    revenue of $25.2 billion, up 15% year-over-year. Net income was $2.1 billion, 
    representing a 8.5% margin. The automotive segment showed strong growth with 
    Model Y deliveries increasing 12% quarter-over-quarter.
    """
    
    summary = memory.store_memory("test_user", "test_conv", test_content)
    print(f"Stored memory summary: {summary}")
    
    # Retrieve memories
    memories = memory.retrieve_memory("test_user", topics=["finance"])
    print(f"Retrieved {len(memories)} memories")
    
    # Get context summary
    context = memory.get_context_summary("test_user", "test_conv")
    print(f"Context summary: {context}")
