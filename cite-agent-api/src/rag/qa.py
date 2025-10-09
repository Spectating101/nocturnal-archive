"""
Q&A service with citations and point-in-time queries
"""
import os
from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional
from src.rag.index import search


def answer(
    query: str, 
    cutoff: Optional[str] = None, 
    tickers: Optional[List[str]] = None, 
    k: int = 5
) -> Dict:
    """
    Answer a question using RAG with citations
    
    Args:
        query: User's question
        cutoff: Date cutoff for point-in-time queries (YYYY-MM-DD)
        tickers: List of tickers to filter by
        k: Number of relevant documents to retrieve
        
    Returns:
        Dict: Answer with citations
    """
    # Search for relevant documents
    hits = search(query, k=k, cutoff=cutoff, tickers=tickers)
    
    if not hits:
        return {
            "answer": "I couldn't find relevant information to answer your question.",
            "citations": [],
            "query": query,
            "cutoff": cutoff,
            "tickers": tickers
        }
    
    # Create extractive summary from top chunks
    summary_sentences = _extract_summary_sentences(hits[:3])  # Top 3 chunks
    
    # Create structured answer with citations
    draft_answer = _create_extractive_answer(summary_sentences, hits)
    
    # Format citations
    citations = []
    for i, hit in enumerate(hits, 1):
        citation = {
            "idx": i,
            "id": hit["id"],
            "title": hit["title"],
            "url": hit["url"],
            "date": str(hit["date"]) if hit.get("date") else None,
            "ticker": hit["ticker"],
            "section": hit["section"],
            "score": round(hit.get("score", 0), 3)
        }
        citations.append(citation)
    
    # Create meta information for reproducibility
    meta_info = {
        "embed_model": os.getenv("RAG_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "k": k,
        "doc_ids": [hit["id"] for hit in hits],
        "search_scores": [hit.get("score", 0) for hit in hits],
        "mmr_applied": len(hits) > k,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "answer": draft_answer,
        "citations": citations,
        "query": query,
        "cutoff": cutoff,
        "tickers": tickers,
        "total_results": len(hits),
        "meta": meta_info
    }


def explain_query(query: str, cutoff: Optional[str] = None, tickers: Optional[List[str]] = None) -> Dict:
    """
    Explain what the query is looking for and how it will be processed
    
    Args:
        query: User's question
        cutoff: Date cutoff for point-in-time queries
        tickers: List of tickers to filter by
        
    Returns:
        Dict: Query explanation
    """
    explanation_parts = []
    
    # Query analysis
    explanation_parts.append(f"**Query**: {query}")
    
    # Filter explanation
    filters = []
    if cutoff:
        filters.append(f"documents dated on or before {cutoff}")
    if tickers:
        ticker_list = ", ".join(tickers)
        filters.append(f"documents for ticker(s): {ticker_list}")
    
    if filters:
        explanation_parts.append(f"**Filters**: {' and '.join(filters)}")
    else:
        explanation_parts.append("**Filters**: None (searching all available documents)")
    
    # Search strategy
    explanation_parts.append("**Search Strategy**: Using semantic similarity to find the most relevant document sections that match your question.")
    
    return {
        "explanation": "\n\n".join(explanation_parts),
        "query": query,
        "cutoff": cutoff,
        "tickers": tickers
    }


def validate_query(query: str) -> Dict[str, any]:
    """
    Validate a query and provide feedback
    
    Args:
        query: User's question
        
    Returns:
        Dict: Validation results
    """
    issues = []
    suggestions = []
    
    # Check query length
    if len(query.strip()) < 3:
        issues.append("Query is too short")
        suggestions.append("Please provide a more specific question")
    
    if len(query) > 2000:
        issues.append("Query is too long")
        suggestions.append("Please shorten your question to under 2000 characters")
    
    # Check for financial keywords
    financial_keywords = [
        "revenue", "earnings", "profit", "margin", "growth", "debt", "assets",
        "cash", "guidance", "forecast", "risk", "competition", "market",
        "financial", "performance", "results", "quarterly", "annual"
    ]
    
    query_lower = query.lower()
    found_keywords = [kw for kw in financial_keywords if kw in query_lower]
    
    if not found_keywords:
        suggestions.append("Consider including financial terms like 'revenue', 'earnings', 'margin', etc. for better results")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "found_keywords": found_keywords,
        "query_length": len(query)
    }


def _extract_summary_sentences(hits: List[Dict]) -> List[str]:
    """
    Extract 1-2 best sentences from each hit for summary
    
    Args:
        hits: List of search result hits
        
    Returns:
        List[str]: Best sentences with citation references
    """
    summary_sentences = []
    
    for i, hit in enumerate(hits, 1):
        snippet = hit.get("snippet", "")
        sentences = _split_into_sentences(snippet)
        
        # Take 1-2 best sentences (longest ones usually contain more info)
        best_sentences = sorted(sentences, key=len, reverse=True)[:2]
        
        for sentence in best_sentences:
            if len(sentence.strip()) > 20:  # Filter out very short sentences
                summary_sentences.append(f"[{i}] {sentence.strip()}")
    
    return summary_sentences


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    import re
    
    # Simple sentence splitting (could be improved with NLTK)
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def _create_extractive_answer(summary_sentences: List[str], hits: List[Dict]) -> str:
    """
    Create structured extractive answer from summary sentences
    
    Args:
        summary_sentences: List of cited sentences
        hits: Full search results for context
        
    Returns:
        str: Structured answer
    """
    if not summary_sentences:
        return "I couldn't find specific information to answer your question in the available documents."
    
    # Group sentences by citation number
    cited_sentences = {}
    for sentence in summary_sentences:
        if sentence.startswith("[") and "] " in sentence:
            citation_num = sentence[1:sentence.index("] ")]
            content = sentence[sentence.index("] ") + 2:]
            cited_sentences[citation_num] = content
    
    # Create structured answer
    answer_parts = []
    
    if len(cited_sentences) > 1:
        answer_parts.append("Based on the available information, here are the key findings:")
    else:
        answer_parts.append("Based on the available information:")
    
    answer_parts.append("")
    
    # Add summary sentences
    for sentence in summary_sentences:
        answer_parts.append(f"• {sentence}")
    
    answer_parts.append("")
    answer_parts.append("Please refer to the citations below for complete context and source documents.")
    
    return "\n".join(answer_parts)


if __name__ == "__main__":
    # Test the Q&A service
    print("Testing Q&A service...")
    
    # Test query validation
    test_queries = [
        "What did Apple say about margins?",
        "Revenue growth",
        "Risk factors",
        "a"  # Too short
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        validation = validate_query(query)
        print(f"Valid: {validation['valid']}")
        if validation['issues']:
            print(f"Issues: {validation['issues']}")
        if validation['suggestions']:
            print(f"Suggestions: {validation['suggestions']}")
    
    # Test query explanation
    print("\n" + "="*50)
    explanation = explain_query("What did Apple say about margins?", cutoff="2024-12-31", tickers=["AAPL"])
    print("Query Explanation:")
    print(explanation['explanation'])
