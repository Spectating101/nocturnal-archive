"""
Real Archive API Routes - Integrated from nocturnal-archive-api
Academic research and synthesis platform
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
import structlog
import os
import sys
import uuid

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

from src.config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/archive", tags=["Archive"])

# Import Archive components
try:
    from src.models.request import SearchRequest
    from src.models.paper import SearchResult, Paper, Author
    from src.services.paper_search import PaperSearcher
    from src.engine.research_engine import sophisticated_engine
    ARCHIVE_AVAILABLE = True
    logger.info("✅ Real Archive components loaded successfully")
except ImportError as e:
    logger.warning(f"Archive components not available: {e}")
    ARCHIVE_AVAILABLE = False

# Simplified Archive implementation for demo purposes
class SimplePaperSearcher:
    """Simplified paper searcher for demo purposes"""
    
    async def search_papers(self, request):
        """Return mock academic papers"""
        import random
        import uuid
        
        papers = []
        for i in range(min(request.limit, 10)):
            paper_id = f"W{random.randint(1000000000, 9999999999)}"
            
            papers.append({
                "id": paper_id,
                "title": f"Research Paper {i+1}: {request.query.title()}",
                "authors": [
                    {"name": f"Author {i+1}, A.", "orcid": f"0000-0000-0000-{i:04d}"},
                    {"name": f"Researcher {i+1}, B.", "orcid": f"0000-0000-0000-{i+1:04d}"}
                ],
                "year": random.randint(2020, 2024),
                "doi": f"10.1038/s41586-023-{random.randint(10000, 99999)}",
                "abstract": f"This paper presents research on {request.query}. The findings show significant results in the field of study. The methodology employed demonstrates innovative approaches to the problem.",
                "citations_count": random.randint(5, 500),
                "open_access": random.choice([True, False]),
                "pdf_url": f"https://example.com/papers/{paper_id}.pdf",
                "source": random.choice(["openalex", "pubmed", "arxiv"]),
                "venue": random.choice(["Nature", "Science", "Cell", "PNAS", "PLOS ONE"]),
                "keywords": [request.query, "research", "analysis", "study"]
            })
        
        # Return simple dict instead of SearchResult
        return {
            "papers": papers,
            "count": len(papers),
            "query_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4())
        }
    
    async def format_citations(self, paper_ids: list, style: str):
        """Return mock formatted citations"""
        citations = []
        for paper_id in paper_ids:
            if style == "bibtex":
                citations.append(f"""@article{{{paper_id},
  title={{Research Paper: {paper_id}}},
  author={{Author, A. and Researcher, B.}},
  journal={{Nature}},
  year={{2023}},
  doi={{10.1038/s41586-023-{paper_id}}}
}}""")
            elif style == "apa":
                citations.append(f"Author, A., & Researcher, B. (2023). Research Paper: {paper_id}. Nature, 10.1038/s41586-023-{paper_id}")
            else:
                citations.append(f"Author, A., Researcher, B. (2023). Research Paper: {paper_id}. Nature.")
        
        return citations

class SimpleResearchEngine:
    """Simplified research engine for demo purposes"""
    
    def __init__(self):
        self.enhanced_research = True
    
    async def search_papers_advanced(self, query: str, limit: int, sources: list, filters: dict):
        """Return mock advanced search results"""
        # Use the simple searcher for now
        searcher = SimplePaperSearcher()
        request = type('Request', (), {
            'query': query,
            'limit': limit,
            'sources': sources,
            'filters': filters
        })()
        result = await searcher.search_papers(request)
        return result["papers"]
    
    async def synthesize_papers(self, paper_ids: list, max_words: int, focus: str):
        """Return mock synthesis"""
        return f"""Synthesis of {len(paper_ids)} research papers focusing on {focus}:

Key Findings:
- Significant advances in the field have been demonstrated across multiple studies
- The research shows consistent patterns in the data analysis
- Methodological improvements have led to more accurate results

Implications:
- These findings have important implications for future research
- The results suggest new directions for investigation
- Practical applications are emerging from this body of work

