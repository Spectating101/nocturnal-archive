"""
Enhanced search endpoint with performance optimizations
"""

import structlog
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from src.config.settings import Settings, get_settings
from src.models.request import SearchRequest
from src.models.paper import SearchResult, Paper, Author
from src.services.paper_search import PaperSearcher
from src.services.performance_integration import performance_integration
from src.engine.research_engine import sophisticated_engine

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResult)
async def search_papers(
    request: SearchRequest,
    enhance: bool = Query(True, description="Enable performance enhancements"),
    extract_insights: bool = Query(False, description="Extract research insights"),
    settings: Settings = Depends(get_settings)
):
    """Search academic papers from trusted sources with performance optimizations"""
    
    try:
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        logger.info(
            "Enhanced search request received",
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
                sources=request.sources
            )
            
            if "error" not in advanced_results:
                # Convert advanced results to our format
                papers = []
                for paper_data in advanced_results.get("papers", []):
                    paper = Paper(
                        id=paper_data.get("id", ""),
                        title=paper_data.get("title", ""),
                        authors=[Author(name=author) for author in paper_data.get("authors", [])],
                        year=paper_data.get("year"),
                        doi=paper_data.get("doi"),
                        abstract=paper_data.get("abstract"),
                        citations_count=paper_data.get("citations_count"),
                        open_access=paper_data.get("open_access"),
                        pdf_url=paper_data.get("pdf_url"),
                        source=paper_data.get("source", "openalex"),
                        venue=paper_data.get("venue"),
                        keywords=paper_data.get("keywords", [])
                    )
                    papers.append(paper)
            else:
                logger.warning("Advanced search failed, falling back to basic search", 
                             error=advanced_results.get("error"), trace_id=trace_id)
                # Fallback to basic search
                searcher = PaperSearcher(settings.openalex_api_key)
                papers = await searcher.search_papers(
                    query=request.query,
                    limit=request.limit,
                    sources=request.sources,
                    filters=request.filters
                )
        else:
            logger.info("Using basic search engine", trace_id=trace_id)
            # Use basic search
            searcher = PaperSearcher(settings.openalex_api_key)
            papers = await searcher.search_papers(
                query=request.query,
                limit=request.limit,
                sources=request.sources,
                filters=request.filters
            )
        
        # Convert papers to dict format for processing
        papers_dict = [paper.dict() for paper in papers]
        
        # Apply performance enhancements if requested
        if enhance:
            logger.info("Applying performance enhancements", trace_id=trace_id)
            papers_dict = await performance_integration.enhance_paper_search(papers_dict)
        
        # Extract research insights if requested
        insights = {}
        if extract_insights:
            logger.info("Extracting research insights", trace_id=trace_id)
            insights = await performance_integration.extract_research_insights(papers_dict)
        
        # Convert back to Paper objects
        enhanced_papers = []
        for paper_dict in papers_dict:
            # Create Paper object from dict, handling enhanced fields
            paper_data = {
                'id': paper_dict['id'],
                'title': paper_dict['title'],
                'authors': paper_dict['authors'],
                'year': paper_dict['year'],
                'doi': paper_dict.get('doi'),
                'abstract': paper_dict.get('abstract'),
                'citations_count': paper_dict.get('citations_count'),
                'open_access': paper_dict.get('open_access'),
                'pdf_url': paper_dict.get('pdf_url'),
                'source': paper_dict['source'],
                'venue': paper_dict.get('venue'),
                'keywords': paper_dict.get('keywords'),
                'created_at': paper_dict.get('created_at'),
                'updated_at': paper_dict.get('updated_at')
            }
            
            # Add enhanced fields as metadata
            enhanced_metadata = {}
            if 'enhanced_abstract' in paper_dict:
                enhanced_metadata['enhanced_abstract'] = paper_dict['enhanced_abstract']
            if 'enhanced_title' in paper_dict:
                enhanced_metadata['enhanced_title'] = paper_dict['enhanced_title']
            if 'scraped_content' in paper_dict:
                enhanced_metadata['scraped_content'] = paper_dict['scraped_content']
            
            if enhanced_metadata:
                paper_data['metadata'] = enhanced_metadata
            
            enhanced_papers.append(Paper(**paper_data))
        
        # Generate query ID
        query_id = f"q_{uuid.uuid4().hex[:8]}"
        
        logger.info(
            "Enhanced search completed",
            query_id=query_id,
            results_count=len(enhanced_papers),
            enhanced=enhance,
            insights_extracted=extract_insights,
            trace_id=trace_id
        )
        
        # Create response with insights if requested
        response_data = {
            'papers': enhanced_papers,
            'count': len(enhanced_papers),
            'query_id': query_id,
            'trace_id': trace_id
        }
        
        if extract_insights and insights:
            response_data['insights'] = insights
        
        return SearchResult(**response_data)
    
    except Exception as e:
        logger.error(
            "Enhanced search failed",
            error=str(e),
            query=request.query,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": "Failed to search papers",
                "trace_id": trace_id
            }
        )


@router.get("/search/insights/{query_id}")
async def get_search_insights(
    query_id: str,
    settings: Settings = Depends(get_settings)
):
    """Get insights for a specific search query"""
    
    try:
        # This would typically fetch from cache or database
        # For now, return a placeholder response
        return {
            "query_id": query_id,
            "insights": {
                "message": "Insights feature coming soon",
                "status": "development"
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get insights for query {query_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "insights_failed",
                "message": "Failed to retrieve insights"
            }
        )
