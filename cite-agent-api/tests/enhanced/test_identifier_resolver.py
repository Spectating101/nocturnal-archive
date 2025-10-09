import asyncio

import pytest

from src.identifiers.resolve import clear_identifier_cache, resolve_cik, resolve_ticker


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_identifier_cache()


def test_resolve_ticker_sync_event_loop():
    mapping = asyncio.run(resolve_ticker("AAPL"))
    assert mapping is not None
    assert mapping.ticker == "AAPL"
    assert mapping.cik
    assert mapping.company_name


@pytest.mark.asyncio
async def test_resolve_cik_async():
    mapping = await resolve_cik("0000320193")
    assert mapping is not None
    assert mapping.ticker == "AAPL"
    assert mapping.cik.endswith("20193")
