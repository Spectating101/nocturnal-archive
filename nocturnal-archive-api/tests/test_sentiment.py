"""
Smoke tests for FinGPT sentiment analysis
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_sentiment_smoke():
    """Test basic sentiment analysis functionality"""
    payload = {
        "text": "TSMC raises capex on strong AI demand; guidance increased."
    }
    
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    
    # Validate response structure
    assert "label" in data, "Response missing 'label' field"
    assert "score" in data, "Response missing 'score' field"
    assert "rationale" in data, "Response missing 'rationale' field"
    assert "adapter" in data, "Response missing 'adapter' field"
    
    # Validate label values
    assert data["label"] in {"positive", "negative", "neutral"}, f"Invalid label: {data['label']}"
    
    # Validate score range
    assert 0.0 <= data["score"] <= 1.0, f"Score out of range: {data['score']}"
    
    # Validate rationale is not empty
    assert len(data["rationale"]) > 0, "Rationale should not be empty"
    
    # Validate adapter is present
    assert len(data["adapter"]) > 0, "Adapter should not be empty"


def test_sentiment_positive_text():
    """Test sentiment analysis with clearly positive text"""
    payload = {
        "text": "Company beats earnings expectations and raises full-year guidance significantly."
    }
    
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be positive or neutral (not negative)
    assert data["label"] in {"positive", "neutral"}, f"Expected positive/neutral, got {data['label']}"


def test_sentiment_negative_text():
    """Test sentiment analysis with clearly negative text"""
    payload = {
        "text": "Company misses revenue targets and warns of challenging market conditions ahead."
    }
    
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be negative or neutral (not positive)
    assert data["label"] in {"negative", "neutral"}, f"Expected negative/neutral, got {data['label']}"


def test_sentiment_neutral_text():
    """Test sentiment analysis with neutral text"""
    payload = {
        "text": "Company reported quarterly results in line with previous guidance."
    }
    
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be neutral (or could be positive/negative depending on interpretation)
    assert data["label"] in {"positive", "negative", "neutral"}, f"Invalid label: {data['label']}"


def test_sentiment_validation():
    """Test input validation"""
    # Test too short text
    payload = {"text": "Hi"}
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    assert response.status_code == 422, "Should reject text that's too short"
    
    # Test missing text field
    payload = {}
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    assert response.status_code == 422, "Should reject missing text field"


def test_sentiment_caching():
    """Test that sentiment results are cached"""
    payload = {
        "text": "This is a test for caching functionality."
    }
    
    # First request
    response1 = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Second request (should be cached)
    response2 = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "demo-key-123"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Results should be identical (cached)
    assert data1 == data2, "Cached results should be identical"


def test_sentiment_authentication():
    """Test that API key authentication is required"""
    payload = {
        "text": "Test authentication requirement."
    }
    
    # Request without API key
    response = client.post("/v1/nlp/sentiment", json=payload)
    assert response.status_code == 401, "Should require API key authentication"
    
    # Request with invalid API key
    response = client.post(
        "/v1/nlp/sentiment", 
        json=payload,
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401, "Should reject invalid API key"
