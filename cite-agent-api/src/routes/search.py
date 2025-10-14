"""
Enhanced search endpoint with performance optimizations
"""

import structlog
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional

from src.config.settings import Settings, get_settings
from src.models.request import SearchRequest
from src.models.paper import SearchResult, Paper, Author
from src.services.paper_search import PaperSearcher
from src.services.performance_integration import performance_integration
from src.utils.async_utils import resolve_awaitable
from src.engine.research_engine import sophisticated_engine
from src.utils.api_fallback import api_fallback

logger = structlog.get_logger(__name__)
router = APIRouter()


def _normalize_authors(raw_authors: Any) -> List[Dict[str, Optional[str]]]:
    """Normalize various author payload shapes into Author-compatible dicts."""
    authors: List[Dict[str, Optional[str]]] = []

    if not raw_authors:
        return [{"name": "Unknown Author", "orcid": None, "affiliation": None}]

    for entry in raw_authors:
        if isinstance(entry, Author):
            authors.append(entry.model_dump())
            continue

        name: Optional[str] = None
        orcid: Optional[str] = None
        affiliation: Optional[str] = None

        if isinstance(entry, dict):
            name = entry.get("name") or entry.get("display_name") or entry.get("full_name")

            nested_author = entry.get("author")
            if not name and isinstance(nested_author, dict):
                name = nested_author.get("display_name") or nested_author.get("name")
                orcid = nested_author.get("orcid")
            else:
                orcid = entry.get("orcid")

            affiliation = entry.get("affiliation")
            if not affiliation:
                institution = entry.get("institution") or entry.get("primary_institution")
                if isinstance(institution, dict):
                    affiliation = institution.get("display_name") or institution.get("name")

        elif isinstance(entry, str):
            name = entry

        if not name:
            continue

        authors.append({
            "name": name.strip(),
            "orcid": orcid,
            "affiliation": affiliation
        })

    if not authors:
        authors.append({"name": "Unknown Author", "orcid": None, "affiliation": None})

    return authors


def _extract_year(payload: Dict[str, Any]) -> Optional[int]:
    """Best-effort extraction of publication year from assorted fields."""
    for key in ("year", "publication_year", "published_year", "pub_year"):
        year_value = payload.get(key)
        if year_value in (None, ""):
            continue
        try:
            return int(year_value)
        except (TypeError, ValueError):
            continue

    for key in ("publication_date", "published_date", "release_date", "date"):
        date_val = payload.get(key)
        if not date_val:
            continue
        try:
            return int(str(date_val)[:4])
        except (TypeError, ValueError):
            continue

    return None


def _normalize_abstract(raw_abstract: Any) -> Optional[str]:
    """Convert OpenAlex inverted index structures into readable text."""
    if isinstance(raw_abstract, dict):
        max_pos = 0
        for positions in raw_abstract.values():
            if positions:
                max_pos = max(max_pos, max(positions))

        words = [""] * (max_pos + 1)
        for word, positions in raw_abstract.items():
            for pos in positions:
                if 0 <= pos < len(words):
                    words[pos] = word

        return " ".join(w for w in words if w)

    if isinstance(raw_abstract, str):
        return raw_abstract

    return None


def _normalize_keywords(raw_keywords: Any) -> Optional[List[str]]:
    """Ensure keywords are returned as a clean list of strings."""
    if not raw_keywords:
        return None

    if isinstance(raw_keywords, list):
        keywords: List[str] = []
        for item in raw_keywords:
            if isinstance(item, str):
                value = item.strip()
            elif isinstance(item, dict):
                value = (item.get("display_name") or item.get("name") or "").strip()
            else:
                continue
            if value:
                keywords.append(value)
        return keywords or None

    if isinstance(raw_keywords, dict):
        values = [str(v).strip() for v in raw_keywords.values() if isinstance(v, str) and v.strip()]
        return values or None

    if isinstance(raw_keywords, str):
        stripped = raw_keywords.strip()
        return [stripped] if stripped else None

    return None


