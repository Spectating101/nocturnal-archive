# Quick Start: Testing Restored Archive API

## Prerequisites

```bash
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api

# Install dependencies (if not already done)
pip install -r requirements.txt
```

## Environment Setup

Create `.env` file with:
```bash
# Required
OPENAI_API_KEY=your-key-here

# Optional but recommended
SEMANTIC_SCHOLAR_API_KEY=your-key-here
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your-sentry-dsn

# Optional
GOOGLE_SEARCH_API_KEY=your-key
GOOGLE_SEARCH_ENGINE_ID=your-id
```

## Start the Server

```bash
# Option 1: Direct
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: From main.py
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api
python -m src.main
```

## Test Restored Features

### 1. Health Check (Verify Middleware Stack)
```bash
curl -X GET http://localhost:8000/api/health -v

# Should see these headers:
# - X-Request-Id
# - X-Trace-ID
# - X-Process-Time
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
```

### 2. Papers Demo Search (New Route)
```bash
curl -X POST http://localhost:8000/v1/api/papers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quantum computing",
    "limit": 10,
    "sources": ["semantic_scholar", "openalex", "offline"]
  }' | jq
```

### 3. Papers Demo Info
```bash
curl http://localhost:8000/v1/api/papers/demo-info | jq
```

### 4. Multi-Provider Search (Enhanced)
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{
    "query": "machine learning interpretability",
    "limit": 15,
    "sources": ["semantic_scholar", "openalex", "pubmed", "offline"],
    "filters": {
      "year_min": 2020,
      "open_access": true,
      "min_citations": 50
    }
  }' | jq
```

### 5. Error Handling (Structured Errors)
```bash
# Test validation error
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}' | jq

# Should see structured error with request_id
```

### 6. Request Tracing
```bash
# Send custom request ID
curl -X GET http://localhost:8000/api/health \
  -H "X-Request-Id: my-test-123" -v

# Response should echo back:
# X-Request-Id: my-test-123
# X-Trace-ID: <generated-uuid>
```

## Verify Middleware Stack

### Security Headers
```bash
curl -I http://localhost:8000/api/health

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
```

### Rate Limiting
```bash
# Burst test (20 requests rapid-fire)
for i in {1..25}; do
  curl -X GET http://localhost:8000/api/health &
done
wait

# Some requests should get 429 status
```

### Large Payload Rejection
```bash
# Create 15MB payload (exceeds 10MB limit)
dd if=/dev/zero bs=1M count=15 | base64 > large.txt

curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d @large.txt

# Should get 413 Request Entity Too Large
rm large.txt
```

## Check Logs

Logs should show structured JSON with:
```json
{
  "timestamp": "2025-10-07T...",
  "level": "info",
  "event": "Request started",
  "method": "POST",
  "path": "/api/search",
  "query_params": {},
  "trace_id": "uuid-here"
}
```

## API Documentation

Visit these URLs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Kubernetes Health Probes

```bash
# Liveness (is process alive?)
curl http://localhost:8000/livez
# {"status": "alive"}

# Readiness (are dependencies OK?)
curl http://localhost:8000/readyz
# {"status": "ready", "issues": null}
# or
# {"status": "degraded", "issues": ["redis_unavailable"]}
```

## Finance APIs (FinSight)

```bash
# Calculate metric
curl http://localhost:8000/v1/finance/calc/AAPL/revenue | jq

# Get KPIs
curl http://localhost:8000/v1/finance/kpis/AAPL | jq

# Get filings
curl http://localhost:8000/v1/finance/filings/AAPL | jq
```

## Common Issues

### 1. Import Errors
```bash
# If you see "ModuleNotFoundError"
pip install -r requirements.txt

# Check Python path
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. Redis Not Available
```bash
# Start Redis if needed
docker run -d -p 6379:6379 redis:latest

# Or disable Redis-dependent features in .env
REDIS_URL=""
```

### 3. Middleware Order Issues
```bash
# Check logs for middleware warnings
grep "middleware" server.log
```

### 4. Missing API Keys
```bash
# Semantic Scholar will gracefully skip if no key
# OpenAlex works without key (polite mode)
# Offline corpus always works
```

## Performance Testing

### Concurrent Requests
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 \
  -H "Content-Type: application/json" \
  -p search.json \
  http://localhost:8000/api/search

# search.json:
# {"query": "test", "limit": 5, "sources": ["offline"]}
```

### Load Testing
```bash
# Install hey
go install github.com/rakyll/hey@latest

# 1000 requests over 10 seconds
hey -n 1000 -c 50 -m POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":5}' \
  http://localhost:8000/api/search
```

## Success Criteria

✅ Server starts without errors
✅ Health endpoint returns 200
✅ All middleware headers present
✅ Papers demo routes accessible
✅ Multi-provider search works
✅ Filters apply correctly
✅ Structured errors returned
✅ Request/Trace IDs propagated
✅ Rate limiting enforces limits
✅ Security headers present

## Next Steps

1. **Production Deploy**: Update Railway/Docker configs
2. **Monitoring**: Configure Sentry, Prometheus
3. **Documentation**: Update API docs with new routes
4. **Testing**: Add integration tests for new features
5. **Scaling**: Configure Redis for caching

## Troubleshooting Commands

```bash
# Check what's listening on port 8000
lsof -i :8000

# View server logs
tail -f server.log

# Check Python environment
python -c "import src.main; print('OK')"

# Verify middleware loaded
python -c "from src.middleware.security import SecurityMiddleware; print('OK')"

# Test imports
python -c "from src.routes import papers_demo; print('OK')"
```

## Quick Smoke Test Script

```bash
#!/bin/bash
# save as test_api.sh

BASE_URL="http://localhost:8000"

echo "Testing health..."
curl -s $BASE_URL/api/health | jq .status

echo "Testing papers demo..."
curl -s -X POST $BASE_URL/v1/api/papers/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":5}' | jq .count

echo "Testing multi-provider search..."
curl -s -X POST $BASE_URL/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":5,"sources":["offline"]}' | jq .papers[].source

echo "All tests passed!"
```

Run with:
```bash
chmod +x test_api.sh
./test_api.sh
```
