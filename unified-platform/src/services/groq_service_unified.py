"""
Unified Groq Service - Handles all LLM operations for the unified platform
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from groq import Groq

logger = logging.getLogger(__name__)

class UnifiedGroqService:
    """
    Unified Groq service that handles all LLM operations for:
    - FinSight (financial analysis)
    - Archive (research synthesis) 
    - Assistant (R/SQL programming help)
    """
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize unified Groq service"""
        self.client = Groq(api_key=api_key)
        self.model = model
        self.max_tokens = 4000
        self.temperature = 0.1
        
        logger.info(f"UnifiedGroqService initialized with model: {model}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Groq service is healthy"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, this is a health check. Please respond with 'OK'."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            return {
                "healthy": True,
                "provider": "groq",
                "model": self.model,
                "response": response.choices[0].message.content.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": "groq"
            }
    
    # === FINSIGHT METHODS ===
    
    async def finsight_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform financial analysis using Groq
        
        Args:
            financial_data: Financial data to analyze
            
        Returns:
            Analysis results
        """
        try:
            prompt = self._build_finsight_prompt(financial_data)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst. Provide accurate, well-structured financial analysis with specific metrics and insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                "success": True,
                "analysis": analysis_text,
                "provider": "groq",
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            }
            
        except Exception as e:
            logger.error(f"FinSight analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq"
            }
    
    def _build_finsight_prompt(self, financial_data: Dict[str, Any]) -> str:
        """Build prompt for financial analysis"""
        ticker = financial_data.get("ticker", "Unknown")
        period = financial_data.get("period", "Unknown")
        data = financial_data.get("data", {})
        
        return f"""Analyze the following financial data for {ticker} for period {period}:

Financial Data:
{json.dumps(data, indent=2)}

Please provide:
1. Key financial metrics and ratios
2. Revenue and profit analysis
3. Growth trends and patterns
4. Risk assessment
5. Investment recommendations
6. Comparison with industry benchmarks

Format your analysis in a structured way with clear sections and specific numbers."""
    
    # === ARCHIVE METHODS ===
    
    async def research_synthesis(self, papers: List[Dict[str, Any]], focus: str = "key_findings") -> Dict[str, Any]:
        """
        Perform research synthesis using Groq
        
        Args:
            papers: List of research papers
            focus: Focus area for synthesis
            
        Returns:
            Synthesis results
        """
        try:
            prompt = self._build_synthesis_prompt(papers, focus)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert research synthesizer. Provide comprehensive, well-cited synthesis of multiple research papers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            synthesis_text = response.choices[0].message.content
            
            return {
                "success": True,
                "synthesis": synthesis_text,
                "provider": "groq",
                "model": self.model,
                "paper_count": len(papers),
                "focus": focus,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            }
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq"
            }
    
    def _build_synthesis_prompt(self, papers: List[Dict[str, Any]], focus: str) -> str:
        """Build prompt for research synthesis"""
        papers_text = ""
        for i, paper in enumerate(papers, 1):
            papers_text += f"\n\nPaper {i}: {paper.get('title', 'Untitled')}\n"
            papers_text += f"Authors: {', '.join(paper.get('authors', []))}\n"
            papers_text += f"Abstract: {paper.get('abstract', '')[:500]}...\n"
        
        return f"""Synthesize the following research papers focusing on {focus}:

{papers_text}

Please provide a comprehensive synthesis that:
1. Identifies common themes and patterns
2. Highlights key findings across all papers
3. Points out contradictions or gaps
4. Provides overall conclusions and insights
5. Suggests areas for future research
6. Includes specific citations and references

Format your response in a structured way with clear sections."""
    
    # === ASSISTANT METHODS ===
    
    async def assistant_help(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Provide R/SQL programming assistance using Groq
        
        Args:
            question: User's question
            context: Additional context (files, code, etc.)
            
        Returns:
            Assistance response
        """
        try:
            prompt = self._build_assistant_prompt(question, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert R and SQL programming assistant. Provide clear, accurate, and practical help with code examples and explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            help_text = response.choices[0].message.content
            
            return {
                "success": True,
                "response": help_text,
                "provider": "groq",
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            }
            
        except Exception as e:
            logger.error(f"Assistant help failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq"
            }
    
    def _build_assistant_prompt(self, question: str, context: Dict[str, Any] = None) -> str:
        """Build prompt for R/SQL assistance"""
        context_text = ""
        if context:
            if "files" in context:
                context_text += f"\n\nRelevant files:\n{context['files']}\n"
            if "code" in context:
                context_text += f"\n\nCode context:\n{context['code']}\n"
            if "error" in context:
                context_text += f"\n\nError message:\n{context['error']}\n"
        
        return f"""Please help with this R/SQL programming question:

Question: {question}
{context_text}

Please provide:
1. Clear explanation of the concept
2. Code examples with comments
3. Best practices and tips
4. Common pitfalls to avoid
5. Related functions or techniques

Format your response in a structured way with clear sections and code blocks."""
    
    # === UNIFIED METHODS ===
    
    async def process_request(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified request processor that routes to appropriate method
        
        Args:
            request_type: Type of request (finsight, archive, assistant)
            data: Request data
            
        Returns:
            Processing results
        """
        try:
            if request_type == "finsight":
                return await self.finsight_analysis(data)
            elif request_type == "archive":
                papers = data.get("papers", [])
                focus = data.get("focus", "key_findings")
                return await self.research_synthesis(papers, focus)
            elif request_type == "assistant":
                question = data.get("question", "")
                context = data.get("context", {})
                return await self.assistant_help(question, context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "provider": "groq"
                }
                
        except Exception as e:
            logger.error(f"Unified request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "groq"
            }
    
    async def batch_process(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple requests in batch
        
        Args:
            requests: List of requests with 'type' and 'data' fields
            
        Returns:
            List of results
        """
        try:
            tasks = []
            for request in requests:
                request_type = request.get("type")
                data = request.get("data", {})
                task = self.process_request(request_type, data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result),
                        "provider": "groq",
                        "request_index": i
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [{
                "success": False,
                "error": str(e),
                "provider": "groq"
            } for _ in requests]


# Backward compatibility
GroqService = UnifiedGroqService
