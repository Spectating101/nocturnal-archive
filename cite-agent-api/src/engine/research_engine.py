"""
Sophisticated Research Engine Integration
Bridges the API with the full advanced research capabilities
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Add the sophisticated research engine to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

ADVANCED_ENGINE_AVAILABLE = False
logger = logging.getLogger(__name__)

try:
    from src.services.research_service.enhanced_research import EnhancedResearchService
    from src.services.research_service.enhanced_synthesizer import EnhancedSynthesizer
    from src.services.search_service import SearchEngine
    from src.services.paper_service import OpenAlexClient
    from src.services.performance_service.rust_performance import HighPerformanceService
    from src.services.llm_service import LLMManager
    ADVANCED_ENGINE_AVAILABLE = True
    logger.info("Advanced research engine loaded successfully")
except ImportError as e:
    ADVANCED_ENGINE_AVAILABLE = False
    logger.warning(f"Advanced research engine not available: {e}")

class SophisticatedResearchEngine:
    """Sophisticated research engine with all advanced capabilities"""
    
    def __init__(self):
        self.enhanced_research = None
        self.enhanced_synthesizer = None
        self.search_engine = None
        self.openalex_client = None
        self.performance_service = None
        self.llm_manager = None
        
        if ADVANCED_ENGINE_AVAILABLE:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self.openalex_client = OpenAlexClient()
                self.performance_service = HighPerformanceService()
                self.llm_manager = LLMManager(redis_url=redis_url)

                search_engine = SearchEngine(
                    openalex_client=self.openalex_client,
                    performance_service=self.performance_service,
                )
                synthesizer = EnhancedSynthesizer(
                    llm_manager=self.llm_manager,
                    openalex_client=self.openalex_client,
                    performance_service=self.performance_service,
                    redis_url=redis_url,
                )
                self.enhanced_research = EnhancedResearchService(
                    search_engine=search_engine,
                    synthesizer=synthesizer,
                    llm_manager=self.llm_manager,
                    openalex_client=self.openalex_client,
                    performance_service=self.performance_service,
                )
                self.enhanced_synthesizer = synthesizer
                self.search_engine = search_engine
                logger.info("All sophisticated components initialized")
            except Exception as e:
                logger.error(f"Failed to initialize sophisticated components: {e}")
                # Don't modify the global variable here
    
    async def search_papers_advanced(self, query: str, limit: int = 10, sources: List[str] = None) -> Dict[str, Any]:
        """Advanced paper search with sophisticated capabilities"""
        if not ADVANCED_ENGINE_AVAILABLE or not self.search_engine:
            return {"error": "Advanced search not available"}
        
        try:
            # Use the sophisticated search engine
            results = await self.search_engine.search_papers(
                query=query,
                limit=limit,
                sources=sources or ["openalex"],
                include_metadata=True,
                include_abstracts=True,
                include_citations=True
            )
            
            # Enhance with performance optimizations
            if self.performance_service:
                enhanced_results = await self.performance_service.enhance_search_results(results)
                return enhanced_results
            
            return results
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return {"error": f"Search failed: {str(e)}"}
    
    async def synthesize_advanced(
        self,
        paper_ids: List[str],
        max_words: int = 500,
        style: str = "comprehensive",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Advanced synthesis with sophisticated capabilities"""
        if not ADVANCED_ENGINE_AVAILABLE or not self.enhanced_synthesizer:
            return {"error": "Advanced synthesis not available"}
        
        try:
            # Get paper details
            papers = []
            for paper_id in paper_ids:
                if self.openalex_client:
                    paper = await self.openalex_client.get_paper_by_id(paper_id)
                    if paper:
                        papers.append(paper)
            
            if not papers:
                return {"error": "No papers found for synthesis"}
            
            # Perform sophisticated synthesis
            synthesis_result = await self.enhanced_synthesizer.synthesize_research(
                papers=papers,
                max_words=max_words,
                style=style,
                context=context or {},
                include_visualizations=True,
                include_topic_modeling=True,
                include_quality_assessment=True,
            )
            
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Advanced synthesis failed: {e}")
            return {"error": f"Synthesis failed: {str(e)}"}

    async def synthesize_strict(
        self,
        paper_ids: List[str],
        max_words: int = 500,
        style: str = "technical",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Strict synthesis pathway that enforces heavy-model semantics."""

        if not ADVANCED_ENGINE_AVAILABLE or not self.enhanced_synthesizer:
            return {"error": "Advanced synthesis not available"}

        merged_context = dict(context or {})
        merged_context.setdefault("mode", "strict")
        merged_context.setdefault("strict", True)

        result = await self.synthesize_advanced(
            paper_ids=paper_ids,
            max_words=max_words,
            style=style,
            context=merged_context,
        )

        if isinstance(result, dict) and "error" not in result:
            routing_md = result.setdefault("routing_metadata", {})
            decision = routing_md.setdefault("routing_decision", {})
            decision.setdefault("complexity", "heavy")
            decision.setdefault("strategy", "advanced_synthesizer_strict")
            decision.setdefault("model", decision.get("model", "llm-heavy"))
        return result
    
    async def format_citations_advanced(self, paper_ids: List[str], format_style: str = "bibtex") -> Dict[str, Any]:
        """Advanced citation formatting with multiple styles"""
        if not ADVANCED_ENGINE_AVAILABLE:
            return {"error": "Advanced formatting not available"}
        
        try:
            # Get paper details
            papers = []
            for paper_id in paper_ids:
                if self.openalex_client:
                    paper = await self.openalex_client.get_paper_by_id(paper_id)
                    if paper:
                        papers.append(paper)
            
            if not papers:
                return {"error": "No papers found for formatting"}
            
            # Format citations using the sophisticated citation manager
            if hasattr(self.enhanced_synthesizer, 'citation_manager'):
                formatted_citations = await self.enhanced_synthesizer.citation_manager.format_citations(
                    papers=papers,
                    format_style=format_style
                )
                return formatted_citations
            
            return {"error": "Citation formatting not available"}
            
        except Exception as e:
            logger.error(f"Advanced formatting failed: {e}")
            return {"error": f"Formatting failed: {str(e)}"}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components"""
        health_status = {
            "advanced_engine": ADVANCED_ENGINE_AVAILABLE,
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if ADVANCED_ENGINE_AVAILABLE:
            # Check each component
            components = {
                "enhanced_research": self.enhanced_research,
                "enhanced_synthesizer": self.enhanced_synthesizer,
                "search_engine": self.search_engine,
                "openalex_client": self.openalex_client,
                "performance_service": self.performance_service,
                "llm_manager": self.llm_manager,
            }
            
            for name, component in components.items():
                health_status["components"][name] = "available" if component else "unavailable"
        
        return health_status

# Global instance
sophisticated_engine = SophisticatedResearchEngine()
