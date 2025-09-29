"""
Mock FinGPT loader for testing without full dependencies
"""
from typing import Dict
import json
import re


class MockFinGPTModel:
    """Mock FinGPT model for testing"""
    
    _tok = None
    _model = None
    _adapter_id = "mock-fingpt-adapter"

    @classmethod
    def load(cls) -> None:
        """Mock load method"""
        print("Mock FinGPT model loaded successfully")
        cls._adapter_id = "mock-fingpt-adapter"

    @classmethod
    def generate_json(cls, instruction: str, text: str) -> Dict:
        """Generate mock JSON response for sentiment analysis"""
        cls.load()
        
        # Simple keyword-based sentiment analysis
        text_lower = text.lower()
        
        positive_keywords = [
            "beat", "exceed", "strong", "growth", "positive", "up", "rise", "increase", 
            "raise", "guidance", "demand", "strong", "robust", "solid", "outperform"
        ]
        negative_keywords = [
            "miss", "decline", "weak", "negative", "down", "fall", "drop", "decrease",
            "challenge", "warning", "concern", "weakness", "underperform", "disappoint"
        ]
        
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            label = "positive"
            score = 0.7 + (positive_count * 0.05)
            rationale = f"Positive sentiment detected ({positive_count} positive indicators)"
        elif negative_count > positive_count:
            label = "negative"
            score = 0.3 - (negative_count * 0.05)
            rationale = f"Negative sentiment detected ({negative_count} negative indicators)"
        else:
            label = "neutral"
            score = 0.5
            rationale = "Neutral sentiment - mixed or no clear indicators"
        
        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))
        
        return {
            "label": label,
            "score": score,
            "rationale": rationale
        }


# Use mock loader for testing
FinGPTModel = MockFinGPTModel
