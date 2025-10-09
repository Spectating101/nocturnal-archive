"""
Citation Verification Service
Extracts and verifies citations from LLM responses
"""

import re
import httpx
import asyncio
from typing import Dict, List, Any
from urllib.parse import urlparse
import structlog

logger = structlog.get_logger(__name__)


class CitationVerifier:
    """Verify citations in LLM responses"""
    
    # Citation patterns
    URL_PATTERN = r'https?://[^\s\)\]\}]+'
    DOI_PATTERN = r'10\.\d{4,}/[^\s\)\]\}]+'
    ARXIV_PATTERN = r'arxiv:\d+\.\d+'
    AUTHOR_YEAR_PATTERN = r'\[([A-Z][a-z]+\s+(?:et al\.\s+)?\d{4})\]'
    
    # Quote patterns (for qualitative analysis)
    QUOTE_PATTERN = r'"([^"]+)"'  # Text in quotes
    ATTRIBUTION_PATTERN = r'—\s*([^,\n]+)(?:,\s*(?:p\.|line)\s*(\d+))?'  # — Author, p. X
    
    def __init__(self, timeout: int = 5, max_concurrent: int = 10):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
    
    def extract_citations(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all citations from text
        
        Returns:
            {
                'urls': [...],
                'dois': [...],
                'arxiv_ids': [...],
                'author_year': [...]
            }
        """
        citations = {
            'urls': re.findall(self.URL_PATTERN, text),
            'dois': re.findall(self.DOI_PATTERN, text),
            'arxiv_ids': re.findall(self.ARXIV_PATTERN, text),
            'author_year': re.findall(self.AUTHOR_YEAR_PATTERN, text)
        }
        
        # Remove duplicates
        for key in citations:
            citations[key] = list(set(citations[key]))
        
        return citations
    
    def has_citations(self, text: str) -> bool:
        """Check if text has any recognizable citations"""
        citations = self.extract_citations(text)
        return any(len(v) > 0 for v in citations.values())
    
    def count_citations(self, text: str) -> int:
        """Count total number of citations"""
        citations = self.extract_citations(text)
        return sum(len(v) for v in citations.values())
    
    def extract_quotes(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract quoted text (for qualitative analysis)
        
        Returns list of:
        {
            'quote': str,
            'attribution': str | None,  # e.g. "Interview 2, line 45"
            'context_before': str | None,
            'context_after': str | None
        }
        """
        quotes = []
        
        # Find all quoted text
        for match in re.finditer(self.QUOTE_PATTERN, text):
            quote_text = match.group(1)
            quote_start = match.start()
            quote_end = match.end()
            
            # Get context (50 chars before/after)
            context_before = text[max(0, quote_start - 50):quote_start].strip()
            context_after = text[quote_end:min(len(text), quote_end + 50)].strip()
            
            # Look for attribution right after quote
            attribution = None
            remaining_text = text[quote_end:min(len(text), quote_end + 100)]
            attr_match = re.search(self.ATTRIBUTION_PATTERN, remaining_text)
            if attr_match:
                source = attr_match.group(1)
                page_or_line = attr_match.group(2)
                if page_or_line:
                    attribution = f"{source}, {'p' if 'p.' in remaining_text else 'line'} {page_or_line}"
                else:
                    attribution = source
            
            quotes.append({
                'quote': quote_text,
                'attribution': attribution,
                'context_before': context_before,
                'context_after': context_after
            })
        
        return quotes
    
    def count_quotes(self, text: str) -> int:
        """Count number of quotes in text"""
        return len(re.findall(self.QUOTE_PATTERN, text))
    
    async def verify_url(self, url: str) -> Dict[str, Any]:
        """
        Verify a single URL
        
        Returns:
            {
                'url': str,
                'status': 'verified' | 'broken' | 'timeout' | 'error',
                'status_code': int | None,
                'title': str | None
            }
        """
        try:
            async with httpx.AsyncClient() as client:
                # Try HEAD first (faster)
                response = await client.head(
                    url, 
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    return {
                        'url': url,
                        'status': 'verified',
                        'status_code': 200,
                        'title': None  # Could extract from GET if needed
                    }
                elif response.status_code == 405:  # HEAD not allowed, try GET
                    response = await client.get(
                        url,
                        timeout=self.timeout,
                        follow_redirects=True
                    )
                    if response.status_code == 200:
                        return {
                            'url': url,
                            'status': 'verified',
                            'status_code': 200,
                            'title': self._extract_title(response.text)
                        }
                
                return {
                    'url': url,
                    'status': 'broken',
                    'status_code': response.status_code,
                    'title': None
                }
                
        except asyncio.TimeoutError:
            return {
                'url': url,
                'status': 'timeout',
                'status_code': None,
                'title': None
            }
        except Exception as e:
            logger.warning(f"URL verification failed", url=url, error=str(e))
            return {
                'url': url,
                'status': 'error',
                'status_code': None,
                'title': None
            }
    
    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML"""
        match = re.search(r'<title>(.+?)</title>', html, re.IGNORECASE)
        return match.group(1) if match else None
    
    async def verify_all_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Verify all URLs concurrently
        
        Returns:
            {
                'total': int,
                'verified': int,
                'broken': int,
                'timeout': int,
                'error': int,
                'details': [...]
            }
        """
        if not urls:
            return {
                'total': 0,
                'verified': 0,
                'broken': 0,
                'timeout': 0,
                'error': 0,
                'details': []
            }
        
        # Verify URLs concurrently (with limit)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def verify_with_semaphore(url):
            async with semaphore:
                return await self.verify_url(url)
        
        results = await asyncio.gather(
            *[verify_with_semaphore(url) for url in urls],
            return_exceptions=True
        )
        
        # Handle exceptions
        results = [
            r if not isinstance(r, Exception) 
            else {'url': urls[i], 'status': 'error', 'status_code': None, 'title': None}
            for i, r in enumerate(results)
        ]
        
        # Count by status
        status_counts = {
            'total': len(results),
            'verified': sum(1 for r in results if r['status'] == 'verified'),
            'broken': sum(1 for r in results if r['status'] == 'broken'),
            'timeout': sum(1 for r in results if r['status'] == 'timeout'),
            'error': sum(1 for r in results if r['status'] == 'error'),
            'details': results
        }
        
        return status_counts
    
    async def verify_response(self, response_text: str) -> Dict[str, Any]:
        """
        Verify all citations in a response (quantitative + qualitative)
        
        Returns:
            {
                'has_citations': bool,
                'total_citations': int,
                'citations': {...},  # by type
                'url_verification': {...},  # verification results
                'quotes': [...],  # extracted quotes (qualitative)
                'quote_count': int,
                'quality_score': float  # 0-1
            }
        """
        citations = self.extract_citations(response_text)
        url_verification = await self.verify_all_urls(citations['urls'])
        
        # Extract quotes (for qualitative analysis)
        quotes = self.extract_quotes(response_text)
        quote_count = len(quotes)
        
        total_citations = sum(len(v) for v in citations.values())
        has_citations = total_citations > 0 or quote_count > 0  # Quotes also count
        
        # Calculate quality score
        if total_citations == 0 and quote_count == 0:
            quality_score = 0.0
        else:
            # URLs get weighted for quantitative, quotes for qualitative
            url_weight = 0.5
            quote_weight = 0.3
            other_weight = 0.2
            
            url_score = (
                url_verification['verified'] / url_verification['total']
                if url_verification['total'] > 0 else 0
            )
            
            # Quote score: quotes with attribution are better
            attributed_quotes = sum(1 for q in quotes if q['attribution'])
            quote_score = (
                attributed_quotes / quote_count
                if quote_count > 0 else 0
            )
            
            other_citations = sum(
                len(v) for k, v in citations.items() 
                if k != 'urls'
            )
            other_score = 1.0 if other_citations > 0 else 0
            
            # Adjust weights based on what's present
            if url_verification['total'] == 0 and quote_count > 0:
                # Qualitative response: prioritize quotes
                quality_score = 0.7 * quote_score + 0.3 * other_score
            elif quote_count == 0 and url_verification['total'] > 0:
                # Quantitative response: prioritize URLs
                quality_score = 0.7 * url_score + 0.3 * other_score
            else:
                # Mixed: use all three
                quality_score = (
                    url_weight * url_score + 
                    quote_weight * quote_score +
                    other_weight * other_score
                )
        
        return {
            'has_citations': has_citations,
            'total_citations': total_citations,
            'citations': citations,
            'url_verification': url_verification,
            'quotes': quotes,  # NEW: for qualitative
            'quote_count': quote_count,  # NEW
            'quality_score': quality_score
        }


# Singleton instance
_verifier = None

def get_verifier() -> CitationVerifier:
    """Get singleton verifier instance"""
    global _verifier
    if _verifier is None:
        _verifier = CitationVerifier()
    return _verifier

