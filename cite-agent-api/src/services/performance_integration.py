"""
Performance integration service - bridges FastAPI with Rust performance layer
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Import the performance service from the main research engine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

try:
    from services.performance_service.rust_performance import HighPerformanceService, ScrapedContent, ProcessedText
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    # Define fallback classes
    from dataclasses import dataclass
    from datetime import datetime, timezone
    from typing import Dict, List
    
    @dataclass
    class ScrapedContent:
        url: str
        title: str
        content: str
        metadata: Dict[str, str]
        timestamp: datetime
    
    @dataclass
    class ProcessedText:
        original: str
        cleaned: str
        chunks: List[str]
        keywords: List[str]
        summary: str
    
    class HighPerformanceService:
        def __init__(self, max_concurrent: int = 10):
            self.max_concurrent = max_concurrent
        
        async def scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
            return []  # Placeholder
        
        async def process_text_batch(self, texts: List[str]) -> List[ProcessedText]:
            return []  # Placeholder

logger = structlog.get_logger(__name__)


class PerformanceIntegration:
    """Integration layer between FastAPI and Rust performance components"""
    
    def __init__(self):
        self.performance_service = HighPerformanceService(max_concurrent=20)
        self.cache = {}  # Simple in-memory cache for now
        self.cache_ttl = 3600  # 1 hour
        self.rust_available = RUST_AVAILABLE
    
    async def enhance_paper_search(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance paper search results with performance optimizations"""
        
        if not self.rust_available:
            logger.info("Rust performance layer not available, returning papers without enhancement")
            return papers
        
        enhanced_papers = []
        
        for paper in papers:
            try:
                # Extract URLs for scraping
                urls_to_scrape = []
                if paper.get('pdf_url'):
                    urls_to_scrape.append(paper['pdf_url'])
                
                # Scrape additional content if available
                scraped_content = []
                if urls_to_scrape:
                    scraped_content = await self.performance_service.scrape_urls(urls_to_scrape)
                
                # Process abstract for better analysis
                abstract = paper.get('abstract', '')
                if abstract:
                    processed_text = await self.performance_service.process_text_batch([abstract])
                    if processed_text:
                        processed = processed_text[0]
                        
                        # Add enhanced metadata
                        paper['enhanced_abstract'] = {
                            'cleaned': processed.cleaned,
                            'keywords': processed.keywords,
                            'summary': processed.summary,
                            'chunks': processed.chunks
                        }
                
                # Add scraped content metadata
                if scraped_content:
                    paper['scraped_content'] = {
                        'title': scraped_content[0].title,
                        'content_preview': scraped_content[0].content[:500] + '...' if len(scraped_content[0].content) > 500 else scraped_content[0].content,
                        'metadata': scraped_content[0].metadata,
                        'scraped_at': scraped_content[0].timestamp.isoformat()
                    }
                
                enhanced_papers.append(paper)
                
            except Exception as e:
                logger.warning(f"Failed to enhance paper {paper.get('id', 'unknown')}: {e}")
                enhanced_papers.append(paper)  # Return original if enhancement fails
        
        return enhanced_papers
    
    async def enhance_synthesis(self, papers: List[Dict[str, Any]], synthesis_text: str) -> Dict[str, Any]:
        """Enhance synthesis with performance optimizations"""
        
        try:
            # Extract all abstracts for processing
            abstracts = [paper.get('abstract', '') for paper in papers if paper.get('abstract')]
            
            if abstracts:
                # Process abstracts in batch
                processed_texts = await self.performance_service.process_text_batch(abstracts)
                
                # Extract common keywords across all papers
                all_keywords = []
                for processed in processed_texts:
                    all_keywords.extend(processed.keywords)
                
                # Get unique keywords with frequency
                from collections import Counter
                keyword_freq = Counter(all_keywords)
                top_keywords = [word for word, count in keyword_freq.most_common(20)]
                
                # Process synthesis text for better formatting
                synthesis_processed = await self.performance_service.process_text_batch([synthesis_text])
                enhanced_synthesis = synthesis_processed[0] if synthesis_processed else None
                
                return {
                    'enhanced_synthesis': {
                        'original': synthesis_text,
                        'cleaned': enhanced_synthesis.cleaned if enhanced_synthesis else synthesis_text,
                        'keywords': top_keywords,
                        'key_phrases': enhanced_synthesis.keywords if enhanced_synthesis else [],
                        'summary': enhanced_synthesis.summary if enhanced_synthesis else synthesis_text[:200] + '...'
                    },
                    'paper_insights': {
                        'total_papers': len(papers),
                        'processed_abstracts': len(processed_texts),
                        'common_keywords': top_keywords,
                        'processing_timestamp': datetime.now(timezone.utc).isoformat()
                    }
                }
            
        except Exception as e:
            logger.error(f"Failed to enhance synthesis: {e}")
        
        return {
            'enhanced_synthesis': {
                'original': synthesis_text,
                'cleaned': synthesis_text,
                'keywords': [],
                'key_phrases': [],
                'summary': synthesis_text[:200] + '...' if len(synthesis_text) > 200 else synthesis_text
            },
            'paper_insights': {
                'total_papers': len(papers),
                'processed_abstracts': 0,
                'common_keywords': [],
                'processing_timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def batch_process_citations(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch process citations for better formatting and analysis"""
        
        try:
            # Extract titles and abstracts for processing
            titles = [paper.get('title', '') for paper in papers]
            abstracts = [paper.get('abstract', '') for paper in papers if paper.get('abstract')]
            
            # Process titles and abstracts in parallel
            title_tasks = [self.performance_service.process_text_batch([title]) for title in titles]
            abstract_tasks = [self.performance_service.process_text_batch([abstract]) for abstract in abstracts] if abstracts else []
            
            # Wait for all processing to complete
            title_results = await asyncio.gather(*title_tasks, return_exceptions=True)
            abstract_results = await asyncio.gather(*abstract_tasks, return_exceptions=True) if abstract_tasks else []
            
            # Enhance papers with processed data
            enhanced_papers = []
            for i, paper in enumerate(papers):
                enhanced_paper = paper.copy()
                
                # Add processed title data
                if i < len(title_results) and not isinstance(title_results[i], Exception):
                    title_processed = title_results[i][0] if title_results[i] else None
                    if title_processed:
                        enhanced_paper['enhanced_title'] = {
                            'cleaned': title_processed.cleaned,
                            'keywords': title_processed.keywords,
                            'summary': title_processed.summary
                        }
                
                # Add processed abstract data
                if paper.get('abstract') and i < len(abstract_results) and not isinstance(abstract_results[i], Exception):
                    abstract_processed = abstract_results[i][0] if abstract_results[i] else None
                    if abstract_processed:
                        enhanced_paper['enhanced_abstract'] = {
                            'cleaned': abstract_processed.cleaned,
                            'keywords': abstract_processed.keywords,
                            'summary': abstract_processed.summary,
                            'chunks': abstract_processed.chunks
                        }
                
                enhanced_papers.append(enhanced_paper)
            
            return enhanced_papers
            
        except Exception as e:
            logger.error(f"Failed to batch process citations: {e}")
            return papers  # Return original papers if processing fails
    
    async def extract_research_insights(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract research insights using performance optimizations"""
        
        try:
            # Collect all text content
            all_texts = []
            for paper in papers:
                if paper.get('title'):
                    all_texts.append(paper['title'])
                if paper.get('abstract'):
                    all_texts.append(paper['abstract'])
            
            if not all_texts:
                return {'insights': {}, 'processing_time': 0}
            
            start_time = datetime.now(timezone.utc)
            
            # Process all texts in batch
            processed_texts = await self.performance_service.process_text_batch(all_texts)
            
            # Extract insights
            all_keywords = []
            all_chunks = []
            
            for processed in processed_texts:
                all_keywords.extend(processed.keywords)
                all_chunks.extend(processed.chunks)
            
            # Analyze keyword frequency
            from collections import Counter
            keyword_freq = Counter(all_keywords)
            top_keywords = [{'word': word, 'frequency': count} for word, count in keyword_freq.most_common(30)]
            
            # Calculate processing time
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                'insights': {
                    'total_papers': len(papers),
                    'total_text_chunks': len(all_chunks),
                    'unique_keywords': len(set(all_keywords)),
                    'top_keywords': top_keywords,
                    'average_chunk_size': sum(len(chunk) for chunk in all_chunks) / len(all_chunks) if all_chunks else 0,
                    'processing_timestamp': datetime.now(timezone.utc).isoformat()
                },
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to extract research insights: {e}")
            return {'insights': {}, 'processing_time': 0}


# Global instance
performance_integration = PerformanceIntegration()
