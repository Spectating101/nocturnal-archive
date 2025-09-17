#search_engine.py
from typing import List, Dict, Optional
import asyncio
import redis.asyncio as redis
import json
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
import os
import aiohttp
from ...utils.logger import logger, log_operation
from ...storage.db.operations import DatabaseOperations
from ...storage.db.models import SearchResult, Paper
from ..llm_service.embeddings import EmbeddingManager
from ..rerank.reranker import Reranker

class SearchEngine:
    def __init__(self, db_ops: DatabaseOperations, redis_url: str):
        #logger.info("Initializing SearchEngine")
        self.db = db_ops
        self.redis_client = redis.from_url(redis_url)
        from .vector_search import VectorSearchEngine
        self.vector_search = VectorSearchEngine(redis_url=redis_url)
        self.embeddings = EmbeddingManager()
        self.reranker = Reranker()
        self.vector_store = None
        self._initialize_lock = asyncio.Lock()
        self.active_searches: Dict[str, Dict] = {}
        #logger.info("SearchEngine initialized")

    @log_operation("start_search_session")
    async def start_search_session(self, session_id: str, query: str, context: Optional[Dict] = None) -> str:
        """Start a new search session with context."""
        #logger.info(f"Starting search session for: {query}")
        
        search_id = f"search:{session_id}:{datetime.utcnow().isoformat()}"
        self.active_searches[search_id] = {
            "session_id": session_id,
            "query": query,
            "context": context or {},
            "status": "starting",
            "results": [],
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Start async search process
        asyncio.create_task(self._conduct_search(search_id))
        return search_id

    async def _conduct_search(self, search_id: str):
        """Conduct comprehensive search with progress tracking."""
        search = self.active_searches[search_id]
        try:
            await self._update_search_status(search_id, "searching")
            
            # Run searches concurrently
            semantic_results, keyword_results = await asyncio.gather(
                self.semantic_search(search["query"]),
                self.keyword_search(search["query"])
            )
            
            # Combine results
            combined_results = await self._combine_results(
                semantic_results,
                keyword_results,
                search["context"]
            )
            
            # Optional re-ranking
            try:
                ranked = await self._rerank_results(search["query"], combined_results)
            except Exception:
                ranked = combined_results

            # Store results
            self.active_searches[search_id]["results"] = ranked
            await self._update_search_status(search_id, "completed")
            
            # Notify completion
            await self.redis_client.publish(
                "search_updates",
                json.dumps({
                    "search_id": search_id,
                    "status": "completed",
                    "result_count": len(combined_results)
                })
            )
            
        except Exception as e:
            logger.error(f"Error in search {search_id}: {str(e)}")
            await self._update_search_status(search_id, "error", str(e))

    @log_operation("semantic_search")
    async def semantic_search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Perform semantic search with retries."""
        # Use Qdrant similarity search
        try:
            pairs = await self.vector_search.similarity_search_with_score(query, k=limit)
            results = []
            for doc, score in pairs:
                results.append(
                    SearchResult(
                        paper_id=doc.get('metadata', {}).get('paper_id'),
                        score=float(score),
                        content=doc.get('page_content', ''),
                        metadata=doc.get('metadata', {})
                    )
                )
            if results:
                return results
        except Exception as e:
            logger.error(f"Vector search error: {e}")
        # Fallback
        return await self.keyword_search(query)

    @log_operation("keyword_search")
    async def keyword_search(self, query: str, fields: List[str] = None) -> List[Paper]:
        """Perform keyword search with field boosting."""
        if not fields:
            fields = {
                'title': 2.0,  # Title matches are more important
                'abstract': 1.5,  # Abstract matches are somewhat important
                'content': 1.0  # Content matches have normal weight
            }
        
        results = []
        for field, boost in fields.items():
            field_results = await self.db.search_papers({
                field: {"$regex": query, "$options": "i"}
            })
            for paper in field_results:
                paper.score = paper.score * boost if hasattr(paper, 'score') else boost
                results.append(paper)
        
        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for paper in sorted(results, key=lambda x: getattr(x, 'score', 0), reverse=True):
            if paper.id not in seen:
                seen.add(paper.id)
                unique_results.append(paper)
        
        return unique_results

    async def _combine_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[Paper],
        context: Dict
    ) -> List[SearchResult]:
        """Combine and rank results considering search context."""
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            combined[result.paper_id] = {
                "result": result,
                "semantic_score": result.score,
                "keyword_score": 0.0
            }
        
        # Add keyword results
        for paper in keyword_results:
            if paper.id in combined:
                combined[paper.id]["keyword_score"] = getattr(paper, 'score', 0.5)
            else:
                combined[paper.id] = {
                    "result": SearchResult(
                        paper_id=paper.id,
                        score=getattr(paper, 'score', 0.5),
                        content="",
                        metadata=paper.metadata
                    ),
                    "semantic_score": 0.0,
                    "keyword_score": getattr(paper, 'score', 0.5)
                }
        
        # Calculate final scores considering context
        results = []
        for paper_id, scores in combined.items():
            context_boost = self._calculate_context_boost(scores["result"], context)
            final_score = (
                scores["semantic_score"] * 0.6 +
                scores["keyword_score"] * 0.3 +
                context_boost * 0.1
            )
            results.append(
                SearchResult(
                    paper_id=paper_id,
                    score=final_score,
                    content=scores["result"].content,
                    metadata={
                        **scores["result"].metadata,
                        "semantic_score": scores["semantic_score"],
                        "keyword_score": scores["keyword_score"],
                        "context_boost": context_boost
                    }
                )
            )
        
        return sorted(results, key=lambda x: x.score, reverse=True)

    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        docs = [
            {
                "content": r.content or "",
                "metadata": r.metadata,
                "paper_id": r.paper_id,
                "score": r.score
            }
            for r in results
        ]
        ranked_docs = await self.reranker.rerank(query, docs, top_k=len(docs))
        # Map back to SearchResult
        mapped = []
        for d in ranked_docs:
            mapped.append(
                SearchResult(
                    paper_id=d.get("paper_id"),
                    score=float(d.get("rerank_score", d.get("score", 0))),
                    content=d.get("content", ""),
                    metadata=d.get("metadata", {})
                )
            )
        return mapped

    def _calculate_context_boost(self, result: SearchResult, context: Dict) -> float:
        """Calculate context-based boost for a result."""
        boost = 1.0
        
        if not context:
            return boost
            
        # Boost based on publication date if time range is important
        if context.get("time_range"):
            try:
                pub_year = int(result.metadata.get("publication_year", 0))
                if pub_year >= context["time_range"]["start"]:
                    boost *= 1.2
            except:
                pass
        
        # Boost based on methodology if specified
        if context.get("methodology"):
            if result.metadata.get("methodology") == context["methodology"]:
                boost *= 1.3

        # Boost based on topic relevance
        if context.get("topics"):
            result_topics = result.metadata.get("topics", [])
            matching_topics = set(context["topics"]) & set(result_topics)
            if matching_topics:
                boost *= (1 + (len(matching_topics) * 0.1))

        # Boost based on citation count if academic impact is important
        if context.get("prioritize_citations"):
            citations = result.metadata.get("citation_count", 0)
            if citations > 100:
                boost *= 1.4
            elif citations > 50:
                boost *= 1.2
            elif citations > 10:
                boost *= 1.1

        return boost

    async def _update_search_status(self, search_id: str, status: str, error: str = None):
        """Update search status in Redis."""
        self.active_searches[search_id]["status"] = status
        if error:
            self.active_searches[search_id]["error"] = error

        await self.redis_client.hset(
            f"search_status:{search_id}",
            mapping={
                "status": status,
                "error": error or "",
                "updated_at": datetime.utcnow().isoformat()
            }
        )

    @log_operation("get_search_status")
    async def get_search_status(self, search_id: str) -> Dict:
        """Get current status of a search operation."""
        if search_id not in self.active_searches:
            return {"error": "Search not found"}

        search = self.active_searches[search_id]
        return {
            "status": search["status"],
            "query": search["query"],
            "result_count": len(search.get("results", [])),
            "started_at": search["started_at"],
            "error": search.get("error")
        }

    async def cleanup(self):
        """Cleanup search engine resources."""
        try:
            # Close Redis connection
            await self.redis_client.close()
            
            # Clear search cache
            self.active_searches.clear()
            
            # Clear vector store
            self.vector_store = None
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    # Add to src/services/search_service/search_engine.py

    async def web_search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Perform web search to complement academic searches"""
        #logger.info(f"Performing web search for: {query}")
        
        api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
        engine_id = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        if not api_key or not engine_id:
            logger.warning("Google Search API key or engine ID not configured")
            return []
        
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": engine_id,
            "q": query,
            "num": min(num_results, 10)  # Google CSE limits to 10 per call
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Web search error: {response.status} - {error_text}")
                        return []
                    
                    data = await response.json()
                    
                    results = []
                    if "items" in data:
                        for item in data["items"]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", ""),
                                "source": "web_search"
                            })
                    
                    #logger.info(f"Web search found {len(results)} results for: {query}")
                    return results
                    
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return []

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch and extract content from a web page"""
        #logger.info(f"Fetching content from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch URL {url}: {response.status}")
                        return None
                    
                    html = await response.text()
                    
                    # Basic extraction - in a real implementation, use a proper
                    # HTML parser like BeautifulSoup, Trafilatura, etc.
                    # This is just a simple placeholder
                    import re
                    no_script = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', '', html)
                    no_style = re.sub(r'<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>', '', no_script)
                    no_tags = re.sub(r'<[^>]+>', ' ', no_style)
                    cleaned = re.sub(r'\s+', ' ', no_tags).strip()
                    
                    return cleaned[:5000]  # Limit to 5000 chars
                    
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return None
    