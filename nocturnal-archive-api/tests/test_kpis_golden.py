"""
Golden test fixtures for FinSight KPIs
Tests against known values from SEC filings
"""

import json
import os
import pytest
import httpx
from pathlib import Path

BASE = os.getenv("BASE", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "demo-key-123")

# Load golden test cases
GOLDEN_DIR = Path(__file__).parent / "golden"
CASES = []

for json_file in GOLDEN_DIR.glob("*.json"):
    if json_file.name.startswith("AAPL_"):
        CASES.append(json_file.name)

@pytest.mark.parametrize("case_file", CASES)
def test_golden_kpis(case_file, httpx_client):
    """Test KPI calculations against golden values"""
    
    # Load golden case
    case_path = GOLDEN_DIR / case_file
    with open(case_path, 'r') as f:
        golden = json.load(f)
    
    ticker = golden["ticker"]
    period = golden["period"]
    freq = golden["freq"]
    
    print(f"\n🧪 Testing {ticker} {period} ({case_file})")
    
    # Test each metric in the golden case
    for metric, spec in golden["expect"].items():
        print(f"  📊 Testing {metric}...")
        
        # Make API call
        url = f"{BASE}/v1/finance/calc/{ticker}/{metric}?period={period}&freq={freq}"
        
        try:
            response = httpx_client.get(
                url,
                headers={"X-API-Key": API_KEY},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
        except httpx.HTTPError as e:
            pytest.fail(f"API call failed for {metric}: {e}")
        
        # Validate response structure
        assert "value" in result, f"Missing 'value' in response for {metric}"
        assert "citations" in result, f"Missing 'citations' in response for {metric}"
        assert "formula" in result, f"Missing 'formula' in response for {metric}"
        
        # Get actual value
        actual_value = result["value"]
        
        # Get expected value and tolerance
        expected_value = spec.get("value") or spec.get("approx")
        tolerance = spec.get("tol", 0.01)
        
        assert expected_value is not None, f"No expected value defined for {metric}"
        
        # Calculate relative tolerance
        if abs(expected_value) > 0:
            relative_tolerance = tolerance * max(1.0, abs(expected_value))
        else:
            relative_tolerance = tolerance
        
        # Check value is within tolerance
        difference = abs(actual_value - expected_value)
        assert difference <= relative_tolerance, (
            f"{metric} value mismatch: "
            f"expected {expected_value:.2f}, "
            f"got {actual_value:.2f}, "
            f"difference {difference:.2f} > tolerance {relative_tolerance:.2f}"
        )
        
        # Validate citations
        citations = result["citations"]
        assert len(citations) >= 1, f"No citations provided for {metric}"
        
        # Validate citation structure
        for citation in citations:
            assert "concept" in citation, f"Citation missing 'concept' for {metric}"
            assert "source_url" in citation, f"Citation missing 'source_url' for {metric}"
        
        print(f"    ✅ {metric}: {actual_value:.2f} (expected: {expected_value:.2f}, diff: {difference:.2f})")
    
    print(f"  🎉 All metrics passed for {ticker} {period}")

def test_golden_series(httpx_client):
    """Test series endpoints with golden data"""
    
    # Test AAPL revenue series
    url = f"{BASE}/v1/finance/kpis/AAPL/revenue?freq=Q&limit=4"
    
    try:
        response = httpx_client.get(
            url,
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
    except httpx.HTTPError as e:
        pytest.fail(f"Series API call failed: {e}")
    
    # Validate series structure
    assert "data" in result, "Missing 'data' in series response"
    assert isinstance(result["data"], list), "Series data should be a list"
    assert len(result["data"]) > 0, "Series should have at least one data point"
    
    # Validate data point structure
    for point in result["data"]:
        assert "period" in point, "Data point missing 'period'"
        assert "value" in point, "Data point missing 'value'"
        assert "citation" in point, "Data point missing 'citation'"
    
    print(f"✅ Series test passed: {len(result['data'])} points returned")

def test_golden_explain(httpx_client):
    """Test expression explanation with golden data"""
    
    payload = {
        "ticker": "AAPL",
        "expr": "revenue - costOfRevenue",
        "period": "2024-Q4",
        "freq": "Q"
    }
    
    url = f"{BASE}/v1/finance/calc/explain"
    
    try:
        response = httpx_client.post(
            url,
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
    except httpx.HTTPError as e:
        pytest.fail(f"Explain API call failed: {e}")
    
    # Validate explanation structure
    assert "value" in result, "Missing 'value' in explanation"
    assert "inputs" in result, "Missing 'inputs' in explanation"
    assert "citations" in result, "Missing 'citations' in explanation"
    
    # Validate inputs
    inputs = result["inputs"]
    assert "revenue" in inputs, "Missing 'revenue' input"
    assert "costOfRevenue" in inputs, "Missing 'costOfRevenue' input"
    
    # Validate input structure
    for input_name, input_data in inputs.items():
        assert "value" in input_data, f"Input {input_name} missing 'value'"
        assert "citation" in input_data, f"Input {input_name} missing 'citation'"
    
    print(f"✅ Explain test passed: {result['value']:.2f}")

def test_golden_verify(httpx_client):
    """Test expression verification with golden data"""
    
    payload = {
    "ticker": "KO",
    "expr": "grossProfit / revenue",
    "assert_value": "≈ 0.62",
    "tolerance": 0.05,
    "period": "latest",
        "freq": "Q"
    }
    
    url = f"{BASE}/v1/finance/calc/verify-expression"
    
    try:
        response = httpx_client.post(
            url,
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
    except httpx.HTTPError as e:
        pytest.fail(f"Verify API call failed: {e}")
    
    # Validate verification structure
    assert "verified" in result, "Missing 'verified' in verification"
    assert "observed" in result, "Missing 'observed' in verification"
    assert "expected" in result, "Missing 'expected' in verification"
    assert "difference" in result, "Missing 'difference' in verification"
    
    # The verification should pass within tolerance
    assert result["verified"] == True, f"Verification failed: {result}"
    
    print(f"✅ Verify test passed: {result['verified']} (observed: {result['observed']:.3f})")

if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
