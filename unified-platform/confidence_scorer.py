#!/usr/bin/env python3
"""
Confidence Scorer - Enhanced confidence scoring and critical judgment
"""

import re
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ConfidenceFactors:
    data_quality: float
    source_reliability: float
    method_confidence: float
    result_consistency: float
    outlier_detection: float

class ConfidenceScorer:
    """Enhanced confidence scoring with critical judgment"""
    
    def __init__(self):
        self.quality_indicators = {
            "high_quality": ["comprehensive", "detailed", "thorough", "complete", "robust"],
            "medium_quality": ["adequate", "sufficient", "reasonable", "standard"],
            "low_quality": ["limited", "incomplete", "partial", "insufficient", "preliminary"]
        }
        
        self.reliability_indicators = {
            "high_reliability": ["peer-reviewed", "published", "validated", "verified", "confirmed"],
            "medium_reliability": ["reported", "documented", "observed", "measured"],
            "low_reliability": ["estimated", "approximate", "preliminary", "unverified", "speculative"]
        }
    
    def calculate_confidence(self, evidence: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        factors = self._analyze_confidence_factors(evidence)
        
        # Weighted average of factors
        weights = {
            "data_quality": 0.25,
            "source_reliability": 0.25,
            "method_confidence": 0.20,
            "result_consistency": 0.20,
            "outlier_detection": 0.10
        }
        
        confidence = sum(factors.__dict__[factor] * weight 
                        for factor, weight in weights.items())
        
        return max(0.0, min(1.0, confidence))
    
    def _analyze_confidence_factors(self, evidence: Dict[str, Any]) -> ConfidenceFactors:
        """Analyze individual confidence factors"""
        
        # Data quality assessment
        data_quality = self._assess_data_quality(evidence)
        
        # Source reliability assessment
        source_reliability = self._assess_source_reliability(evidence)
        
        # Method confidence assessment
        method_confidence = self._assess_method_confidence(evidence)
        
        # Result consistency assessment
        result_consistency = self._assess_result_consistency(evidence)
        
        # Outlier detection
        outlier_detection = self._assess_outlier_detection(evidence)
        
        return ConfidenceFactors(
            data_quality=data_quality,
            source_reliability=source_reliability,
            method_confidence=method_confidence,
            result_consistency=result_consistency,
            outlier_detection=outlier_detection
        )
    
    def _assess_data_quality(self, evidence: Dict[str, Any]) -> float:
        """Assess data quality"""
        score = 0.5  # Base score
        
        # Check for data completeness
        if evidence.get("data_completeness", 0) > 0.8:
            score += 0.2
        elif evidence.get("data_completeness", 0) > 0.6:
            score += 0.1
        
        # Check for data freshness
        if evidence.get("data_freshness", False):
            score += 0.1
        
        # Check for data validation
        if evidence.get("data_validated", False):
            score += 0.1
        
        # Check for missing values
        if evidence.get("missing_values", 0) < 0.1:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_source_reliability(self, evidence: Dict[str, Any]) -> float:
        """Assess source reliability"""
        score = 0.5  # Base score
        
        # Check source count
        source_count = evidence.get("source_count", 0)
        if source_count >= 3:
            score += 0.2
        elif source_count >= 2:
            score += 0.1
        
        # Check for peer-reviewed sources
        if evidence.get("peer_reviewed", False):
            score += 0.2
        
        # Check for authoritative sources
        if evidence.get("authoritative", False):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_method_confidence(self, evidence: Dict[str, Any]) -> float:
        """Assess method confidence"""
        score = 0.5  # Base score
        
        # Check for established methods
        if evidence.get("established_method", False):
            score += 0.2
        
        # Check for statistical significance
        if evidence.get("statistically_significant", False):
            score += 0.1
        
        # Check for cross-validation
        if evidence.get("cross_validated", False):
            score += 0.1
        
        # Check for replication
        if evidence.get("replicated", False):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_result_consistency(self, evidence: Dict[str, Any]) -> float:
        """Assess result consistency"""
        score = 0.5  # Base score
        
        # Check for consistent results
        if evidence.get("consistent_results", False):
            score += 0.2
        
        # Check for expected patterns
        if evidence.get("expected_patterns", False):
            score += 0.1
        
        # Check for logical consistency
        if evidence.get("logical_consistency", False):
            score += 0.1
        
        # Check for temporal consistency
        if evidence.get("temporal_consistency", False):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_outlier_detection(self, evidence: Dict[str, Any]) -> float:
        """Assess outlier detection"""
        score = 0.5  # Base score
        
        # Check for outlier analysis
        if evidence.get("outlier_analyzed", False):
            score += 0.2
        
        # Check for anomaly detection
        if evidence.get("anomalies_detected", False):
            score += 0.1
        
        # Check for data cleaning
        if evidence.get("data_cleaned", False):
            score += 0.1
        
        # Check for quality control
        if evidence.get("quality_controlled", False):
            score += 0.1
        
        return min(1.0, score)
    
    def detect_outliers(self, data: List[float]) -> List[int]:
        """Detect outliers using modified Z-score method"""
        if len(data) < 5:
            return []
        
        # Calculate median and MAD
        sorted_data = sorted(data)
        n = len(sorted_data)
        median = sorted_data[n // 2]
        
        # Calculate MAD (Median Absolute Deviation)
        deviations = [abs(x - median) for x in data]
        mad = sorted(deviations)[n // 2]
        
        if mad == 0:
            return []
        
        # Modified Z-score threshold (3.5 is more robust than 3.0)
        threshold = 3.5
        
        outliers = []
        for i, value in enumerate(data):
            modified_z_score = 0.6745 * (value - median) / mad
            if abs(modified_z_score) > threshold:
                outliers.append(i)
        
        return outliers
    
    def generate_confidence_report(self, confidence: float, factors: ConfidenceFactors, 
                                 outliers: List[int] = None) -> str:
        """Generate a confidence report"""
        
        # Overall confidence level
        if confidence >= 0.9:
            level = "Very High"
            emoji = "🟢"
        elif confidence >= 0.8:
            level = "High"
            emoji = "🟡"
        elif confidence >= 0.6:
            level = "Medium"
            emoji = "🟠"
        else:
            level = "Low"
            emoji = "🔴"
        
        report = f"{emoji} **Confidence Level: {level} ({confidence:.2f})**\n\n"
        
        # Factor breakdown
        report += "**Confidence Factors:**\n"
        report += f"• Data Quality: {factors.data_quality:.2f}\n"
        report += f"• Source Reliability: {factors.source_reliability:.2f}\n"
        report += f"• Method Confidence: {factors.method_confidence:.2f}\n"
        report += f"• Result Consistency: {factors.result_consistency:.2f}\n"
        report += f"• Outlier Detection: {factors.outlier_detection:.2f}\n\n"
        
        # Warnings and recommendations
        if confidence < 0.7:
            report += "⚠️ **Warnings:**\n"
            if factors.data_quality < 0.6:
                report += "• Data quality is low - consider additional validation\n"
            if factors.source_reliability < 0.6:
                report += "• Source reliability is low - seek additional sources\n"
            if factors.method_confidence < 0.6:
                report += "• Method confidence is low - consider alternative approaches\n"
            if factors.result_consistency < 0.6:
                report += "• Results may be inconsistent - verify findings\n"
        
        # Outlier information
        if outliers:
            report += f"\n🔍 **Outliers Detected:** {len(outliers)} data points flagged\n"
            report += "• Consider investigating these values for data quality issues\n"
        
        return report
    
    def assess_text_quality(self, text: str) -> Dict[str, Any]:
        """Assess quality indicators in text"""
        text_lower = text.lower()
        
        quality_score = 0.5
        reliability_score = 0.5
        
        # Check for quality indicators
        for level, indicators in self.quality_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    if level == "high_quality":
                        quality_score += 0.1
                    elif level == "medium_quality":
                        quality_score += 0.05
                    else:
                        quality_score -= 0.1
        
        # Check for reliability indicators
        for level, indicators in self.reliability_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    if level == "high_reliability":
                        reliability_score += 0.1
                    elif level == "medium_reliability":
                        reliability_score += 0.05
                    else:
                        reliability_score -= 0.1
        
        return {
            "data_quality": max(0.0, min(1.0, quality_score)),
            "source_reliability": max(0.0, min(1.0, reliability_score)),
            "text_length": len(text),
            "has_citations": bool(re.search(r'\[.*?\]|\(.*?\)', text)),
            "has_numbers": bool(re.search(r'\d+', text))
        }

# Example usage
if __name__ == "__main__":
    scorer = ConfidenceScorer()
    
    # Test confidence scoring
    evidence = {
        "data_completeness": 0.9,
        "data_freshness": True,
        "data_validated": True,
        "missing_values": 0.05,
        "source_count": 3,
        "peer_reviewed": True,
        "authoritative": True,
        "established_method": True,
        "statistically_significant": True,
        "consistent_results": True,
        "expected_patterns": True,
        "outlier_analyzed": True
    }
    
    confidence = scorer.calculate_confidence(evidence)
    factors = scorer._analyze_confidence_factors(evidence)
    
    print("🎯 CONFIDENCE SCORER TEST")
    print("=" * 50)
    print(f"Overall Confidence: {confidence:.2f}")
    print(f"Data Quality: {factors.data_quality:.2f}")
    print(f"Source Reliability: {factors.source_reliability:.2f}")
    print(f"Method Confidence: {factors.method_confidence:.2f}")
    
    # Test outlier detection
    test_data = [1, 2, 3, 4, 5, 100]  # 100 is an outlier
    outliers = scorer.detect_outliers(test_data)
    print(f"\nOutliers in {test_data}: {outliers}")
    
    # Generate report
    report = scorer.generate_confidence_report(confidence, factors, outliers)
    print(f"\nConfidence Report:\n{report}")

