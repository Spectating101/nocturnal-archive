# src/services/llm_service/api_clients/groq_client.py

import aiohttp
import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from collections import deque
import time
from groq import Groq

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for Groq AI API - replaces all other LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq client with API key"""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.request_times = deque(maxlen=10)  # Track last 10 requests
        self.requests_per_minute = 30  # Groq's generous limit
        self.client = None
        
        # Set default model
        self.default_model = "llama-3.3-70b-versatile"
        self.synthesis_model = "llama-3.3-70b-versatile"
        self.analysis_model = "llama-3.3-70b-versatile"
        
        if not self.api_key:
            logger.warning("Groq API key not set. Set GROQ_API_KEY env var or pass as argument")
        else:
            self.client = Groq(api_key=self.api_key)
    
    def set_config(self, config):
        """Set configuration for the client"""
        self.config = config
        
        # Update model names from config
        models = config.get("models", {})
        self.default_model = models.get("default", "llama-3.3-70b-versatile")
        self.synthesis_model = models.get("synthesis", "llama-3.3-70b-versatile")
        self.analysis_model = models.get("analysis", "llama-3.3-70b-versatile")
    
    async def _check_rate_limit(self):
        """Wait if we're hitting rate limits"""
        now = time.time()
        if len(self.request_times) >= 10:
            oldest = self.request_times[0]
            if now - oldest < 60:  # 10 requests within 60 seconds
                wait_time = 60 - (now - oldest) + 1
                logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
        self.request_times.append(now)
    
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document using Groq API
        
        Args:
            document: Document to process with fields like 'id', 'title', 'content', 'type'
            
        Returns:
            Dict with processing results
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq client not initialized - API key missing",
                "provider": "groq"
            }
        
        try:
            await self._check_rate_limit()
            
            # Extract document information
            doc_id = document.get("id", "unknown")
            title = document.get("title", "")
            content = document.get("content", "")
            doc_type = document.get("type", "research")
            
            # Build appropriate prompt based on document type
            if doc_type == "research":
                prompt = self._build_research_prompt(title, content)
            elif doc_type == "financial":
                prompt = self._build_financial_prompt(title, content)
            else:
                prompt = self._build_general_prompt(title, content)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are an expert research and financial analysis assistant. Provide accurate, well-structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # Parse and structure the response
            result = {
                "success": True,
                "provider": "groq",
                "model": self.default_model,
                "document_id": doc_id,
                "analysis": result_text,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "title": title,
                    "type": doc_type,
                    "content_length": len(content),
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            }
            
            logger.info(f"Document {doc_id} processed successfully by Groq")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id} with Groq: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq",
                "document_id": doc_id
            }
    
    async def synthesize_documents(self, documents: List[Dict[str, Any]], focus: str = "key_findings") -> Dict[str, Any]:
        """
        Synthesize multiple documents using Groq
        
        Args:
            documents: List of documents to synthesize
            focus: Focus area for synthesis
            
        Returns:
            Dict with synthesis results
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq client not initialized - API key missing",
                "provider": "groq"
            }
        
        try:
            await self._check_rate_limit()
            
            # Build synthesis prompt
            prompt = self._build_synthesis_prompt(documents, focus)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.synthesis_model,
                messages=[
                    {"role": "system", "content": "You are an expert research synthesizer. Provide comprehensive, well-cited synthesis of multiple documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            synthesis_text = response.choices[0].message.content
            
            result = {
                "success": True,
                "provider": "groq",
                "model": self.synthesis_model,
                "synthesis": synthesis_text,
                "document_count": len(documents),
                "focus": focus,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            }
            
            logger.info(f"Synthesized {len(documents)} documents successfully with Groq")
            return result
            
        except Exception as e:
            logger.error(f"Error synthesizing documents with Groq: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq"
            }
    
    def _build_research_prompt(self, title: str, content: str) -> str:
        """Build prompt for research document analysis"""
        return f"""Analyze the following research document and extract key information:

Title: {title}

Content: {content[:2000]}...

Please provide:
1. Main findings and conclusions
2. Methodology used
3. Key data points and statistics
4. Limitations or gaps
5. Implications for future research

Format your response in a structured way with clear sections."""
    
    def _build_financial_prompt(self, title: str, content: str) -> str:
        """Build prompt for financial document analysis"""
        return f"""Analyze the following financial document and extract key information:

Title: {title}

Content: {content[:2000]}...

Please provide:
1. Key financial metrics and ratios
2. Revenue and profit analysis
3. Risk factors identified
4. Market trends and outlook
5. Investment implications

Format your response in a structured way with clear sections."""
    
    def _build_general_prompt(self, title: str, content: str) -> str:
        """Build prompt for general document analysis"""
        return f"""Analyze the following document and extract key information:

Title: {title}

Content: {content[:2000]}...

Please provide:
1. Main points and key insights
2. Important data or statistics
3. Conclusions and recommendations
4. Areas for further investigation

Format your response in a structured way with clear sections."""
    
    def _build_synthesis_prompt(self, documents: List[Dict[str, Any]], focus: str) -> str:
        """Build prompt for document synthesis"""
        docs_text = ""
        for i, doc in enumerate(documents, 1):
            docs_text += f"\n\nDocument {i}: {doc.get('title', 'Untitled')}\n"
            docs_text += f"Content: {doc.get('content', '')[:500]}...\n"
        
        return f"""Synthesize the following documents focusing on {focus}:

{docs_text}

Please provide a comprehensive synthesis that:
1. Identifies common themes and patterns
2. Highlights key findings across all documents
3. Points out contradictions or gaps
4. Provides overall conclusions and insights
5. Suggests areas for future research

Format your response in a structured way with clear sections."""
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Groq service is healthy"""
        if not self.client:
            return {
                "healthy": False,
                "error": "Groq client not initialized",
                "provider": "groq"
            }
        
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "user", "content": "Hello, this is a health check. Please respond with 'OK'."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            return {
                "healthy": True,
                "provider": "groq",
                "model": self.default_model,
                "response": response.choices[0].message.content.strip()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": "groq"
            }