def _prepare_paper_payload(raw_paper: Any, trace_id: str) -> Optional[Dict[str, Any]]:
    """Sanitize raw paper data into a Paper-compatible payload."""
    if raw_paper is None:
        return None

    if isinstance(raw_paper, Paper):
        raw_paper = raw_paper.model_dump()

    if not isinstance(raw_paper, dict):
        logger.warning(
            "Skipping paper with unexpected payload type",
            payload_type=type(raw_paper).__name__,
            trace_id=trace_id
        )
        return None

    paper_id = raw_paper.get("id") or raw_paper.get("paper_id") or raw_paper.get("doi")
    if not paper_id:
        paper_id = f"paper_{uuid.uuid4().hex[:8]}"

    title = (
        raw_paper.get("title")
        or raw_paper.get("display_name")
        or raw_paper.get("paper_title")
        or "Untitled paper"
    )
    title = title.strip() if isinstance(title, str) else "Untitled paper"
    if not title:
        title = "Untitled paper"

    authors = _normalize_authors(raw_paper.get("authors"))

    year = _extract_year(raw_paper)
    if year is None:
        logger.warning(
            "Skipping paper due to missing publication year",
            paper_id=paper_id,
            trace_id=trace_id
        )
        return None

    abstract = _normalize_abstract(raw_paper.get("abstract"))

    keywords = _normalize_keywords(
        raw_paper.get("keywords") or raw_paper.get("concepts")
    )

    citations = raw_paper.get("citations_count")
    if citations is not None:
        try:
            citations = int(citations)
        except (TypeError, ValueError):
            citations = None

    open_access = raw_paper.get("open_access")
    if isinstance(open_access, dict):
        open_access = open_access.get("is_oa")

    pdf_url = raw_paper.get("pdf_url")
    if not pdf_url and isinstance(raw_paper.get("open_access"), dict):
        pdf_url = raw_paper["open_access"].get("oa_url")

    payload: Dict[str, Any] = {
        "id": str(paper_id),
        "title": title,
        "authors": authors,
        "year": year,
        "doi": raw_paper.get("doi"),
        "abstract": abstract,
        "citations_count": citations,
        "open_access": open_access,
        "pdf_url": pdf_url,
        "source": raw_paper.get("source") or raw_paper.get("source_type") or "openalex",
        "venue": raw_paper.get("venue"),
        "keywords": keywords,
        "created_at": raw_paper.get("created_at"),
        "updated_at": raw_paper.get("updated_at"),
    }

    return payload


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
            papers = []
            if "error" not in advanced_results:
                # Convert advanced results to our format
                for paper_data in advanced_results.get("papers", []):
                    normalized = _prepare_paper_payload(paper_data, trace_id)
                    if normalized:
                        papers.append(normalized)
                if not papers:
                    logger.info(
                        "Advanced search returned no papers, falling back to basic search",
                        trace_id=trace_id,
                    )
            else:
                logger.warning("Advanced search failed, falling back to basic search", 
                             error=advanced_results.get("error"), trace_id=trace_id)
                # Fallback to basic search
                searcher = PaperSearcher()
                papers = await searcher.search_papers(
                    query=request.query,
                    limit=request.limit,
                    sources=request.sources,
                    filters=request.filters
                )
                try:
                    await searcher.close()
                except Exception:
                    pass

            if not papers:
                searcher = PaperSearcher()
                papers = await searcher.search_papers(
                    query=request.query,
                    limit=request.limit,
                    sources=request.sources,
                    filters=request.filters
                )
                try:
                    await searcher.close()
                except Exception:
                    pass
        else:
            logger.info("Using basic search engine", trace_id=trace_id)
            # Use basic search
            searcher = PaperSearcher()
            papers = await searcher.search_papers(
                query=request.query,
                limit=request.limit,
                sources=request.sources
            )
            try:
                await searcher.close()
            except Exception:
                pass
        
        # Extract papers from the response
        if isinstance(papers, dict) and "papers" in papers:
            papers_dict = papers["papers"]
        else:
            papers_dict = papers
        
        # Apply performance enhancements if requested
        if enhance:
            logger.info("Applying performance enhancements", trace_id=trace_id)
            papers_dict = await resolve_awaitable(
                performance_integration.enhance_paper_search(papers_dict)
            )
        
        # Extract research insights if requested
        insights = {}
        if extract_insights:
            logger.info("Extracting research insights", trace_id=trace_id)
            insights = await resolve_awaitable(
                performance_integration.extract_research_insights(papers_dict)
            )
        
        # Convert back to Paper objects
        enhanced_papers = []
        for paper_dict in papers_dict:
            normalized_payload = _prepare_paper_payload(paper_dict, trace_id)
            if not normalized_payload:
                continue

            # Attach enhanced metadata when available (silently ignored by Pydantic if unsupported)
            enhanced_metadata = {}
            if isinstance(paper_dict, dict):
                if 'enhanced_abstract' in paper_dict:
                    enhanced_metadata['enhanced_abstract'] = paper_dict['enhanced_abstract']
                if 'enhanced_title' in paper_dict:
                    enhanced_metadata['enhanced_title'] = paper_dict['enhanced_title']
                if 'scraped_content' in paper_dict:
                    enhanced_metadata['scraped_content'] = paper_dict['scraped_content']

            if enhanced_metadata:
                normalized_payload['metadata'] = enhanced_metadata

            try:
                enhanced_papers.append(Paper(**normalized_payload))
            except Exception as err:
                logger.warning(
                    "Skipping paper due to validation failure",
                    error=str(err),
                    paper_id=normalized_payload.get('id'),
                    trace_id=trace_id
                )
        
        # If no papers found, try fallback
        if not enhanced_papers:
            logger.warning("No papers found, trying fallback", query=request.query, trace_id=trace_id)
            fallback_response = api_fallback.get_fallback_response(request.query, "No results from APIs")
            fallback_papers = fallback_response.get("papers", [])
            
            # Convert fallback papers to Paper objects
            for paper_data in fallback_papers:
                try:
                    normalized = _prepare_paper_payload(paper_data, trace_id)
                    if normalized:
                        enhanced_papers.append(Paper(**normalized))
                except Exception as err:
                    logger.warning("Skipping fallback paper", error=str(err), trace_id=trace_id)
        
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
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=500,
            content={
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
