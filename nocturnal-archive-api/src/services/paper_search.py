"""
Paper search service - OpenAlex integration
"""

import structlog
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.paper import Paper, Author
from src.models.request import SearchFilters

logger = structlog.get_logger(__name__)


class PaperSearcher:
    """Paper search service using OpenAlex API"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.openalex.org"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        sources: List[str] = None,
        filters: Optional[SearchFilters] = None
    ) -> List[Paper]:
        """Search for papers using OpenAlex API"""
        
        if sources is None:
            sources = ["openalex"]
        
        papers = []
        
        for source in sources:
            if source == "openalex":
                source_papers = await self._search_openalex(query, limit, filters)
                papers.extend(source_papers)
            # TODO: Add PubMed and arXiv sources
        
        # Remove duplicates and limit results
        unique_papers = self._deduplicate_papers(papers)
        return unique_papers[:limit]
    
    async def _search_openalex(
        self,
        query: str,
        limit: int,
        filters: Optional[SearchFilters] = None
    ) -> List[Paper]:
        """Search OpenAlex API"""
        
        try:
            # Build search parameters
            params = {
                "search": query,
                "per-page": min(limit, 200),  # OpenAlex max per page
                "page": 1,
                "sort": "cited_by_count:desc"
            }
            
            # Add filters
            if filters:
                if filters.year_min:
                    params["filter"] = f"publication_year:>={filters.year_min}"
                if filters.year_max:
                    existing_filter = params.get("filter", "")
                    if existing_filter:
                        params["filter"] = f"{existing_filter},publication_year:<={filters.year_max}"
                    else:
                        params["filter"] = f"publication_year:<={filters.year_max}"
                
                if filters.open_access:
                    existing_filter = params.get("filter", "")
                    if existing_filter:
                        params["filter"] = f"{existing_filter},is_oa:true"
                    else:
                        params["filter"] = "is_oa:true"
            
            # Make API request
            response = await self.client.get(f"{self.base_url}/works", params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for work in data.get("results", []):
                paper = self._parse_openalex_work(work)
                if paper:
                    papers.append(paper)
            
            logger.info(
                "OpenAlex search completed",
                query=query,
                results_count=len(papers),
                total_found=data.get("meta", {}).get("count", 0)
            )
            
            return papers
        
        except httpx.HTTPError as e:
            logger.error("OpenAlex API error", error=str(e), query=query)
            raise Exception(f"OpenAlex API error: {str(e)}")
        except Exception as e:
            logger.error("OpenAlex search failed", error=str(e), query=query)
            raise
    
    def _parse_openalex_work(self, work: Dict[str, Any]) -> Optional[Paper]:
        """Parse OpenAlex work data into Paper model"""
        
        try:
            # Extract basic information
            paper_id = work.get("id", "").split("/")[-1]  # Extract ID from URL
            title = work.get("title", "")
            
            if not title:
                return None
            
            # Extract authors
            authors = []
            for author_data in work.get("authorships", []):
                author = author_data.get("author", {})
                if author:
                    author_name = author.get("display_name", "")
                    if author_name:
                        authors.append(Author(
                            name=author_name,
                            orcid=author.get("orcid"),
                            affiliation=author_data.get("institutions", [{}])[0].get("display_name") if author_data.get("institutions") else None
                        ))
            
            # Extract publication info
            publication_date = work.get("publication_date", "")
            year = None
            if publication_date:
                try:
                    year = int(publication_date.split("-")[0])
                except (ValueError, IndexError):
                    pass
            
            # Extract venue
            venue = None
            primary_location = work.get("primary_location", {})
            if primary_location:
                source = primary_location.get("source", {})
                venue = source.get("display_name")
            
            # Extract abstract
            abstract = work.get("abstract_inverted_index")
            abstract_text = None
            if abstract:
                # Reconstruct abstract from inverted index
                abstract_text = self._reconstruct_abstract(abstract)
            
            # Extract keywords
            keywords = []
            concepts = work.get("concepts", [])
            for concept in concepts[:10]:  # Top 10 concepts
                if concept.get("score", 0) > 0.3:  # Only high-confidence concepts
                    keywords.append(concept.get("display_name", ""))
            
            return Paper(
                id=paper_id,
                title=title,
                authors=authors,
                year=year or 0,
                doi=work.get("doi"),
                abstract=abstract_text,
                citations_count=work.get("cited_by_count", 0),
                open_access=work.get("open_access", {}).get("is_oa", False),
                pdf_url=work.get("open_access", {}).get("oa_url"),
                source="openalex",
                venue=venue,
                keywords=keywords,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.warning("Failed to parse OpenAlex work", error=str(e), work_id=work.get("id"))
            return None
    
    def _reconstruct_abstract(self, abstract_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract from OpenAlex inverted index"""
        
        try:
            # Create a list of (position, word) tuples
            words_with_positions = []
            for word, positions in abstract_index.items():
                for pos in positions:
                    words_with_positions.append((pos, word))
            
            # Sort by position
            words_with_positions.sort(key=lambda x: x[0])
            
            # Join words
            abstract = " ".join([word for _, word in words_with_positions])
            return abstract
        
        except Exception:
            return ""
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on DOI or title"""
        
        seen = set()
        unique_papers = []
        
        for paper in papers:
            # Use DOI as primary key, fallback to title
            key = paper.doi or paper.title.lower().strip()
            
            if key not in seen:
                seen.add(key)
                unique_papers.append(paper)
        
        return unique_papers
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
