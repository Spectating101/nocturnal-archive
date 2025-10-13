# Cite-Agent API Documentation

## Base URL
```
https://cite-agent-api-720dfadd602c.herokuapp.com
```

## Authentication

All API endpoints require authentication via JWT tokens. Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Getting Started

1. **Register** a new account
2. **Login** to get your JWT token
3. **Use the token** in subsequent requests

---

## Authentication Endpoints

### Register User

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@university.edu",
  "password": "your_password"
}
```

**Response:**
```json
{
  "user_id": "abc123...",
  "email": "user@university.edu",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-11-11T07:57:34.854287+00:00",
  "daily_token_limit": 25000
}
```

**Requirements:**
- Email must be from academic domain (.edu, .ac.uk, etc.)
- Password minimum 8 characters

### Login User

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@university.edu",
  "password": "your_password"
}
```

**Response:** Same as register

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "abc123...",
  "email": "user@university.edu",
  "created_at": "2025-10-12T10:00:00Z",
  "last_login": "2025-10-12T15:30:00Z",
  "tokens_used_today": 1500,
  "tokens_remaining": 23500,
  "last_token_reset": "2025-10-12T00:00:00Z"
}
```

### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

### Logout

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

---

## Research Endpoints

### Search Academic Papers

```http
POST /api/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "machine learning in healthcare",
  "limit": 10,
  "fields": ["title", "authors", "year", "doi", "abstract"]
}
```

**Response:**
```json
{
  "papers": [
    {
      "title": "Deep Learning for Medical Image Analysis",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2023,
      "doi": "10.1038/s41586-023-12345-6",
      "abstract": "This paper presents...",
      "citation_count": 150,
      "venue": "Nature Medicine",
      "url": "https://www.nature.com/articles/s41586-023-12345-6"
    }
  ],
  "total": 1,
  "sources_tried": ["semantic_scholar", "openalex", "pubmed"]
}
```

### Synthesize Research

```http
POST /api/synthesize
Authorization: Bearer <token>
Content-Type: application/json

{
  "paper_ids": ["paper1", "paper2", "paper3"],
  "max_words": 500,
  "focus": "key findings and implications"
}
```

**Response:**
```json
{
  "synthesis": "Based on the analysis of 3 papers...",
  "key_findings": [
    "Finding 1: ...",
    "Finding 2: ..."
  ],
  "implications": "The research suggests...",
  "citations": [
    {
      "paper_id": "paper1",
      "title": "Paper Title",
      "doi": "10.1038/..."
    }
  ]
}
```

### Format Citations

```http
POST /api/format
Authorization: Bearer <token>
Content-Type: application/json

{
  "citations": [
    {
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "year": 2023,
      "venue": "Journal Name",
      "doi": "10.1038/..."
    }
  ],
  "style": "apa"  // or "mla", "chicago", "ieee"
}
```

**Response:**
```json
{
  "formatted_citations": [
    "Author 1, A., & Author 2, B. (2023). Paper Title. Journal Name, 45(2), 123-145. https://doi.org/10.1038/..."
  ],
  "style": "apa"
}
```

---

## Financial Data Endpoints

### Get Financial Metrics

```http
GET /v1/finance/calc/{ticker}/{metric}
Authorization: Bearer <token>
```

**Example:**
```http
GET /v1/finance/calc/AAPL/revenue
```

**Response:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue",
  "value": 94.04,
  "unit": "billion",
  "currency": "USD",
  "period": "2025-06-28",
  "source": "SEC Filing",
  "filing_url": "https://www.sec.gov/Archives/edgar/data/0000320193/0000320193-25-000073/"
}
```

**Available Metrics:**
- `revenue` - Total revenue
- `grossProfit` - Gross profit
- `netIncome` - Net income
- `totalAssets` - Total assets
- `totalDebt` - Total debt
- `marketCap` - Market capitalization

### Get Company KPIs

```http
GET /v1/finance/kpis/{ticker}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "ticker": "AAPL",
  "kpis": {
    "revenue": 94.04,
    "gross_profit": 43.72,
    "net_income": 23.64,
    "total_assets": 352.76,
    "total_debt": 111.09,
    "market_cap": 3200.00
  },
  "currency": "USD",
  "last_updated": "2025-06-28T00:00:00Z"
}
```

### Get Financial Reports

```http
GET /v1/finance/reports/{ticker}
Authorization: Bearer <token>
?year=2024&quarter=Q3
```