This synthesis represents a comprehensive analysis of {len(paper_ids)} papers, providing insights into the current state of research in this area."""

# Global instances - USE REAL COMPONENTS
if ARCHIVE_AVAILABLE:
    paper_searcher = PaperSearcher()
    sophisticated_engine = sophisticated_engine
    logger.info("🚀 Using REAL Archive components - no mocks!")
else:
    # Use simplified implementations
    paper_searcher = SimplePaperSearcher()
    sophisticated_engine = SimpleResearchEngine()
    logger.warning("⚠️ Using mock Archive components - real APIs not available")

class ArchiveSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for academic papers")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    sources: List[str] = Field(["openalex"], description="Data sources to search")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")

class ArchiveFormatRequest(BaseModel):
    paper_ids: List[str] = Field(..., description="List of paper IDs to format")
    style: str = Field("bibtex", description="Citation style (bibtex, apa, mla, chicago, harvard)")

class ArchiveSynthesizeRequest(BaseModel):
    paper_ids: List[str] = Field(..., description="List of paper IDs to synthesize")
    max_words: int = Field(300, ge=50, le=1000, description="Maximum words in synthesis")
    focus: str = Field("key_findings", description="Focus area for synthesis")

@router.get("/health")
async def archive_health():
    """Archive module health check"""
    return {
        "module": "archive",
        "status": "healthy" if ARCHIVE_AVAILABLE else "unavailable",
        "components": {
            "paper_searcher": ARCHIVE_AVAILABLE,
            "research_engine": ARCHIVE_AVAILABLE
        },
        "endpoints": [
            "GET /archive/health",
            "POST /archive/search",
            "POST /archive/format",
            "POST /archive/synthesize"
        ],
        "timestamp": date.today().isoformat()
    }

@router.post("/search")
async def search_papers(
    request: ArchiveSearchRequest,
    enhance: bool = Query(True, description="Enable performance enhancements"),
    extract_insights: bool = Query(False, description="Extract research insights"),
    settings: Settings = Depends(get_settings)
):
    """Search academic papers from trusted sources with performance optimizations"""
    
    if not ARCHIVE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Archive components not available")
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Archive search request received",
            query=request.query,
            limit=request.limit,
            sources=request.sources,
            enhance=enhance,
            extract_insights=extract_insights,
            trace_id=trace_id
        )
        
        # Try sophisticated engine first, fallback to basic search
        if sophisticated_engine.enhanced_research:
            logger.info("Using sophisticated research engine", trace_id=trace_id)
            advanced_results = await sophisticated_engine.search_papers_advanced(
                query=request.query,
                limit=request.limit,
                sources=request.sources,
                filters=request.filters or {}
            )
            
            if advanced_results:
                return {
                    "papers": advanced_results,
                    "count": len(advanced_results),
                    "query_id": f"q_{trace_id}",
                    "trace_id": trace_id,
                    "engine": "sophisticated"
                }
        
        # Fallback to basic search
        logger.info("Using basic paper search", trace_id=trace_id)
        search_request = SearchRequest(
            query=request.query,
            limit=request.limit,
            sources=request.sources,
            filters=request.filters or {}
        )
        
        results = await paper_searcher.search_papers(search_request)
        
        return {
            "papers": results["papers"],
            "count": results["count"],
            "query_id": f"q_{trace_id}",
            "trace_id": trace_id,
            "engine": "basic"
        }
        
    except Exception as e:
        logger.error(f"Archive search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Archive search failed: {str(e)}")

@router.post("/format")
async def format_citations(
    request: ArchiveFormatRequest,
    settings: Settings = Depends(get_settings)
):
    """Format paper citations in various styles"""
    
    if not ARCHIVE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Archive components not available")
    
    try:
        logger.info(
            "Archive format request received",
            paper_ids=request.paper_ids,
            style=request.style
        )
        
        # Format citations using paper searcher
        formatted_citations = await paper_searcher.format_citations(
            paper_ids=request.paper_ids,
            style=request.style
        )
        
        return {
            "paper_ids": request.paper_ids,
            "style": request.style,
            "citations": formatted_citations,
            "count": len(formatted_citations),
            "timestamp": date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Archive format failed: {e}")
        raise HTTPException(status_code=500, detail=f"Archive format failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_research(
    request: ArchiveSynthesizeRequest,
    settings: Settings = Depends(get_settings)
):
    """Synthesize research findings from multiple papers"""
    
    if not ARCHIVE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Archive components not available")
    
    try:
        logger.info(
            "Archive synthesize request received",
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus
        )
        
        # Synthesize using research engine
        synthesis = await sophisticated_engine.synthesize_papers(
            paper_ids=request.paper_ids,
            max_words=request.max_words,
            focus=request.focus
        )
        
        return {
            "paper_ids": request.paper_ids,
            "synthesis": synthesis,
            "word_count": len(synthesis.split()),
            "focus": request.focus,
            "timestamp": date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Archive synthesize failed: {e}")
        raise HTTPException(status_code=500, detail=f"Archive synthesize failed: {str(e)}")

@router.get("/status")
async def archive_status(settings: Settings = Depends(get_settings)):
    """Get Archive module status and configuration"""
    return {
        "module": "archive",
        "enabled": ARCHIVE_AVAILABLE,
        "status": "healthy" if ARCHIVE_AVAILABLE else "unavailable",
        "configuration": {
            "paper_searcher_enabled": ARCHIVE_AVAILABLE,
            "research_engine_enabled": ARCHIVE_AVAILABLE,
            "sophisticated_engine": ARCHIVE_AVAILABLE and sophisticated_engine.enhanced_research
        },
        "endpoints": [
            "GET /archive/health",
            "GET /archive/status",
            "POST /archive/search",
            "POST /archive/format", 
            "POST /archive/synthesize"
        ],
        "timestamp": date.today().isoformat()
    }
