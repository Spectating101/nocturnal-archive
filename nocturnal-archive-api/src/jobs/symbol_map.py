"""SEC symbol mapping utilities with smart caching and auto-refresh."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import structlog

from src.core.paths import SYMBOL_MAP_JSON, SYMBOL_MAP_PARQUET

logger = structlog.get_logger(__name__)

# SEC API configuration
SEC_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = {"User-Agent": "Finsight/1.0 contact@example.com"}

# In-process cache (avoids repeated disk reads)
_SYMBOL_CACHE: Optional[pd.DataFrame] = None
_CACHE_TIMESTAMP: Optional[float] = None
_CACHE_TTL = 3600 * 6  # refresh cached DataFrame every 6 hours


def _should_refresh_file(path: Path, max_age_days: int = 7) -> bool:
    """Return True if the on-disk map is older than ``max_age_days``."""

    if not path.exists():
        return True

    try:
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.utcnow() - modified > timedelta(days=max_age_days)
    except OSError:
        return True


def fetch_symbol_map() -> pd.DataFrame:
    """
    Fetch the latest SEC company tickers mapping and save to local storage.

    Returns
    -------
    pd.DataFrame
        Clean symbol mapping with ``cik``, ``ticker`` and ``title`` columns.
    """

    logger.info("Fetching SEC symbol map", url=SEC_URL)

    response = requests.get(SEC_URL, headers=USER_AGENT, timeout=30)
    response.raise_for_status()

    SYMBOL_MAP_JSON.write_bytes(response.content)
    logger.debug("Saved raw SEC symbol map", path=str(SYMBOL_MAP_JSON))

    data = json.loads(response.content)
    rows = [
        {
            "cik": entry["cik_str"],
            "ticker": entry["ticker"],
            "title": entry["title"],
        }
        for entry in data.values()
    ]

    df = pd.DataFrame(rows)
    df = df.dropna().drop_duplicates(subset=["ticker"])
    df["cik"] = df["cik"].astype(int).astype(str).str.zfill(10)

    SYMBOL_MAP_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SYMBOL_MAP_PARQUET, index=False)
    logger.info("Stored SEC symbol map", rows=len(df), path=str(SYMBOL_MAP_PARQUET))

    return df


def load_symbol_map(force_refresh: bool = False) -> pd.DataFrame:
    """Load the symbol map, refreshing from the SEC if necessary."""

    global _SYMBOL_CACHE, _CACHE_TIMESTAMP

    cache_age = time.time() - _CACHE_TIMESTAMP if _CACHE_TIMESTAMP else None
    if (
        not force_refresh
        and _SYMBOL_CACHE is not None
        and cache_age is not None
        and cache_age < _CACHE_TTL
    ):
        return _SYMBOL_CACHE

    need_refresh = force_refresh or _should_refresh_file(SYMBOL_MAP_PARQUET)

    if SYMBOL_MAP_PARQUET.exists() and not need_refresh:
        try:
            _SYMBOL_CACHE = pd.read_parquet(SYMBOL_MAP_PARQUET)
            _CACHE_TIMESTAMP = time.time()
            return _SYMBOL_CACHE
        except Exception as exc:  # pragma: no cover - parquet read edge cases
            logger.warning("Failed to load cached symbol map", error=str(exc))
            # Try JSON fallback if parquet fails (e.g., missing pyarrow)
            if SYMBOL_MAP_JSON.exists():
                try:
                    with open(SYMBOL_MAP_JSON) as f:
                        data = json.load(f)
                    rows = [
                        {
                            "cik": str(entry["cik_str"]).zfill(10),
                            "ticker": entry["ticker"],
                            "title": entry["title"],
                        }
                        for entry in data.values()
                    ]
                    _SYMBOL_CACHE = pd.DataFrame(rows).dropna().drop_duplicates(subset=["ticker"])
                    _CACHE_TIMESTAMP = time.time()
                    logger.info("Loaded symbol map from JSON fallback", rows=len(_SYMBOL_CACHE))
                    return _SYMBOL_CACHE
                except Exception as json_error:
                    logger.error("JSON fallback also failed", error=str(json_error))
            need_refresh = True

    if need_refresh:
        try:
            _SYMBOL_CACHE = fetch_symbol_map()
            _CACHE_TIMESTAMP = time.time()
            return _SYMBOL_CACHE
        except Exception as exc:
            logger.error("Unable to refresh SEC symbol map", error=str(exc))
            if SYMBOL_MAP_PARQUET.exists():
                try:
                    _SYMBOL_CACHE = pd.read_parquet(SYMBOL_MAP_PARQUET)
                    _CACHE_TIMESTAMP = time.time()
                    return _SYMBOL_CACHE
                except Exception:  # pragma: no cover
                    pass

    if _SYMBOL_CACHE is None:
        _SYMBOL_CACHE = pd.DataFrame(columns=["cik", "ticker", "title"])
        _CACHE_TIMESTAMP = time.time()

    return _SYMBOL_CACHE


def cik_for_ticker(ticker: str) -> Optional[str]:
    """
    Get CIK for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        str: 10-digit CIK if found, None otherwise
    """
    if not ticker:
        return None

    df = load_symbol_map()
    if df.empty:
        logger.warning("Symbol map empty when resolving ticker", ticker=ticker)
        return None

    matches = df[df.ticker.str.upper() == ticker.upper()]
    if matches.empty:
        logger.info("Ticker not found in symbol map", ticker=ticker)
        return None

    return matches.cik.iloc[0]


def ticker_for_cik(cik: str) -> Optional[str]:
    """
    Get ticker for a given CIK.

    Args:
        cik: 10-digit CIK

    Returns:
        str: Ticker symbol if found, None otherwise
    """
    if not cik:
        return None

    df = load_symbol_map()
    if df.empty:
        logger.warning("Symbol map empty when resolving CIK", cik=cik)
        return None

    cik_normalized = str(cik).zfill(10)
    matches = df[df.cik == cik_normalized]
    if matches.empty:
        logger.info("CIK not found in symbol map", cik=cik_normalized)
        return None

    return matches.ticker.iloc[0]


def search_companies(query: str, limit: int = 10) -> pd.DataFrame:
    """
    Search companies by ticker or company title.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        pd.DataFrame: Matching companies
    """
    df = load_symbol_map()
    if df.empty or not query:
        return pd.DataFrame(columns=["cik", "ticker", "title"])

    query_lower = query.lower()
    mask = (
        df.ticker.str.lower().str.contains(query_lower)
        | df.title.str.lower().str.contains(query_lower)
    )

    return df[mask].head(limit)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch or search SEC symbol map")
    parser.add_argument("command", choices=["fetch", "search"], help="Operation to perform")
    parser.add_argument("arg", nargs="?", help="Ticker or company query for search")
    args = parser.parse_args()

    if args.command == "fetch":
        df = fetch_symbol_map()
        logger.info("Fetched SEC symbol map", rows=len(df))
        print(f"Fetched {len(df)} symbols")
        print("\nSample:")
        print(df.head())
    elif args.command == "search":
        if not args.arg:
            parser.error("search command requires a query argument")
        results = search_companies(args.arg)
        if results.empty:
            print("No matches found")
        else:
            print(results.to_string(index=False))
