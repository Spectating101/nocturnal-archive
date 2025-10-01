"""
Enhanced Synthesis Service with Capability-Aware Groq Model Routing
Production-ready implementation with caching, error handling, and smart model selection
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

from src.config.settings import get_settings
from src.utils.resiliency import cache
from src.utils.error_handling import create_problem_response
from src.services.groq_router import GroqModelRouter, TaskComplexity

logger = structlog.get_logger(__name__)

class Synthesizer:
    """Production-ready synthesis with real LLM integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.groq_router = None
        self._init_groq_router()
        
    def _init_groq_router(self):
        """Initialize Groq model router with proper error handling"""
        try:
            # Unify API key loading via settings (avoid per-request env reads)
            api_key = (self.settings.groq_api_key
                       if getattr(self.settings, 'groq_api_key', None)
                       else os.getenv("GROQ_API_KEY"))
            if api_key:
                # Initialize router (will be async)
                self.groq_router = GroqModelRouter(api_key)
                logger.info("Groq model router initialized successfully")
            else:
                logger.warning("No Groq API key found - synthesis will use fallback")
                
        except ImportError:
            logger.warning("Groq library not available - synthesis will use fallback")
        except Exception as e:
            logger.error(f"Failed to initialize Groq router: {e}")
    
    @cache(ttl=7200, source_version="synthesis")  # 2 hour cache
    async def synthesize_papers(
        self, 
        paper_ids: List[str], 
        max_words: int = 500,
        focus: str = "key_findings",
        style: str = "academic",
        papers: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Synthesize papers with real LLM integration"""
        
        try:
            # Get paper details (this would integrate with your paper service)
            paper_details = papers if papers else await self._get_paper_details(paper_ids)
            
            if not paper_details:
                return {
                    "error": "No papers found for the provided IDs",
                    "summary": "",
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": 0
                }
            
            # Prepare synthesis prompt
            synthesis_prompt = self._build_synthesis_prompt(paper_details, max_words, focus, style)
            
            # Use capability-aware LLM routing for synthesis
            if self.groq_router:
                synthesis_result = await self._routed_synthesize(
                    synthesis_prompt, 
                    max_words, 
                    len(paper_details),
                    strict_mode=False
                )
            else:
                synthesis_result = self._fallback_synthesize(paper_details, focus)

            # Normalize unexpected types
            if not isinstance(synthesis_result, dict):
                synthesis_result = {
                    "summary": str(synthesis_result),
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": len(str(synthesis_result).split())
                }
            
            # Format response
            return {
                "summary": synthesis_result.get("summary", ""),
                "key_findings": list(synthesis_result.get("key_findings", []) or []),
                "citations_used": dict(synthesis_result.get("citations_used", {}) or {}),
                "word_count": int(synthesis_result.get("word_count", 0) or 0),
                "papers_synthesized": len(paper_details),
                "routing_metadata": synthesis_result.get("routing_metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                "error": f"Synthesis failed: {str(e)}",
                "summary": "",
                "key_findings": [],
                "citations_used": {},
                "word_count": 0
            }
    
    async def _get_paper_details(self, paper_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for papers via OpenAlex when possible; fallback to mock."""
        try:
            import aiohttp
        except ImportError:
            aiohttp = None

        async def _openalex_abstract_to_text(inv_idx: Dict[str, list]) -> str:
            if not isinstance(inv_idx, dict):
                return str(inv_idx) if inv_idx is not None else ""
            # Reconstruct abstract from inverted index
            max_pos = 0
            for word, positions in inv_idx.items():
                if positions:
                    max_pos = max(max_pos, max(positions))
            words = [""] * (max_pos + 1)
            for word, positions in inv_idx.items():
                for pos in positions:
                    if 0 <= pos < len(words):
                        words[pos] = word
            return " ".join(w for w in words if w)

        async def _fetch_openalex(ids: List[str]) -> List[Dict[str, Any]]:
            if aiohttp is None:
                return []
            base = "https://api.openalex.org/works"
            headers = {
                "User-Agent": "Nocturnal-Archive/1.0 (contact@nocturnal.dev)",
                "Accept": "application/json",
            }
            results: List[Dict[str, Any]] = []
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                for raw_id in ids:
                    # Normalize ID
                    openalex_id = str(raw_id)
                    if "/works/" in openalex_id:
                        openalex_id = openalex_id.split("/works/")[-1]
                    if openalex_id.startswith("openalex:"):
                        openalex_id = openalex_id.split(":", 1)[1]
                    url = f"{base}/{openalex_id}"
                    try:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                authors = []
                                for a in data.get("authorships", []):
                                    name = a.get("author", {}).get("display_name", "")
                                    if name:
                                        authors.append({"name": name})
                                venue = data.get("primary_location", {}).get("source", {}).get("display_name", "")
                                doi = data.get("doi", "")
                                if doi and doi.startswith("https://doi.org/"):
                                    doi = doi.replace("https://doi.org/", "")
                                abstract_idx = data.get("abstract_inverted_index", {})
                                abstract_txt = await _openalex_abstract_to_text(abstract_idx)
                                results.append({
                                    "id": data.get("id", "").split("/")[-1] or openalex_id,
                                    "title": data.get("title", ""),
                                    "authors": authors,
                                    "year": data.get("publication_year"),
                                    "doi": doi,
                                    "abstract": abstract_txt,
                                    "citations_count": data.get("cited_by_count", 0),
                                    "open_access": data.get("open_access", {}).get("is_oa", False),
                                    "pdf_url": data.get("open_access", {}).get("oa_url", ""),
                                    "source": "openalex",
                                    "venue": venue,
                                    "keywords": [c.get("display_name", "") for c in data.get("concepts", [])[:5]],
                                })
                            else:
                                continue
                    except Exception:
                        continue
            return results

        # Try fetching real details
        real = await _fetch_openalex(paper_ids)
        if real:
            return real

        # Fallback to minimal mock if nothing fetched
        papers: List[Dict[str, Any]] = []
        for i, paper_id in enumerate(paper_ids):
            papers.append({
                "id": paper_id,
                "title": f"Paper {i+1}",
                "authors": [{"name": f"Author {i+1}"}],
                "abstract": "",
                "year": 2024,
                "venue": "",
                "citations_count": 0
            })
        return papers
    
    def _build_synthesis_prompt(
        self, 
        papers: List[Dict], 
        max_words: int, 
        focus: str, 
        style: str
    ) -> str:
        """Build synthesis prompt for LLM"""
        
        # Prepare paper summaries
        paper_summaries = []
        for i, paper in enumerate(papers, 1):
            abstract = paper.get('abstract', 'No abstract available')
            if isinstance(abstract, dict):
                abstract = abstract.get('text', 'No abstract available')
            summary = f"""
Paper {i}: {paper.get('title', 'Untitled')}
Authors: {', '.join([author.get('name', '') for author in paper.get('authors', [])])}
Year: {paper.get('year', 'Unknown')}
Abstract: {abstract}
Citations: {paper.get('citations_count', 0)}
"""
            paper_summaries.append(summary)
        
        # Build the prompt
        prompt = f"""
You are a research synthesis expert. Please synthesize the following research papers into a comprehensive summary.

Focus: {focus}
Style: {style}
Maximum words: {max_words}

Papers to synthesize:
{chr(10).join(paper_summaries)}

Please provide:
1. A comprehensive summary that synthesizes the key findings across all papers
2. A list of 3-5 key findings with citations
3. Ensure the response is well-structured and academically rigorous

Format your response as JSON with the following structure:
{{
    "summary": "Your comprehensive synthesis here...",
    "key_findings": [
        "Finding 1 [1]",
        "Finding 2 [2]",
        "Finding 3 [1,2]"
    ],
    "citations_used": {{
        "[1]": "paper_id_1",
        "[2]": "paper_id_2"
    }},
    "word_count": 0
}}
"""
        
        return prompt
    
    async def _routed_synthesize(
        self, 
        prompt: str, 
        max_words: int, 
        paper_count: int,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """Use capability-aware model routing for synthesis"""
        try:
            def _strip_fences(text: str) -> str:
                if text is None:
                    return ""
                t = text.strip()
                if t.startswith("```"):
                    # remove first fence line
                    lines = t.splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    # remove trailing fence
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    return "\n".join(lines).strip()
                return t

            # Determine task complexity and routing requirements
            output_requirements = {
                'max_words': max_words,
                'paper_count': paper_count,
                'requires_reasoning': paper_count > 2 or max_words > 500,
                'safety_critical': False
            }
            
            # Use router for smart model selection
            messages = [
                {
                    "role": "system",
                    "content": "You are a research synthesis expert. Provide accurate, well-structured academic synthesis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            content, metadata = await self.groq_router.generate_with_routing(
                messages=messages,
                task_type="synthesis",
                output_requirements=output_requirements,
                strict_mode=strict_mode,
                max_tokens=min(max_words * 2, 4000),  # More generous token limit
                temperature=0.3
            )
            
            # Try to parse JSON response with sanitizer and placeholder detection
            try:
                clean = _strip_fences(content)
                result = json.loads(clean)
                # Add routing metadata
                result["routing_metadata"] = metadata
                # Enforce max_words trimming if provider returned verbose text
                summary = result.get("summary", "")
                if isinstance(summary, str):
                    words = summary.split()
                    if len(words) > max_words:
                        result["summary"] = " ".join(words[:max_words])
                # Placeholder detection
                placeholder_markers = ["[Insert", "[Paper", "Your comprehensive synthesis", "Sample abstract"]
                text_blob = (result.get("summary") or "") + "\n" + "\n".join(result.get("key_findings", []))
                if any(m in text_blob for m in placeholder_markers):
                    result["quality_warning"] = "LLM returned placeholder-like content; inputs may be insufficient."
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": _strip_fences(content),
                    "key_findings": [content[:100] + "..."],
                    "citations_used": {},
                    "word_count": len(content.split()),
                    "routing_metadata": metadata
                }
                
        except Exception as e:
            logger.error(f"Routed synthesis failed: {e}")
            raise
    
    def _fallback_synthesize(self, papers: List[Dict], focus: str) -> Dict[str, Any]:
        """Fallback synthesis when LLM is not available"""
        
        # Simple rule-based synthesis
        titles = [paper.get("title", "") for paper in papers]
        authors = []
        for paper in papers:
            authors.extend([author.get("name", "") for author in paper.get("authors", [])])
        
        summary = f"This synthesis covers {len(papers)} research papers focusing on {focus}. "
        summary += f"The papers include: {', '.join(titles[:3])}. "
        summary += f"Key authors include: {', '.join(list(set(authors))[:3])}. "
        summary += "The research demonstrates significant findings in the field."
        
        key_findings = []
        citations_used = {}
        
        for i, paper in enumerate(papers, 1):
            finding = f"Paper {i} presents important findings in {paper.get('venue', 'the field')} [1]"
            key_findings.append(finding)
            citations_used[f"[{i}]"] = paper.get("id", f"paper_{i}")
        
        return {
            "summary": summary,
            "key_findings": key_findings,
            "citations_used": citations_used,
            "word_count": len(summary.split())
        }
    
    async def synthesize_with_context(
        self,
        paper_ids: List[str],
        context: str,
        max_words: int = 500
    ) -> Dict[str, Any]:
        """Synthesize papers with additional context"""
        
        try:
            papers = await self._get_paper_details(paper_ids)
            
            if not papers:
                return {
                    "error": "No papers found for the provided IDs",
                    "summary": "",
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": 0
                }
            
            # Build context-aware prompt
            context_prompt = f"""
Context: {context}

Please synthesize the following papers in relation to this context:
{chr(10).join([f"- {paper.get('title', 'Untitled')}" for paper in papers])}

Focus on how these papers relate to the provided context.
"""
            
            if self.llm_client:
                synthesis_result = await self._llm_synthesize(context_prompt, max_words)
            else:
                synthesis_result = self._fallback_synthesize(papers, "contextual analysis")
            
            return {
                "summary": synthesis_result["summary"],
                "key_findings": synthesis_result["key_findings"],
                "citations_used": synthesis_result["citations_used"],
                "word_count": synthesis_result["word_count"],
                "context_used": context,
                "papers_synthesized": len(papers),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context synthesis failed: {e}")
            return {
                "error": f"Context synthesis failed: {str(e)}",
                "summary": "",
                "key_findings": [],
                "citations_used": {},
                "word_count": 0
            }
    
    @cache(ttl=7200, source_version="synthesis_strict")  # 2 hour cache
    async def synthesize_papers_strict(
        self, 
        paper_ids: List[str], 
        max_words: int = 500,
        focus: str = "key_findings",
        style: str = "academic"
    ) -> Dict[str, Any]:
        """Strict synthesis requiring heavy model capability (70B+ models)"""
        
        try:
            # Get paper details
            papers = await self._get_paper_details(paper_ids)
            
            if not papers:
                return {
                    "error": "No papers found for the provided IDs",
                    "summary": "",
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": 0
                }
            
            # Check if we have Groq router available
            if not self.groq_router:
                return {
                    "error": "Strict synthesis requires Groq LLM access",
                    "summary": "",
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": 0
                }
            
            # Prepare synthesis prompt
            synthesis_prompt = self._build_synthesis_prompt(papers, max_words, focus, style)
            
            # Use strict mode routing (requires heavy model)
            synthesis_result = await self._routed_synthesize(
                synthesis_prompt, 
                max_words, 
                len(papers),
                strict_mode=True  # This will fail if no heavy model available
            )
            
            # Normalize unexpected types
            if not isinstance(synthesis_result, dict):
                synthesis_result = {
                    "summary": str(synthesis_result),
                    "key_findings": [],
                    "citations_used": {},
                    "word_count": len(str(synthesis_result).split())
                }
            
            # Format response with strict mode indicator
            return {
                "summary": synthesis_result.get("summary", ""),
                "key_findings": list(synthesis_result.get("key_findings", []) or []),
                "citations_used": dict(synthesis_result.get("citations_used", {}) or {}),
                "word_count": int(synthesis_result.get("word_count", 0) or 0),
                "papers_synthesized": len(papers),
                "synthesis_mode": "strict",
                "routing_metadata": synthesis_result.get("routing_metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except RuntimeError as e:
            # This is thrown when no suitable heavy model is available
            logger.warning(f"Strict synthesis failed - no heavy model available: {e}")
            return {
                "error": "Strict synthesis requires a heavy model (70B+) but none are available",
                "summary": "",
                "key_findings": [],
                "citations_used": {},
                "word_count": 0,
                "synthesis_mode": "strict",
                "fallback_suggestion": "Try the regular /synthesize endpoint for fallback synthesis"
            }
            
        except Exception as e:
            logger.error(f"Strict synthesis failed: {e}")
            return {
                "error": f"Strict synthesis failed: {str(e)}",
                "summary": "",
                "key_findings": [],
                "citations_used": {},
                "word_count": 0,
                "synthesis_mode": "strict"
            }