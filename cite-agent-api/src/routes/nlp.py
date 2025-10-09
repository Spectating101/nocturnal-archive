"""
NLP API routes for FinGPT sentiment analysis
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import List
from src.services.sentiment import SentimentIn, SentimentOut, classify_sentiment
from src.core.ratelimit import rate_limit
from src.core.soft_quota import soft_quota

router = APIRouter(prefix="/v1/nlp", tags=["nlp"])


@router.post("/sentiment", response_model=SentimentOut)
def sentiment_api(payload: SentimentIn, request: Request, _=Depends(rate_limit), __=Depends(soft_quota)) -> SentimentOut:
    """
    Analyze financial sentiment of text using FinGPT
    
    Args:
        payload: Text to analyze for sentiment
        
    Returns:
        SentimentOut with label, score, rationale, and adapter info
        
    Raises:
        HTTPException: If sentiment analysis fails
    """
    try:
        return classify_sentiment(payload)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


class BatchSentimentIn(BaseModel):
    """Batch sentiment analysis request"""
    texts: List[str] = Field(min_length=1, max_length=50, description="List of texts to analyze")


class BatchSentimentOut(BaseModel):
    """Batch sentiment analysis response"""
    results: List[SentimentOut]
    count: int


@router.post("/sentiment/batch", response_model=BatchSentimentOut)
def sentiment_batch(
    payload: BatchSentimentIn, 
    request: Request, 
    _=Depends(rate_limit), 
    __=Depends(soft_quota)
) -> BatchSentimentOut:
    """
    Analyze sentiment for multiple texts in a single request
    
    Args:
        payload: List of texts to analyze
        request: The incoming request object (for dependencies)
        _: Rate limit dependency
        __: Soft quota dependency
        
    Returns:
        BatchSentimentOut with results and count
    """
    # Process each text
    results = []
    for text in payload.texts:
        sentiment_input = SentimentIn(text=text)
        result = classify_sentiment(sentiment_input)
        results.append(result)
    
    return BatchSentimentOut(results=results, count=len(results))
