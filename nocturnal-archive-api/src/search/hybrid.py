"""
Hybrid search combining keyword and vector search
"""

from typing import List, Tuple, Dict, Set
import re

def normalize(query: str) -> str:
    """Normalize search query"""
    return " ".join(query.lower().split())

def extract_keywords(query: str) -> List[str]:
    """Extract keywords from query"""
    # Remove common stop words and extract meaningful terms
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    words = re.findall(r'\b\w+\b', query.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]

def keyword_score(text: str, must_have: List[str]) -> float:
    """Calculate keyword match score"""
    if not must_have:
        return 1.0
    
    text_lower = text.lower()
    matches = sum(1 for keyword in must_have if keyword in text_lower)
    return matches / len(must_have)

def strict_filter(documents: List[Dict], must_have: List[str]) -> List[Dict]:
    """Filter documents that contain ALL must-have keywords"""
    if not must_have:
        return documents
    
    filtered = []
    for doc in documents:
        text = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('content', '')}"
        if all(keyword in text.lower() for keyword in must_have):
            filtered.append(doc)
    
    return filtered

def blend_results(
    keyword_results: List[Tuple[str, float]], 
    vector_results: List[Tuple[str, float]], 
    alpha: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Blend keyword and vector search results
    
    Args:
        keyword_results: List of (doc_id, score) from keyword search
        vector_results: List of (doc_id, score) from vector search
        alpha: Weight for keyword results (0.0 = vector only, 1.0 = keyword only)
    
    Returns:
        Blended results sorted by score
    """
    # Convert to dictionaries for easier lookup
    kw_scores = {doc_id: score for doc_id, score in keyword_results}
    vec_scores = {doc_id: score for doc_id, score in vector_results}
    
    # Get all unique document IDs
    all_ids = set(kw_scores.keys()) | set(vec_scores.keys())
    
    # Blend scores
    blended = []
    for doc_id in all_ids:
        kw_score = kw_scores.get(doc_id, 0.0)
        vec_score = vec_scores.get(doc_id, 0.0)
        blended_score = alpha * kw_score + (1 - alpha) * vec_score
        blended.append((doc_id, blended_score))
    
    # Sort by score (descending)
    return sorted(blended, key=lambda x: x[1], reverse=True)

def hybrid_search(
    query: str,
    documents: List[Dict],
    strict: bool = False,
    alpha: float = 0.6,
    vector_search_func=None
) -> List[Dict]:
    """
    Perform hybrid search combining keyword and vector search
    
    Args:
        query: Search query
        documents: List of documents to search
        strict: If True, only return documents containing all keywords
        alpha: Weight for keyword vs vector results
        vector_search_func: Function to perform vector search (optional)
    
    Returns:
        List of documents sorted by relevance
    """
    keywords = extract_keywords(query)
    
    if strict:
        # Strict mode: filter by keywords first, then optionally re-rank by vector
        filtered_docs = strict_filter(documents, keywords)
        
        if vector_search_func and filtered_docs:
            # Re-rank filtered results using vector search
            vector_results = vector_search_func(query, filtered_docs)
            # Convert back to documents
            doc_map = {doc.get('id', i): doc for i, doc in enumerate(filtered_docs)}
            return [doc_map[doc_id] for doc_id, _ in vector_results if doc_id in doc_map]
        else:
            # Just return keyword-filtered results
            return filtered_docs
    
    else:
        # Non-strict mode: blend keyword and vector results
        keyword_results = []
        for i, doc in enumerate(documents):
            text = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('content', '')}"
            score = keyword_score(text, keywords)
            if score > 0:
                keyword_results.append((doc.get('id', i), score))
        
        if vector_search_func:
            vector_results = vector_search_func(query, documents)
            blended = blend_results(keyword_results, vector_results, alpha)
            
            # Convert back to documents
            doc_map = {doc.get('id', i): doc for i, doc in enumerate(documents)}
            return [doc_map[doc_id] for doc_id, _ in blended if doc_id in doc_map]
        else:
            # Just return keyword results
            doc_map = {doc.get('id', i): doc for i, doc in enumerate(documents)}
            return [doc_map[doc_id] for doc_id, _ in keyword_results if doc_id in doc_map]
