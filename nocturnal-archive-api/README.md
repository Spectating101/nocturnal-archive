# FinSight API - Regulator-First Financial Data

> **This isn't yfinance.** FinSight provides regulator-first financial data with full provenance, multi-jurisdiction support, and cited mathematics.

## 🚀 Quick Start

### 1. "A = B - C" with Full Citations

```bash
# Explain gross profit calculation with proofs
curl -X POST -H "X-API-Key: demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","expr":"grossProfit = revenue - costOfRevenue","period":"2024-Q4","freq":"Q"}' \
  http://localhost:8000/v1/finance/calc/explain
```

**Response:**
```json
{
  "expr": "grossProfit = revenue - costOfRevenue",
  "value": 49234000000,
  "left": {
    "concept": "grossProfit",
    "value": 49234000000,
    "unit": "USD"
  },
  "right": {
    "terms": [
      {
        "concept": "revenue",
        "value": 119575000000,
        "accession": "0000320193-24-000006",
        "unit": "USD",
        "scale": "U",
        "fx_used": null
      },
      {
        "concept": "costOfRevenue", 
        "value": 70341000000,
        "accession": "0000320193-24-000006",
        "unit": "USD",
        "scale": "U",
        "fx_used": null
      }
    ]
  },
  "citations": [
    {
      "source": "SEC EDGAR 10-K Filing",
      "accession": "0000320193-24-000006",
      "url": "https://www.sec.gov/Archives/edgar/...",
      "page": "Consolidated Statements of Operations"
    }
  ]
}
```

### 2. Segment Analysis (yfinance can't do this)

```bash
# Get AAPL revenue by geography (Greater China, Americas, Europe)
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/segments/AAPL/revenue?dim=Geography&freq=Q&limit=8"
```

**Response:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue",
  "dimension": "Geography",
  "series": [
    {
      "segment": "Americas",
      "points": [
        {"period": "2024-Q4", "value": 50414000000, "citation": {...}},
        {"period": "2024-Q3", "value": 48190000000, "citation": {...}}
      ]
    },
    {
      "segment": "Greater China",
      "points": [
        {"period": "2024-Q4", "value": 20819000000, "citation": {...}},
        {"period": "2024-Q3", "value": 19290000000, "citation": {...}}
      ]
    },
    {
      "segment": "Europe", 
      "points": [
        {"period": "2024-Q4", "value": 24189000000, "citation": {...}},
        {"period": "2024-Q3", "value": 22920000000, "citation": {...}}
      ]
    }
  ]
}
```

### 3. Derived KPIs with Citations Per Point

```bash
# ROE TTM series with full provenance
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/calc/series/AAPL/roe?freq=Q&ttm=true&limit=12"
```

**Response:**
```json
{
  "ticker": "AAPL",
  "metric": "roe",
  "freq": "Q",
  "ttm": true,
  "series": [
    {
      "period": "2024-Q4",
      "value": 1.47,
      "formula": "netIncome / shareholdersEquity",
      "citations": [
        {
          "concept": "netIncome",
          "value": 33916000000,
          "accession": "0000320193-24-000006",
          "unit": "USD"
        },
        {
          "concept": "shareholdersEquity",
          "value": 23060000000,
          "accession": "0000320193-24-000006", 
          "unit": "USD"
        }
      ]
    }
  ]
}
```

## 🌍 Multi-Jurisdiction Support

### US GAAP (AAPL)
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/AAPL/revenue?freq=Q&limit=4"
```

### IFRS + EUR (ASML)
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/ASML/revenue?freq=Q&limit=4"
```

### IFRS + TWD (TSM) with FX normalization
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/TSM/revenue?freq=Q&limit=4"
```

## 📊 What Makes FinSight Different

### ✅ **Regulator-First Data**
- SEC EDGAR XBRL facts with full provenance
- Every number links back to official filings
- Amendment and restatement tracking

### ✅ **Multi-Jurisdiction**
- US GAAP + IFRS concept mapping
- Cross-border currency normalization (EUR, TWD, GBP → USD)
- Unit scaling (K, M, B, T) with metadata

### ✅ **Cited Mathematics**
- Every calculation shows "A = B - C" with clickable SEC citations
- Full audit trail for derived metrics
- Amendment control (`as_reported=true|false`)

