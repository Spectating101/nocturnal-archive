"""
API Fallback Utilities
Provides fallback responses when APIs fail
"""

import structlog
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

logger = structlog.get_logger(__name__)

class APIFallback:
    """Provides fallback responses when external APIs fail"""
    
    def __init__(self):
        self.offline_data_path = Path(__file__).parent.parent / "data" / "offline_papers.json"
        self._offline_cache: Optional[List[Dict[str, Any]]] = None
    
    def get_offline_papers(self) -> List[Dict[str, Any]]:
        """Get offline paper data as fallback"""
        if self._offline_cache is None:
            try:
                if self.offline_data_path.exists():
                    with open(self.offline_data_path, 'r') as f:
                        self._offline_cache = json.load(f)
                else:
                    self._offline_cache = []
            except Exception as e:
                logger.error("Error loading offline data", error=str(e))
                self._offline_cache = []
        
        return self._offline_cache
    
    def search_offline_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search offline papers as fallback"""
        papers = self.get_offline_papers()
        query_lower = query.lower()
        
        results = []
        for paper in papers:
            # Simple text matching
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            authors = ' '.join([author.get('name', '') for author in paper.get('authors', [])]).lower()
            
            if (query_lower in title or 
                query_lower in abstract or 
                query_lower in authors):
                results.append(paper)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_fallback_response(self, query: str, error: str) -> Dict[str, Any]:
        """Get a fallback response when APIs fail"""
        return {
            "papers": self.search_offline_papers(query, 5),
            "total": len(self.search_offline_papers(query, 5)),
            "sources_tried": ["offline_fallback"],
            "error": f"API temporarily unavailable: {error}",
            "fallback": True,
            "message": "Showing cached results. Please try again later for live data."
        }
    
    def get_common_papers(self, topic: str) -> List[Dict[str, Any]]:
        """Get common papers for popular topics"""
        common_papers = {
            "transformer": [
                {
                    "title": "Attention Is All You Need",
                    "authors": [{"name": "Ashish Vaswani"}],
                    "year": 2017,
                    "venue": "NeurIPS",
                    "doi": "10.5555/3295222.3295349",
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "citation_count": 50000
                }
            ],
            "machine learning": [
                {
                    "title": "The Elements of Statistical Learning",
                    "authors": [{"name": "Trevor Hastie"}, {"name": "Robert Tibshirani"}, {"name": "Jerome Friedman"}],
                    "year": 2009,
                    "venue": "Springer",
                    "doi": "10.1007/978-0-387-84858-7",
                    "abstract": "This book describes the important ideas in these areas in a common conceptual framework...",
                    "citation_count": 25000
                }
            ],
            "deep learning": [
                {
                    "title": "Deep Learning",
                    "authors": [{"name": "Yann LeCun"}, {"name": "Yoshua Bengio"}, {"name": "Geoffrey Hinton"}],
                    "year": 2015,
                    "venue": "Nature",
                    "doi": "10.1038/nature14539",
                    "abstract": "Deep learning allows computational models that are composed of multiple processing layers...",
                    "citation_count": 30000
                }
            ]
        }
        
        topic_lower = topic.lower()
        for key, papers in common_papers.items():
            if key in topic_lower:
                return papers
        
        return []

# Global instance
api_fallback = APIFallback()