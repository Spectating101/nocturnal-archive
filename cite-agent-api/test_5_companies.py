#!/usr/bin/env python3
"""
Test 5 diverse companies to verify duration filtering fix
"""
from datetime import datetime
from typing import Iterator, Tuple

import pytest
from fastapi.testclient import TestClient

from src.main import app

API_KEY = "demo-key-123"
BASE_PATH = "/v1/finance/calc/{ticker}/grossProfit?period=latest"

# 5 diverse companies across different sectors
COMPANIES: Tuple[Tuple[str, str, str], ...] = (
    ("PLTR", "Palantir Technologies", "Tech - Data Analytics"),
    ("TSLA", "Tesla", "Automotive/Energy"),
    ("WMT", "Walmart", "Retail"),
    ("KO", "Coca-Cola", "Consumer Staples"),
    ("META", "Meta Platforms", "Communication Services"),
)

@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Session-scoped FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("ticker,name,sector", COMPANIES)
def test_company(client: TestClient, ticker: str, name: str, sector: str) -> None:
    """Test a company's latest quarterly gross profit."""
    response = client.get(
        BASE_PATH.format(ticker=ticker),
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()
    data = response.json()

    # Extract key values
    gross_profit = data.get("value")
    inputs = data.get("inputs", {})
    revenue_input = inputs.get("revenue", {})
    cost_input = inputs.get("costOfRevenue", {})

    assert gross_profit is not None, f"Missing gross profit value for {ticker}"
    assert "citation" in revenue_input, f"Missing revenue citation for {ticker}"
    assert "citation" in cost_input, f"Missing cost citation for {ticker}"

    revenue_value = revenue_input.get("value")
    cost_value = cost_input.get("value")

    assert revenue_value and revenue_value > 0, f"Revenue not populated for {ticker}"
    assert cost_value and cost_value >= 0, f"Cost of revenue missing for {ticker}"

    # Validate citations include quarterly duration when available
    citation = revenue_input.get("citation", {})
    start_date = citation.get("start")
    end_date = citation.get("end")

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        assert 60 <= days <= 125, (
            f"Citation duration {days} days outside expected quarterly window for {ticker}"
        )

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 Testing 5 Diverse Companies - Duration Filter Verification")
    print("="*80)
    print("\nPlease verify these values with ChatGPT for Q2 2025 quarterly data")
    print("(Looking for most recent QUARTERLY filing, not YTD)")
    
    for ticker, name, sector in COMPANIES:
        test_company(ticker, name, sector)
    
    print("\n" + "="*80)
    print("✅ Test Complete - Please verify values with ChatGPT!")
    print("="*80)
    print()
