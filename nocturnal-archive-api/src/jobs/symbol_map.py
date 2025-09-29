"""
SEC symbol mapping job - fetches and maintains CIK↔ticker ground truth
"""
import json
import pandas as pd
import requests
from pathlib import Path
from src.core.paths import SYMBOL_MAP_JSON, SYMBOL_MAP_PARQUET

# SEC API configuration
SEC_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = {"User-Agent": "Finsight/1.0 contact@example.com"}


def fetch_symbol_map() -> pd.DataFrame:
    """
    Fetch the latest SEC company tickers mapping and save to local storage
    
    Returns:
        pd.DataFrame: Clean symbol mapping with cik, ticker, title columns
    """
    print(f"Fetching symbol map from {SEC_URL}")
    
    # Fetch from SEC
    response = requests.get(SEC_URL, headers=USER_AGENT, timeout=30)
    response.raise_for_status()
    
    # Save raw JSON
    SYMBOL_MAP_JSON.write_bytes(response.content)
    print(f"Saved raw JSON to {SYMBOL_MAP_JSON}")
    
    # Parse and clean data
    data = json.loads(response.content)
    rows = []
    
    for entry in data.values():
        rows.append({
            "cik": entry["cik_str"],
            "ticker": entry["ticker"],
            "title": entry["title"]
        })
    
    # Create DataFrame and clean
    df = pd.DataFrame(rows)
    
    # Remove nulls and duplicates
    df = df.dropna().drop_duplicates(subset=["ticker"])
    
    # Normalize CIK format (10-digit zero-padded)
    df["cik"] = df["cik"].astype(int).astype(str).str.zfill(10)
    
    # Save as Parquet for fast access
    df.to_parquet(SYMBOL_MAP_PARQUET, index=False)
    print(f"Saved {len(df)} symbols to {SYMBOL_MAP_PARQUET}")
    
    return df


def load_symbol_map() -> pd.DataFrame:
    """
    Load the local symbol mapping
    
    Returns:
        pd.DataFrame: Symbol mapping if available, empty DataFrame otherwise
    """
    if SYMBOL_MAP_PARQUET.exists():
        return pd.read_parquet(SYMBOL_MAP_PARQUET)
    return pd.DataFrame(columns=["cik", "ticker", "title"])


def cik_for_ticker(ticker: str) -> str | None:
    """
    Get CIK for a given ticker symbol
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        str: 10-digit CIK if found, None otherwise
    """
    df = load_symbol_map()
    if df.empty:
        return None
        
    matches = df[df.ticker.str.upper() == ticker.upper()]
    return matches.cik.iloc[0] if len(matches) > 0 else None


def ticker_for_cik(cik: str) -> str | None:
    """
    Get ticker for a given CIK
    
    Args:
        cik: 10-digit CIK
        
    Returns:
        str: Ticker symbol if found, None otherwise
    """
    df = load_symbol_map()
    if df.empty:
        return None
        
    matches = df[df.cik == cik]
    return matches.ticker.iloc[0] if len(matches) > 0 else None


def search_companies(query: str, limit: int = 10) -> pd.DataFrame:
    """
    Search companies by ticker or title
    
    Args:
        query: Search query
        limit: Maximum results to return
        
    Returns:
        pd.DataFrame: Matching companies
    """
    df = load_symbol_map()
    if df.empty:
        return pd.DataFrame()
    
    query_lower = query.lower()
    mask = (
        df.ticker.str.lower().str.contains(query_lower) |
        df.title.str.lower().str.contains(query_lower)
    )
    
    return df[mask].head(limit)


if __name__ == "__main__":
    # CLI usage
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        df = fetch_symbol_map()
        print(f"Fetched {len(df)} symbols")
        print("\nSample:")
        print(df.head())
    else:
        print("Usage: python -m src.jobs.symbol_map fetch")