**Response:**
```json
{
  "ticker": "AAPL",
  "year": 2024,
  "quarter": "Q3",
  "reports": {
    "income_statement": {
      "revenue": 94.04,
      "cost_of_revenue": 50.32,
      "gross_profit": 43.72,
      "operating_income": 28.15,
      "net_income": 23.64
    },
    "balance_sheet": {
      "total_assets": 352.76,
      "total_liabilities": 258.55,
      "total_equity": 94.21
    }
  },
  "filing_date": "2025-06-28",
  "source": "SEC 10-Q"
}
```

---

## Analytics Endpoints

### Download Statistics

```http
GET /api/download/stats/summary
```

**Response:**
```json
{
  "total_downloads": 1250,
  "last_7_days": 45,
  "last_24_hours": 8,
  "by_platform": {
    "windows": 650,
    "macos": 420,
    "linux": 180
  }
}
```

### Usage Overview

```http
GET /api/analytics/overview
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_users": 150,
  "active_users_24h": 25,
  "today_queries": 450,
  "today_tokens": 125000,
  "total_queries": 15000,
  "total_tokens": 2500000,
  "avg_response_time": 3.2
}
```

### User Statistics

```http
GET /api/analytics/users
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "user_id": "abc123...",
    "email": "user@university.edu",
    "created_at": "2025-10-01T10:00:00Z",
    "last_active": "2025-10-12T15:30:00Z",
    "total_queries": 150,
    "total_tokens": 45000,
    "status": "active"
  }
]
```

---

## Download Tracking Endpoints

### Track Downloads

These endpoints track downloads and redirect to the actual files:

```http
GET /api/download/windows
GET /api/download/macos
GET /api/download/linux
```

**Response:** 302 Redirect to actual installer file

**Tracked Data:**
- Platform (windows/macos/linux)
- IP address
- User agent
- Referrer
- Timestamp

---

## Error Handling

### Standard Error Response

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "request_id": "trace_id_here",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `authentication_error` | 401 | Invalid or missing token |
| `permission_denied` | 403 | Insufficient permissions |
| `rate_limit_exceeded` | 429 | Too many requests |
| `validation_error` | 400 | Invalid request data |
| `not_found` | 404 | Resource not found |
| `internal_server_error` | 500 | Server error |

### Rate Limiting

Rate limits are applied per user tier:

| Tier | Requests/Hour | Burst Limit |
|------|---------------|-------------|
| Free | 100 | 20/min |
| Pro | 1,000 | 60/min |
| Enterprise | 5,000 | 200/min |

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
X-Usage-Today: 150
```

---

## SDKs and Libraries

### Python

```python
import asyncio
from cite_agent import EnhancedNocturnalAgent, ChatRequest

async def main():
    agent = EnhancedNocturnalAgent()
    await agent.initialize()
    
    request = ChatRequest(
        question="Find papers on AI in healthcare",
        user_id="user123"
    )
    
    response = await agent.process_request(request)
    print(response.response)
    
    await agent.close()

asyncio.run(main())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://cite-agent-api-720dfadd602c.herokuapp.com',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Search papers
const searchPapers = async (query) => {
  const response = await client.post('/api/search', {
    query: query,
    limit: 10
  });
  return response.data;
};

// Get financial data
const getFinancialData = async (ticker, metric) => {
  const response = await client.get(`/v1/finance/calc/${ticker}/${metric}`);
  return response.data;
};
```

### cURL Examples

```bash
# Register user
curl -X POST https://cite-agent-api-720dfadd602c.herokuapp.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@university.edu", "password": "password123"}'

# Search papers
curl -X POST https://cite-agent-api-720dfadd602c.herokuapp.com/api/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning healthcare", "limit": 5}'

# Get financial data
curl -X GET https://cite-agent-api-720dfadd602c.herokuapp.com/v1/finance/calc/AAPL/revenue \
  -H "Authorization: Bearer <token>"
```

---

## Changelog

### v1.0.5 (Current)
- Fixed CLI initialization bugs
- Improved session handling
- Set temperature to 0.2 for better accuracy
- Added comprehensive error handling
- Enhanced download tracking

### v1.0.4
- Initial public release
- Basic research and finance capabilities
- JWT authentication
- Rate limiting

---

## Support

- **Documentation**: [Full docs](https://docs.cite-agent.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/cite-agent/issues)
- **Email**: api-support@cite-agent.com
- **Status Page**: [status.cite-agent.com](https://status.cite-agent.com)