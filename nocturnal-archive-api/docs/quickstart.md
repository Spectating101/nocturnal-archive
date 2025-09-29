# FinSight Quickstart Guide

Get up and running with FinSight in 5 minutes.

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-org/finsight-api.git
cd finsight-api

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 🔑 Authentication

```bash
# Set your API key
export NOCTURNAL_KEY="demo-key-123"

# Or use in requests
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/AAPL/revenue"
```

## 📊 Your First API Call

```bash
# Get Apple's revenue for the last 4 quarters
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/AAPL/revenue?freq=Q&limit=4"
```

**Response:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue",
  "freq": "Q",
  "data": [
    {
      "period": "2024-Q4",
      "value": 119575000000,
      "citation": {
        "source": "SEC EDGAR",
        "accession": "0000320193-24-000006",
        "url": "https://www.sec.gov/Archives/edgar/..."
      }
    }
  ]
}
```

## 🧮 Calculate Derived Metrics

```bash
# Calculate gross margin with full explanation
curl -X POST -H "X-API-Key: demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","expr":"grossMargin = (revenue - costOfRevenue) / revenue","period":"2024-Q4","freq":"Q"}' \
  "http://localhost:8000/v1/finance/calc/explain"
```

## 🌍 Multi-Jurisdiction Examples

### US Company (GAAP)
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/MSFT/revenue?freq=Q&limit=4"
```

### European Company (IFRS + EUR)
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/ASML/revenue?freq=Q&limit=4"
```

### Asian Company (IFRS + TWD)
```bash
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/kpis/TSM/revenue?freq=Q&limit=4"
```

## 📈 Segment Analysis

```bash
# Get revenue by geography
curl -H "X-API-Key: demo-key-123" \
  "http://localhost:8000/v1/finance/segments/AAPL/revenue?dim=Geography&freq=Q&limit=8"
```

## 📊 Generate Reports

```bash
# Generate PDF report
curl -H "X-API-Key: demo-key-123" \
  -o aapl-report.pdf \
  "http://localhost:8000/v1/finance/reports/AAPL/2024-Q4.pdf"
```

## 🔍 Health Check

```bash
# Check system health
curl "http://localhost:8000/v1/finance/status"
```

## 🧪 Run Tests

```bash
# Run smoke tests
bash scripts/smoke_finance.sh

# Run alpha audit
bash scripts/alpha_audit.sh

# Prime cache
bash scripts/prime_cache.sh
```

## 📚 Next Steps

1. **Explore the API**: Visit `http://localhost:8000/docs` for interactive documentation
2. **Read the full docs**: Check out [API Reference](api-reference.md)
3. **Join the community**: [Discord](https://discord.gg/finsight) | [GitHub](https://github.com/your-org/finsight-api)

---

**Need help?** Check our [FAQ](faq.md) or [contact support](mailto:support@finsight.dev).