"""
Q&A API routes for RAG-powered financial document search
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from src.rag.qa import answer, validate_query, explain_query
from src.rag.index import get_doc_stats
from src.core.ratelimit import rate_limit
from src.core.soft_quota import soft_quota


router = APIRouter(prefix="/v1/qa", tags=["qa"])


class QARequest(BaseModel):
    """Request model for Q&A queries"""
    query: str = Field(min_length=3, max_length=2000, description="Question to answer")
    cutoff: Optional[str] = Field(None, description="Date cutoff for point-in-time queries (YYYY-MM-DD)")
    tickers: Optional[List[str]] = Field(None, description="List of tickers to filter by")
    k: int = Field(5, ge=1, le=20, description="Number of relevant documents to retrieve")


class QAResponse(BaseModel):
    """Response model for Q&A queries"""
    answer: str
    citations: List[dict]
    query: str
    cutoff: Optional[str] = None
    tickers: Optional[List[str]] = None
    total_results: int


@router.post("/filings", response_model=QAResponse)
def filings_qa(request: QARequest, req: Request, _=Depends(rate_limit), __=Depends(soft_quota)):
    """
    Answer questions about SEC filings using RAG with citations
    
    This endpoint searches through indexed SEC filing sections to answer
    financial questions with proper citations and point-in-time filtering.
    
    Example queries:
    - "What did Apple say about margins?"
    - "What are the main risk factors?"
    - "How did revenue perform last quarter?"
    """
    try:
        # Validate the query
        validation = validate_query(request.query)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid query",
                    "issues": validation["issues"],
                    "suggestions": validation["suggestions"]
                }
            )
        
        # Process the query
        result = answer(
            query=request.query,
            cutoff=request.cutoff,
            tickers=request.tickers,
            k=request.k
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


class BatchQAIn(BaseModel):
    """Batch Q&A request"""
    items: List[QARequest] = Field(min_length=1, max_length=10, description="List of Q&A requests")


class BatchQAOut(BaseModel):
    """Batch Q&A response"""
    results: List[QAResponse]
    count: int


@router.post("/filings/batch", response_model=BatchQAOut)
def filings_batch(
    request: BatchQAIn, 
    req: Request, 
    _=Depends(rate_limit), 
    __=Depends(soft_quota)
) -> BatchQAOut:
    """
    Answer multiple questions about SEC filings in a single request
    
    This endpoint allows processing multiple Q&A queries in a single API call,
    which is useful for batch processing and reducing latency overhead.
    
    Args:
        request: List of Q&A requests (max 10)
        req: The incoming request object (for dependencies)
        _: Rate limit dependency
        __: Soft quota dependency
        
    Returns:
        BatchQAOut with results and count
    """
    try:
        results = []
        for item in request.items:
            # Validate each query
            validation = validate_query(item.query)
            if not validation["valid"]:
                # Skip invalid queries but continue processing others
                results.append({
                    "answer": "Query validation failed",
                    "citations": [],
                    "query": item.query,
                    "cutoff": item.cutoff,
                    "tickers": item.tickers,
                    "total_results": 0,
                    "error": validation["issues"]
                })
                continue
            
            # Process valid queries
            result = answer(
                query=item.query,
                cutoff=item.cutoff,
                tickers=item.tickers,
                k=item.k
            )
            results.append(result)
        
        return BatchQAOut(results=results, count=len(results))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch queries: {str(e)}"
        )


@router.get("/explain")
def explain_qa_query(
    query: str = Query(..., description="Query to explain"),
    cutoff: Optional[str] = Query(None, description="Date cutoff"),
    tickers: Optional[str] = Query(None, description="Comma-separated tickers")
):
    """
    Explain how a query will be processed without executing it
    
    Useful for understanding how filters and search will work before
    running the actual query.
    """
    try:
        # Parse tickers if provided
        ticker_list = None
        if tickers:
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        
        return explain_query(query, cutoff=cutoff, tickers=ticker_list)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error explaining query: {str(e)}"
        )


@router.get("/stats")
def get_qa_stats():
    """
    Get statistics about the indexed document collection
    
    Returns information about total documents, tickers, date ranges,
    and section types available for Q&A.
    """
    try:
        return get_doc_stats()
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stats: {str(e)}"
        )


@router.post("/validate")
def validate_qa_query(request: QARequest):
    """
    Validate a query without executing it
    
    Returns validation results, suggestions, and query analysis
    to help users improve their questions.
    """
    try:
        validation = validate_query(request.query)
        return {
            "valid": validation["valid"],
            "issues": validation["issues"],
            "suggestions": validation["suggestions"],
            "found_keywords": validation["found_keywords"],
            "query_length": validation["query_length"],
            "query": request.query
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating query: {str(e)}"
        )


# Health check endpoint for RAG system
@router.get("/health")
def qa_health():
    """
    Health check for the Q&A system
    
    Verifies that the RAG system components are working properly.
    """
    try:
        # Try to get stats as a health check
        stats = get_doc_stats()
        
        return {
            "status": "healthy",
            "total_documents": stats.get("total_documents", 0),
            "message": "Q&A system is operational"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Q&A system is not operational"
        }
