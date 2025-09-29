"""
FinGPT sentiment analysis service with caching
"""
import hashlib
from typing import Dict
from pydantic import BaseModel, Field
from src.core.cache import cache
from src.providers.fingpt.loader import FinGPTModel


class SentimentIn(BaseModel):
    """Input model for sentiment analysis"""
    text: str = Field(min_length=3, max_length=8000, description="Text to analyze")


class SentimentOut(BaseModel):
    """Output model for sentiment analysis"""
    label: str = Field(description="Sentiment label: positive, negative, or neutral")
    score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    rationale: str = Field(description="Brief explanation of the sentiment classification")
    adapter: str = Field(description="FinGPT adapter ID used for analysis")


def _hash(text: str, adapter: str) -> str:
    """Generate cache key hash for text and adapter"""
    h = hashlib.sha256()
    h.update(adapter.encode())
    h.update(text.strip().encode())
    return h.hexdigest()


def classify_sentiment(payload: SentimentIn) -> SentimentOut:
    """
    Classify financial sentiment using FinGPT with caching
    
    Args:
        payload: SentimentIn containing text to analyze
        
    Returns:
        SentimentOut with label, score, rationale, and adapter info
    """
    # Load model and get adapter ID
    FinGPTModel.load()
    adapter = FinGPTModel._adapter_id or "unknown"
    
    # Check cache first
    key = _hash(payload.text, adapter)
    hit = cache.get(key)
    if hit:
        return SentimentOut(**hit)
    
    # Generate sentiment analysis
    try:
        result = FinGPTModel.generate_json(
            "Classify the financial sentiment and return JSON only.",
            payload.text
        )
        
        # Validate and normalize result
        label = str(result.get("label", "neutral")).lower()
        if label not in ["positive", "negative", "neutral"]:
            label = "neutral"
            
        score = float(result.get("score", 0.5))
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        rationale = str(result.get("rationale", ""))
        if not rationale:
            rationale = f"Classified as {label} with score {score:.2f}"
        
        # Create output
        output = SentimentOut(
            label=label,
            score=score,
            rationale=rationale,
            adapter=adapter
        )
        
        # Cache the result
        cache.set(key, output.model_dump())
        
        return output
        
    except Exception as e:
        # Fallback for any errors
        fallback = SentimentOut(
            label="neutral",
            score=0.5,
            rationale=f"Error in sentiment analysis: {str(e)}",
            adapter=adapter
        )
        
        # Cache fallback result to avoid repeated failures
        cache.set(key, fallback.model_dump())
        
        return fallback
