"""
Cross-source financial data validation service.
Compares SEC EDGAR fundamentals with market data providers
and produces a trust score with detailed provenance.
"""

from __future__ import annotations

import asyncio
import os
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from src.adapters.alpha_vantage import AlphaVantageAdapter
from src.adapters.yahoo_finance_direct import YahooFinanceDirectAdapter
from src.adapters.sec_facts import get_sec_facts_adapter

logger = structlog.get_logger(__name__)


@dataclass
class ValidationSourceResult:
    """Normalized data point returned by a validation source."""

    source: str
    value: Optional[float]
    period: Optional[str]
    unit: Optional[str]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class ValidationResult:
    """Cross-source validation summary."""

    ticker: str
    metric: str
    period: str
    freq: str
    trust_score: float
    sources_count: int
    consensus_value: Optional[float]
    discrepancies: List[str]
    sources: List[ValidationSourceResult]
    validation_time: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "metric": self.metric,
            "period": self.period,
            "freq": self.freq,
            "trust_score": self.trust_score,
            "sources_count": self.sources_count,
            "consensus_value": self.consensus_value,
            "discrepancies": self.discrepancies,
            "sources": [source.to_dict() for source in self.sources],
            "validation_time": self.validation_time,
        }


class DataValidator:
    """Compare financial metrics across multiple providers."""

    DISCREPANCY_THRESHOLD = 0.10  # 10%

    def __init__(self, alpha_vantage_key: Optional[str] = None):
        api_key = alpha_vantage_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.sec_adapter = get_sec_facts_adapter()
        self.yahoo_adapter = YahooFinanceDirectAdapter()
        self.alpha_adapter = AlphaVantageAdapter(api_key)

    async def close(self) -> None:
        """Close underlying HTTP sessions."""
        await asyncio.gather(
            self.yahoo_adapter.close(),
            self.alpha_adapter.close(),
            return_exceptions=True,
        )
        try:
            await self.sec_adapter.close()
        except AttributeError:
            # Global adapter may not expose close during tests
            pass

    async def cross_validate(
        self,
        ticker: str,
        metric: str,
        period: str = "latest",
        freq: str = "Q",
    ) -> ValidationResult:
        """Compare metric across SEC, Yahoo Finance, and Alpha Vantage."""

        logger.info(
            "Cross-validating metric",
            ticker=ticker,
            metric=metric,
            period=period,
            freq=freq,
        )

        fetch_tasks = [
            self._fetch_sec_fact(ticker, metric, period, freq),
            self._fetch_yahoo_financial(ticker, metric, freq),
            self._fetch_alpha_financial(ticker, metric, freq),
        ]

        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        sources: List[ValidationSourceResult] = []

        for result in results:
            if isinstance(result, ValidationSourceResult):
                sources.append(result)
            elif isinstance(result, Exception):
                logger.debug(
                    "Validation source error",
                    ticker=ticker,
                    metric=metric,
                    error=str(result),
                )

        numeric_sources = [src for src in sources if isinstance(src.value, (int, float))]
        values = [src.value for src in numeric_sources if src.value is not None]

        if not values:
            raise ValueError(
                f"No validation sources available for {ticker} {metric} (all providers returned no data)"
            )

        consensus = statistics.median(values)
        discrepancies = self._compute_discrepancies(consensus, numeric_sources)
        trust_score = self._compute_trust_score(values, consensus, discrepancies)

        validation = ValidationResult(
            ticker=ticker,
            metric=metric,
            period=period,
            freq=freq,
            trust_score=trust_score,
            sources_count=len(values),
            consensus_value=consensus,
            discrepancies=discrepancies,
            sources=sources,
            validation_time=datetime.utcnow().isoformat(),
        )

        logger.info(
            "Cross-validation completed",
            ticker=ticker,
            metric=metric,
            trust_score=trust_score,
            discrepancies=len(discrepancies),
        )
        return validation

    async def _fetch_sec_fact(
        self,
        ticker: str,
        metric: str,
        period: str,
        freq: str,
    ) -> Optional[ValidationSourceResult]:
        try:
            fact = await self.sec_adapter.get_fact(ticker, metric, period=period, freq=freq)
            if not fact:
                return None

            unit = fact.get("unit", "USD")
            citation = fact.get("citation", {})
            return ValidationSourceResult(
                source="sec_edgar",
                value=fact.get("value"),
                period=fact.get("period"),
                unit=unit,
                details={
                    "concept": fact.get("concept"),
                    "accession": citation.get("accession"),
                    "url": citation.get("url"),
                    "taxonomy": citation.get("taxonomy"),
                },
            )
        except Exception as exc:
            logger.debug(
                "SEC validation fetch failed",
                ticker=ticker,
                metric=metric,
                error=str(exc),
            )
            return None

    async def _fetch_yahoo_financial(
        self,
        ticker: str,
        metric: str,
        freq: str,
    ) -> Optional[ValidationSourceResult]:
        try:
            period = "quarterly" if freq.upper() == "Q" else "annual"
            financials = await self.yahoo_adapter.get_financials(ticker, period)
            if not financials:
                return None

            key = self._metric_to_snake(metric)
            value = financials.get(key)
            if value is None:
                return None

            return ValidationSourceResult(
                source="yahoo_finance",
                value=float(value) if isinstance(value, (int, float)) else None,
                period=financials.get("period"),
                unit="USD",
                details={"raw": financials},
            )
        except Exception as exc:
            logger.debug(
                "Yahoo Finance validation fetch failed",
                ticker=ticker,
                metric=metric,
                error=str(exc),
            )
            return None

    async def _fetch_alpha_financial(
        self,
        ticker: str,
        metric: str,
        freq: str,
    ) -> Optional[ValidationSourceResult]:
        try:
            period = "quarterly" if freq.upper() == "Q" else "annual"
            financials = await self.alpha_adapter.get_financials(ticker, period)
            if not financials:
                return None

            key = self._metric_to_snake(metric)
            value = financials.get(key)
            if value is None:
                return None

            return ValidationSourceResult(
                source="alpha_vantage",
                value=float(value) if isinstance(value, (int, float)) else None,
                period=financials.get("fiscal_date_ending") or financials.get("period"),
                unit="USD",
                details={"raw": financials},
            )
        except Exception as exc:
            logger.debug(
                "Alpha Vantage validation fetch failed",
                ticker=ticker,
                metric=metric,
                error=str(exc),
            )
            return None

    def _metric_to_snake(self, metric: str) -> str:
        key = metric.replace(" ", "").replace("-", "_")
        snake = ""
        for char in key:
            if char.isupper() and snake:
                snake += "_" + char.lower()
            else:
                snake += char.lower()
        return snake

    def _compute_discrepancies(
        self,
        consensus: float,
        sources: List[ValidationSourceResult],
    ) -> List[str]:
        discrepancies: List[str] = []
        if not sources:
            return discrepancies

        for src in sources:
            value = src.value
            if value is None:
                continue
            if consensus == 0:
                diff = abs(value - consensus)
                if diff > 1e-6:
                    discrepancies.append(f"{src.source}:Δ={diff:.2f}")
                continue

            percent_diff = abs(value - consensus) / abs(consensus)
            if percent_diff > self.DISCREPANCY_THRESHOLD:
                discrepancies.append(f"{src.source}:{percent_diff:.1%}")
        return discrepancies

    def _compute_trust_score(
        self,
        values: List[float],
        consensus: float,
        discrepancies: List[str],
    ) -> float:
        if not values:
            return 0.0

        if len(values) == 1:
            # Single source verified – medium confidence
            return 65.0

        max_diff_pct = 0.0
        if consensus != 0:
            max_diff_pct = max(
                abs(value - consensus) / abs(consensus) for value in values
            )
        else:
            max_diff_pct = max(abs(value - consensus) for value in values)

        if not discrepancies:
            return 95.0 if len(values) > 1 else 85.0
        if max_diff_pct <= 0.15:
            return 75.0
        if max_diff_pct <= 0.30:
            return 55.0
        return 35.0