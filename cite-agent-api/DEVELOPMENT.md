# Nocturnal Archive API – Development Quickstart

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
```

The base requirements install the FastAPI runtime; the dev manifest layers in pytest and async test helpers so the finance regression suite (`tests/test_kpis_golden.py`) can execute locally.

## Useful Commands

```bash
python3 -m pytest tests/enhanced -q
python3 -m pytest tests/test_kpis_golden.py -q
```

## Data Prerequisites

Finance endpoints expect the SEC symbol map and company facts to be primed. The resolver now reads from `data/company_tickers.json` by default and refreshes using `src.jobs.symbol_map`. To refresh the cache manually:

```bash
python3 -m src.jobs.symbol_map
```

This writes `data/symbol_map.parquet` and keeps the in-process cache current. For full facts ingestion, run the SEC fetch job provided in `src/ingest/sec` (see `docs/DEPLOYMENT_GUIDE.md`).
