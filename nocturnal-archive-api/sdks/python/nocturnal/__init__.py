"""
Nocturnal Archive Python SDK
"""

import os
import requests
from typing import Dict, Any, List, Optional

BASE_URL = os.getenv("NOCTURNAL_BASE", "https://api.nocturnal.dev")
API_KEY = os.getenv("NOCTURNAL_KEY", "")

def _get_headers() -> Dict[str, str]:
    """Get request headers with API key"""
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

def papers_search(query: str, limit: int = 10, sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search academic papers
    
    Args:
        query: Search query
        limit: Maximum number of results
        sources: List of sources to search (default: ["openalex"])
    
    Returns:
        Search results
    """
    if sources is None:
        sources = ["openalex"]
    
    payload = {
        "query": query,
        "limit": limit,
        "sources": sources
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/api/papers/search",
        json=payload,
        headers=_get_headers(),
        timeout=15
    )
    response.raise_for_status()
    return response.json()

def finance_synthesize(
    context: Dict[str, Any], 
    claims: List[Dict[str, Any]], 
    grounded: bool = True,
    max_words: int = 400,
    style: str = "markdown"
) -> Dict[str, Any]:
    """
    Synthesize finance data with numeric grounding
    
    Args:
        context: Financial context with time series data
        claims: List of numeric claims to verify
        grounded: Whether to enforce numeric grounding
        max_words: Maximum words in summary
        style: Output style (markdown, json, etc.)
    
    Returns:
        Synthesis results with evidence
    """
    payload = {
        "context": context,
        "claims": claims,
        "grounded": grounded,
        "max_words": max_words,
        "style": style
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/api/finance/synthesize",
        json=payload,
        headers=_get_headers(),
        timeout=60
    )
    response.raise_for_status()
    return response.json()

def create_synthesis_job(
    context: Dict[str, Any], 
    claims: List[Dict[str, Any]], 
    max_words: int = 400,
    style: str = "markdown"
) -> Dict[str, Any]:
    """
    Create an async synthesis job
    
    Args:
        context: Financial context with time series data
        claims: List of numeric claims to verify
        max_words: Maximum words in summary
        style: Output style
    
    Returns:
        Job information with job_id for polling
    """
    payload = {
        "context": context,
        "claims": claims,
        "max_words": max_words,
        "style": style
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/api/jobs/synthesis",
        json=payload,
        headers=_get_headers(),
        timeout=15
    )
    response.raise_for_status()
    return response.json()

def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get job status and result
    
    Args:
        job_id: Job ID to check
    
    Returns:
        Job status information
    """
    response = requests.get(
        f"{BASE_URL}/v1/api/jobs/{job_id}",
        headers=_get_headers(),
        timeout=15
    )
    response.raise_for_status()
    return response.json()

def verify_claims(
    context: Dict[str, Any], 
    claims: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify claims without synthesis
    
    Args:
        context: Financial context with time series data
        claims: List of numeric claims to verify
    
    Returns:
        Verification results
    """
    payload = {
        "context": context,
        "claims": claims,
        "grounded": True
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/api/finance/verify-claims",
        json=payload,
        headers=_get_headers(),
        timeout=30
    )
    response.raise_for_status()
    return response.json()

# Convenience functions
def search_papers(query: str, limit: int = 10) -> Dict[str, Any]:
    """Convenience function for paper search"""
    return papers_search(query, limit)

def synthesize_finance(context: Dict[str, Any], claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for finance synthesis"""
    return finance_synthesize(context, claims)
