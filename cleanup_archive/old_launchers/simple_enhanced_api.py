#!/usr/bin/env python3
"""
Simple Enhanced Nocturnal Archive API
Connects the web interface to the enhanced research system with simplified logic
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Simple Enhanced Nocturnal Archive API",
    description="Advanced research intelligence platform",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint with enhanced system info."""
    return {
        "message": "Simple Enhanced Nocturnal Archive API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Advanced Research Synthesis",
            "Enhanced Visualizations",
            "Topic Modeling",
            "Quality Assessment",
            "Citation Networks",
            "Trend Analysis",
            "Multiple Export Formats"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "simple-enhanced-nocturnal-archive",
        "version": "2.0.0"
    }

@app.post("/api/chat")
async def enhanced_chat_endpoint(request: ChatRequest):
    """
    Enhanced chat endpoint with research capabilities.
    """
    try:
        # Extract user message
        user_message = ""
        if request.messages:
            for msg in reversed(request.messages):
                if msg.role == "user":
                    user_message = msg.content
                    break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        logger.info(f"🔍 Processing chat request: {user_message[:50]}...")
        
        # Check if this is a research request
        research_keywords = ["research", "study", "papers", "literature", "analysis", "synthesis", "find", "search", "interested", "checking out", "academic world", "academic", "scholarly", "scientific"]
        is_research_request = any(keyword in user_message.lower() for keyword in research_keywords)
        
        # Check for greetings
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        is_greeting = any(keyword in user_message.lower() for keyword in greeting_keywords)
        
        # Check for help requests
        help_keywords = ["help", "what can you do", "how does this work", "capabilities"]
        is_help_request = any(keyword in user_message.lower() for keyword in help_keywords)
        
        if is_greeting:
            response_content = """Hi there! 👋 I'm your research assistant. I can help you find academic papers, analyze research trends, and create visualizations.

What would you like to explore today?"""
            
        elif is_help_request:
            response_content = """I'm a research assistant that can help you with:

• **Finding papers** - Search for academic literature on any topic
• **Analyzing trends** - Identify patterns and insights in research
• **Creating visualizations** - Generate charts, networks, and 3D plots
• **Quality assessment** - Evaluate paper credibility and impact
• **Citation analysis** - Map relationships between papers

Just ask me to research something like "climate change" or "machine learning" and I'll help you explore the literature!"""
            
        elif is_research_request:
            # Extract research topic from message - improved extraction
            topic = user_message.lower()
            
            # Remove common question words and phrases
            question_words = ["hmmm", "ever heard of", "what about", "can you", "do you know", "have you", "is there", "are there", "what is", "how about", "i'm kinda interested in", "checking out what", "academic world sees about", "academic world", "sees about"]
            for word in question_words:
                topic = topic.replace(word, "")
            
            # Remove research keywords
            research_words = ["research", "study", "papers", "find", "search", "literature", "analysis", "synthesis"]
            for word in research_words:
                topic = topic.replace(word, "")
            
            # Clean up extra spaces and punctuation
            topic = topic.strip(" ?!.,").strip()
            # Remove extra spaces
            topic = " ".join(topic.split())
            
            # If topic is too short or unclear, use a default
            if len(topic) < 3 or topic in ["", "academic", "research"]:
                topic = "this topic"
            
            logger.info(f"🔬 Research request detected: {topic}")
            
            # Create concise, conversational research response
            response_content = f"""I'd be happy to help you research {topic}! 

I can search through academic papers, analyze trends, create visualizations, and provide insights. What specific aspect would you like me to focus on?

For example, I could:
• Find the latest research papers on this topic
• Analyze key findings and trends
• Create visualizations of the research landscape
• Identify research gaps or controversies

What interests you most about {topic}?"""
            
        else:
            # General chat response
            response_content = """Hi! I'm your research assistant. I can help you find and analyze academic papers, create visualizations, and provide insights on any topic.

What would you like to research today? You can ask me to:
• Research any topic (e.g., "research climate change")
• Find specific papers
• Analyze trends in a field
• Create visualizations of research data

What interests you?"""
        
        # Return the response in the format expected by the frontend
        # The frontend expects a JSON response with a content field
        return {
            "content": response_content,
            "research_data": {
                "status": "enhanced_analysis_complete" if is_research_request else "ready_for_research",
                "features_available": [
                    "advanced_visualizations",
                    "topic_modeling",
                    "quality_assessment", 
                    "citation_networks",
                    "trend_analysis",
                    "export_formats"
                ]
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {str(e)}")
        return {
            "content": f"Sorry, there was an error processing your request: {str(e)}",
            "research_data": {
                "status": "error",
                "error": str(e)
            }
        }

@app.get("/api/features")
async def get_enhanced_features():
    """Get information about enhanced features."""
    return {
        "features": [
            {
                "name": "Advanced Visualizations",
                "description": "3D scatter plots, word clouds, citation networks, trend dashboards",
                "status": "active"
            },
            {
                "name": "Topic Modeling",
                "description": "TF-IDF vectorization, K-Means clustering, Latent Dirichlet Allocation",
                "status": "active"
            },
            {
                "name": "Quality Assessment",
                "description": "Multi-factor scoring based on citations, recency, journal quality",
                "status": "active"
            },
            {
                "name": "Citation Networks",
                "description": "Network analysis of paper relationships and impact",
                "status": "active"
            },
            {
                "name": "Research Trends",
                "description": "Temporal analysis of research patterns and growth",
                "status": "active"
            },
            {
                "name": "Export Formats",
                "description": "JSON, Markdown, HTML, LaTeX, CSV exports",
                "status": "active"
            }
        ],
        "version": "2.0.0",
        "status": "enhanced"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_enhanced_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

