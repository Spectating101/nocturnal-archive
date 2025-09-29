"""
Tests for SEC symbol mapping functionality
"""
import pytest
import pandas as pd
from src.jobs.symbol_map import (
    fetch_symbol_map, 
    load_symbol_map, 
    cik_for_ticker, 
    ticker_for_cik,
    search_companies
)


def test_fetch_symbol_map():
    """Test fetching symbol map from SEC"""
    df = fetch_symbol_map()
    
    # Validate DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert {"ticker", "cik", "title"} <= set(df.columns)
    assert len(df) > 1000  # Should have thousands of companies
    
    # Validate data quality
    assert not df.ticker.isna().any()
    assert not df.cik.isna().any()
    assert not df.title.isna().any()
    
    # Validate CIK format (10-digit zero-padded)
    assert all(len(cik) == 10 for cik in df.cik)
    assert all(cik.isdigit() for cik in df.cik)
    
    # Validate tickers are unique
    assert df.ticker.nunique() == len(df)
    
    # Check for known companies
    tickers = df.ticker.str.upper()
    assert "AAPL" in tickers.values
    assert "MSFT" in tickers.values
    assert "GOOGL" in tickers.values


def test_load_symbol_map():
    """Test loading local symbol map"""
    df = load_symbol_map()
    
    assert isinstance(df, pd.DataFrame)
    # Should have the expected columns even if empty
    assert {"ticker", "cik", "title"} <= set(df.columns)


def test_cik_for_ticker():
    """Test CIK lookup by ticker"""
    cik = cik_for_ticker("AAPL")
    assert cik is not None
    assert len(cik) == 10
    assert cik.isdigit()
    
    # Test case insensitive
    cik_upper = cik_for_ticker("aapl")
    assert cik == cik_upper
    
    # Test non-existent ticker
    cik_missing = cik_for_ticker("NONEXISTENT")
    assert cik_missing is None


def test_ticker_for_cik():
    """Test ticker lookup by CIK"""
    # First get a known CIK
    cik = cik_for_ticker("AAPL")
    assert cik is not None
    
    # Then look it up
    ticker = ticker_for_cik(cik)
    assert ticker == "AAPL"
    
    # Test non-existent CIK
    ticker_missing = ticker_for_cik("0000000000")
    assert ticker_missing is None


def test_search_companies():
    """Test company search functionality"""
    results = search_companies("Apple", limit=5)
    assert isinstance(results, pd.DataFrame)
    
    if not results.empty:
        # Should find Apple
        titles = results.title.str.lower()
        tickers = results.ticker.str.upper()
        assert any("apple" in title for title in titles) or "AAPL" in tickers.values
    
    # Test ticker search
    ticker_results = search_companies("AAPL", limit=5)
    assert isinstance(ticker_results, pd.DataFrame)
    
    if not ticker_results.empty:
        assert "AAPL" in ticker_results.ticker.values


def test_symbol_map_data_quality():
    """Test data quality of symbol map"""
    df = load_symbol_map()
    
    if df.empty:
        pytest.skip("No symbol map data available")
    
    # No empty tickers
    assert not df.ticker.str.strip().eq("").any()
    
    # No empty CIKs
    assert not df.cik.str.strip().eq("").any()
    
    # No empty titles
    assert not df.title.str.strip().eq("").any()
    
    # Tickers should be reasonable length
    assert df.ticker.str.len().between(1, 10).all()
    
    # All CIKs should be 10 digits
    assert df.cik.str.len().eq(10).all()
    assert df.cik.str.match(r"^\d{10}$").all()


def test_known_companies():
    """Test that we can find major companies"""
    known_companies = {
        "AAPL": "Apple Inc",
        "MSFT": "Microsoft Corp",
        "GOOGL": "Alphabet Inc",
        "AMZN": "Amazon.com Inc",
        "TSLA": "Tesla Inc"
    }
    
    for ticker, expected_title in known_companies.items():
        cik = cik_for_ticker(ticker)
        assert cik is not None, f"Could not find CIK for {ticker}"
        
        # Look up the ticker back from CIK
        found_ticker = ticker_for_cik(cik)
        assert found_ticker == ticker, f"CIK {cik} did not map back to {ticker}"
        
        # Search for the company by name
        search_results = search_companies(expected_title.split()[0], limit=10)
        if not search_results.empty:
            found_tickers = search_results.ticker.str.upper()
            assert ticker in found_tickers.values, f"Could not find {ticker} in search for {expected_title}"