### ✅ **Segment-Aware Analysis**
- Geographic breakdowns (Americas, Europe, Greater China)
- Business segment analysis
- Product-level revenue splits

### ✅ **Production-Ready**
- Rate limiting and circuit breakers
- RFC 7807 error responses
- Health monitoring and status endpoints
- PDF snapshot reports

## 🔧 API Reference

### Core Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /v1/finance/kpis/{ticker}/{metric}` | Get KPI time series |
| `GET /v1/finance/calc/{ticker}/{metric}` | Calculate derived metric |
| `GET /v1/finance/calc/series/{ticker}/{metric}` | Get calculated series |
| `POST /v1/finance/calc/explain` | Explain calculation with proofs |
| `GET /v1/finance/segments/{ticker}/{metric}` | Get segment breakdown |
| `GET /v1/finance/status` | Health check for all sources |
| `GET /v1/finance/reports/{ticker}/{period}.pdf` | Generate PDF report |

### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `freq` | Frequency (Q, A) | `Q` |
| `limit` | Number of periods | `12` |
| `ttm` | Trailing twelve months | `true` |
| `dim` | Segment dimension | `Geography` |
| `as_reported` | Use original filings | `true` |
| `accession` | Pin to specific filing | `0000320193-24-000006` |

## 🚀 CLI Example

```bash
# Install FinSight CLI
pip install finsight-cli

# Get AAPL revenue with citations
finsight kpis AAPL revenue --limit 8 --format json

# Explain gross margin calculation
finsight calc explain AAPL "grossMargin = (revenue - costOfRevenue) / revenue"

# Generate PDF report
finsight report AAPL 2024-Q4 --format pdf --output aapl-report.pdf
```

## 📈 Supported Companies

### US GAAP (USD)
- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation  
- **NVDA** - NVIDIA Corporation
- **AMZN** - Amazon.com Inc.

### IFRS (Multi-Currency)
- **ASML** - ASML Holding N.V. (EUR)
- **TSM** - Taiwan Semiconductor (TWD)
- **SAP** - SAP SE (EUR)
- **SHEL** - Shell plc (USD/EUR/GBP)

## 🔒 Authentication

```bash
# Set your API key
export NOCTURNAL_KEY="your-api-key-here"

# Or use in requests
curl -H "X-API-Key: your-api-key-here" \
  "http://localhost:8000/v1/finance/kpis/AAPL/revenue"
```

## 📊 Status & Health

```bash
# Check all data sources
curl http://localhost:8000/v1/finance/status

# Response
{
  "overall_status": "healthy",
  "health_percentage": 95.2,
  "sources": [
    {
      "id": "sec_edgar",
      "name": "SEC EDGAR",
      "status": "healthy",
      "latency_ms": 245
    },
    {
      "id": "ecb_fx", 
      "name": "ECB FX Rates",
      "status": "healthy",
      "latency_ms": 89
    }
  ]
}
```

## 🎯 SLOs & Monitoring

- **Availability**: ≥ 99.9%
- **5xx Error Rate**: ≤ 0.1%
- **Latency**: Cached ≤ 350ms, EDGAR ≤ 1.5s
- **Circuit Breaker**: < 1% open rate
- **Cost Control**: No key exceeds 3× baseline

## 🚀 Getting Started

1. **Start the server:**
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

2. **Run the alpha audit:**
   ```bash
   bash scripts/alpha_audit.sh
   ```

3. **Test the demo endpoints:**
   ```bash
   bash scripts/smoke_finance.sh
   ```

## 📚 Documentation

- [API Reference](docs/api-reference.md)
- [Error Codes](docs/error-codes.md)
- [Data Sources](docs/data-sources.md)
- [Calculation Engine](docs/calculations.md)

## 🏆 Why FinSight?

**vs. yfinance:**
- ✅ Regulator-first (SEC EDGAR vs. Yahoo Finance)
- ✅ Full provenance and citations
- ✅ Multi-jurisdiction (US + IFRS)
- ✅ Segment-level analysis
- ✅ Amendment and restatement control
- ✅ Production-ready error handling

**vs. Bloomberg/Refinitiv:**
- ✅ Developer-friendly API
- ✅ Transparent pricing
- ✅ Open source components
- ✅ Self-hosted option

---

**FinSight: Regulator-First Financial Data with Full Provenance** 🚀