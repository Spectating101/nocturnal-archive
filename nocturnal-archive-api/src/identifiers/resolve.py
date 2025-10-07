"""Robust ticker/CIK resolution backed by local SEC symbol datasets."""
from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import structlog

from src.core.paths import DATA_DIR
from src.jobs import symbol_map

logger = structlog.get_logger(__name__)

_SYMBOL_CACHE_LOCK = threading.RLock()
_SYMBOL_CACHE: Dict[str, "TickerMapping"] = {}
_CIK_CACHE: Dict[str, "TickerMapping"] = {}
_CACHE_PRIMED = False


@dataclass(slots=True)
class TickerMapping:
    """Normalized mapping entry for a listed security."""

    ticker: str
    cik: str
    company_name: str
    exchange: Optional[str] = None
    sic: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


async def resolve_ticker(ticker: str, *, force_refresh: bool = False) -> Optional[TickerMapping]:
    """Resolve a ticker symbol to its CIK and metadata.

    The resolver prefers the cached parquet/JSON symbol map written by
    :mod:`src.jobs.symbol_map`. If the cache is missing or stale it will refresh
    in the background using the existing job helpers. This keeps the runtime
    dependency graph small—no direct HTTP calls here—and lets us serve lookups
    even when offline (using the bundled `data/company_tickers.json`).
    """

    ticker = (ticker or "").strip().upper()
    if not ticker:
        return None

    await _ensure_cache(force_refresh=force_refresh)

    with _SYMBOL_CACHE_LOCK:
        mapping = _SYMBOL_CACHE.get(ticker)
        if mapping:
            return mapping

    # Cache miss: try a targeted refresh just for this ticker to keep latency low
    logger.info("Ticker cache miss", ticker=ticker)
    await _refresh_cache()

    with _SYMBOL_CACHE_LOCK:
        return _SYMBOL_CACHE.get(ticker)


async def resolve_cik(cik: str, *, force_refresh: bool = False) -> Optional[TickerMapping]:
    """Resolve a CIK to its ticker mapping."""

    cik = (cik or "").strip().lstrip("0")
    if not cik:
        return None

    await _ensure_cache(force_refresh=force_refresh)

    with _SYMBOL_CACHE_LOCK:
        mapping = _CIK_CACHE.get(cik)
        if mapping:
            return mapping

    logger.info("CIK cache miss", cik=cik)
    await _refresh_cache()

    with _SYMBOL_CACHE_LOCK:
        return _CIK_CACHE.get(cik)


def clear_identifier_cache() -> None:
    """Reset in-process caches (useful for tests)."""

    global _CACHE_PRIMED
    with _SYMBOL_CACHE_LOCK:
        _SYMBOL_CACHE.clear()
        _CIK_CACHE.clear()
        _CACHE_PRIMED = False


async def _ensure_cache(*, force_refresh: bool = False) -> None:
    global _CACHE_PRIMED
    if force_refresh or not _CACHE_PRIMED:
        await _refresh_cache(force_refresh=force_refresh)


async def _refresh_cache(*, force_refresh: bool = False) -> None:
    """Refresh caches using symbol_map job helpers."""

    def _load_dataframe() -> pd.DataFrame:
        # Try fast path via job helper (handles parquet/JSON refresh logic)
        return symbol_map.load_symbol_map(force_refresh=force_refresh)

    df = await asyncio.to_thread(_load_dataframe)

    if df.empty:
        # Offline fallback: load bundled company_tickers JSON if pandas DF empty
        fallback_path = DATA_DIR / "company_tickers.json"
        if fallback_path.exists():
            with fallback_path.open("r") as handle:
                raw = json.load(handle)
            rows = [
                {
                    "cik": str(entry.get("cik_str", "")).strip(),
                    "ticker": str(entry.get("ticker", "")).strip().upper(),
                    "title": entry.get("title", ""),
                }
                for entry in raw.values() if isinstance(entry, dict)
            ]
            df = pd.DataFrame(rows)
        else:
            logger.warning("No symbol datasets available; identifier cache remains empty")
            return

    # Normalize and repopulate caches
    df = df.dropna(subset=["ticker", "cik"]).drop_duplicates(subset=["ticker"])
    df["ticker"] = df["ticker"].str.upper()
    df["cik"] = df["cik"].astype(str).str.zfill(10)

    local_symbol_cache: Dict[str, TickerMapping] = {}
    local_cik_cache: Dict[str, TickerMapping] = {}

    for _, row in df.iterrows():
        mapping = TickerMapping(
            ticker=row["ticker"],
            cik=row["cik"],
            company_name=row.get("title", ""),
            exchange=row.get("exchange"),
            sic=row.get("sic"),
            metadata={
                key: str(value)
                for key in ("sic_description", "fye", "entity_type")
                if (value := row.get(key)) is not None and not pd.isna(value)
            },
        )
        local_symbol_cache[mapping.ticker] = mapping
        local_cik_cache[mapping.cik] = mapping
        local_cik_cache[mapping.cik.lstrip("0")] = mapping

    with _SYMBOL_CACHE_LOCK:
        _SYMBOL_CACHE.clear()
        _SYMBOL_CACHE.update(local_symbol_cache)

        _CIK_CACHE.clear()
        _CIK_CACHE.update(local_cik_cache)

        global _CACHE_PRIMED
        _CACHE_PRIMED = True

    logger.info(
        "Identifier cache primed",
        tickers=len(_SYMBOL_CACHE),
        ciks=len(_CIK_CACHE),
        force_refresh=force_refresh,
    )
