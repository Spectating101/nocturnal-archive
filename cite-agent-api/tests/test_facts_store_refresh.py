import pytest

from src.facts.store import Fact, FactsStore, PeriodType


@pytest.mark.asyncio
async def test_get_fact_refreshes_stale_data(monkeypatch):
    store = FactsStore()

    ticker = "AMD"
    cik = "0000000000"
    concept = "us-gaap:Revenues"

    old_fact = Fact(
        concept=concept,
        value=1_647_000_000.0,
        unit="USD",
        period="2018-Q1",
        period_type=PeriodType.DURATION,
        accession="0000000000-18-000001",
        fragment_id=None,
        url="https://www.sec.gov/Archives/edgar/data/0000000000/0000000000-18-000001",
        dimensions={},
        quality_flags=[],
        company_name="Advanced Micro Devices, Inc.",
        cik=cik,
        start_date="2017-12-31",
        end_date="2018-03-31",
    )

    store.facts_by_company[cik] = {concept: [old_fact]}
    store.facts_by_concept[concept] = [old_fact]
    store._ticker_to_cik[ticker.upper()] = cik

    async def fake_resolve(_: str) -> str:
        return cik

    async def fake_lazy_load(_: str, __: str, force_refresh: bool = False) -> None:
        assert force_refresh is True
        refreshed_fact = Fact(
            concept=concept,
            value=7_685_000_000.0,
            unit="USD",
            period="2025-Q2",
            period_type=PeriodType.DURATION,
            accession="0000000000-25-000002",
            fragment_id=None,
            url="https://www.sec.gov/Archives/edgar/data/0000000000/0000000000-25-000002",
            dimensions={},
            quality_flags=[],
            company_name="Advanced Micro Devices, Inc.",
            cik=cik,
            start_date="2025-03-31",
            end_date="2025-06-30",
        )
        store.facts_by_company[cik] = {concept: [refreshed_fact]}
        store.facts_by_concept[concept] = [refreshed_fact]

    monkeypatch.setattr(store, "_resolve_ticker_to_cik", fake_resolve, raising=False)
    monkeypatch.setattr(store, "_lazy_load_company_facts", fake_lazy_load, raising=False)

    result = await store.get_fact(ticker, concept, period="latest", freq="Q")

    assert result is not None
    assert result.period == "2025-Q2"
    assert result.value == pytest.approx(7_685_000_000.0)