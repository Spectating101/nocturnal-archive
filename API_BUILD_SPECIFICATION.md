# 📘 Nocturnal Archive — API Build Specification

## **1. Purpose & Vision**

Nocturnal Archive is an **API-first backend** for academic research that provides clean, reliable endpoints for finding, formatting, and synthesizing academic papers. 

**Core Philosophy:**
- **No hallucinations** - Only real papers with verified metadata
- **API-first** - Designed for developers, not end users
- **Trusted sources** - OpenAlex, PubMed, arXiv (no scraping)
- **Simple contracts** - Predictable request/response patterns

**Target Use Cases:**
- AI research assistants
- Academic workflow tools (Zotero, Overleaf integrations)
- Research note-taking apps
- Internal research team pipelines

---

## **2. API Design**

### **Endpoint 1: `/api/search`**
**Purpose:** Find academic papers from trusted sources

**Request:**
```json
POST /api/search
{
  "query": "CRISPR base editing efficiency",
  "limit": 10,
  "sources": ["openalex"],
  "filters": {
    "year_min": 2020,
    "open_access": true
  }
}
```

**Response:**
```json
{
  "papers": [
    {
      "id": "W2981234567",
      "title": "Improved CRISPR base editing efficiency in human cells",
      "authors": [
        {"name": "Smith, J.", "orcid": "0000-0000-0000-0000"},
        {"name": "Doe, A.", "orcid": "0000-0000-0000-0001"}
      ],
      "year": 2023,
      "doi": "10.1038/s41586-023-xxxxx",
      "abstract": "Recent advances in CRISPR base editing have shown...",
      "citations_count": 45,
      "open_access": true,
      "pdf_url": "https://www.nature.com/articles/s41586-023-xxxxx.pdf",
      "source": "openalex",
      "venue": "Nature",
      "keywords": ["CRISPR", "base editing", "gene therapy"]
    }
  ],
  "count": 10,
  "query_id": "q_123",
  "trace_id": "trace_456"
}
```

### **Endpoint 2: `/api/format`**
**Purpose:** Convert paper IDs into citation formats

**Request:**
```json
POST /api/format
{
  "paper_ids": ["W2981234567", "W2981234568"],
  "style": "bibtex",
  "options": {
    "include_abstract": false,
    "include_keywords": true
  }
}
```

**Response:**
```json
{
  "formatted": "@article{smith2023improved,\n  title={Improved CRISPR base editing efficiency in human cells},\n  author={Smith, J. and Doe, A.},\n  journal={Nature},\n  year={2023},\n  doi={10.1038/s41586-023-xxxxx}\n}",
  "format": "bibtex",
  "count": 1,
  "trace_id": "trace_789"
}
```

### **Endpoint 3: `/api/synthesize`**
**Purpose:** Summarize findings across selected papers

**Request:**
```json
POST /api/synthesize
{
  "paper_ids": ["W2981234567", "W2981234568"],
  "max_words": 300,
  "focus": "key_findings",
  "style": "academic"
}
```

**Response:**
```json
{
  "summary": "Recent advances in CRISPR base editing demonstrate significant improvements in efficiency and precision. Smith et al. (2023) report 95% editing efficiency in human cells, while Doe et al. (2023) show reduced off-target effects through novel guide RNA designs.",
  "key_findings": [
    "Efficiency improved to 95% in human cells [1]",
    "Off-target effects reduced by 80% [2]",
    "Novel guide RNA designs show promise [2]"
  ],
  "citations_used": {
    "[1]": "W2981234567",
    "[2]": "W2981234568"
  },
  "word_count": 287,
  "trace_id": "trace_101"
}
```

### **Endpoint 4: `/api/health`**
**Purpose:** System health and status

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "openalex": "ok",
    "openai": "ok",
    "database": "ok"
  },
  "version": "1.0.0"
}
```

---

## **3. Tech Stack**

### **Core Framework**
- **FastAPI** - Modern Python web framework with automatic OpenAPI docs
- **Pydantic** - Data validation and serialization
- **httpx** - Async HTTP client for external APIs

### **Data Sources**
- **OpenAlex** - Primary academic paper database
- **PubMed** - Medical literature (future)
- **arXiv** - Preprints (future)

### **LLM Integration**
- **OpenAI API** - GPT-3.5-turbo for synthesis (cost-effective)
- **Fallback support** - Anthropic Claude (future)

### **Storage & Caching**
- **PostgreSQL** - Via Supabase for metadata caching
- **Redis** - Optional result caching and rate limiting

### **Deployment**
- **Railway** - Primary deployment platform
- **Render** - Backup deployment option
- **Docker** - Containerization for consistency

### **Monitoring**
- **Sentry** - Error tracking and performance monitoring
- **Structured logging** - JSON logs for observability

---

## **4. Project Structure**

```
nocturnal-archive-api/
├── src/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment configuration
│   │   └── database.py         # Database connection
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── search.py           # /api/search endpoint
│   │   ├── format.py           # /api/format endpoint
│   │   ├── synthesize.py       # /api/synthesize endpoint
│   │   └── health.py           # /api/health endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── paper_search.py     # OpenAlex integration
│   │   ├── citation_formatter.py # Citation formatting
│   │   ├── synthesizer.py      # LLM synthesis
│   │   └── cache.py            # Redis caching
│   ├── models/
│   │   ├── __init__.py
│   │   ├── paper.py            # Paper data models
│   │   ├── request.py          # Request models
│   │   └── response.py         # Response models
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limit.py       # Rate limiting
│   │   ├── tracing.py          # Request tracing
│   │   └── error_handler.py    # Error handling
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Structured logging
│       └── validators.py       # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_search.py
│   ├── test_format.py
│   ├── test_synthesize.py
│   └── conftest.py
├── docs/
│   ├── api_spec.yaml           # OpenAPI specification
│   └── README.md
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## **5. Development Plan**

### **Week 1 — MVP Core**
- [ ] **Day 1-2:** Project setup and basic FastAPI structure
- [ ] **Day 3-4:** Implement `PaperSearcher` service with OpenAlex
- [ ] **Day 5:** Build `/api/search` endpoint
- [ ] **Day 6:** Implement `CitationFormatter` with BibTeX
- [ ] **Day 7:** Build `/api/format` endpoint

### **Week 2 — Synthesis & Polish**
- [ ] **Day 8-9:** Implement `Synthesizer` with OpenAI integration
- [ ] **Day 10:** Build `/api/synthesize` endpoint
- [ ] **Day 11:** Add `/api/health` endpoint
- [ ] **Day 12:** Implement caching and rate limiting
- [ ] **Day 13:** Add comprehensive error handling
- [ ] **Day 14:** Deploy to Railway and test

### **Week 3 — Documentation & Launch**
- [ ] **Day 15-16:** Write comprehensive API documentation
- [ ] **Day 17:** Create landing page with API key signup
- [ ] **Day 18:** Add monitoring and alerting
- [ ] **Day 19:** Performance testing and optimization
- [ ] **Day 20:** Launch and announce

---

## **6. Implementation Details**

### **PaperSearcher Service**
```python
class PaperSearcher:
    def __init__(self, openalex_api_key: str):
        self.client = httpx.AsyncClient()
        self.api_key = openalex_api_key
    
    async def search_papers(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Paper]:
        # OpenAlex API integration
        # Input validation and sanitization
        # Result formatting and deduplication
```

### **CitationFormatter Service**
```python
class CitationFormatter:
    def __init__(self):
        self.formatters = {
            'bibtex': self._format_bibtex,
            'apa': self._format_apa,
            'mla': self._format_mla
        }
    
    async def format_papers(
        self, 
        paper_ids: List[str], 
        style: str
    ) -> str:
        # Fetch paper metadata
        # Apply formatting rules
        # Return formatted citations
```

### **Synthesizer Service**
```python
class Synthesizer:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    async def synthesize_papers(
        self, 
        paper_ids: List[str], 
        max_words: int = 300
    ) -> SynthesisResult:
        # Fetch paper abstracts
        # Construct synthesis prompt
        # Call OpenAI API
        # Parse and format response
```

---

## **7. Security & Rate Limiting**

### **API Key Authentication**
- Simple API key system for initial launch
- Rate limiting: 100 requests/hour for free tier
- 1000 requests/hour for paid tier

### **Input Validation**
- Strict input validation on all endpoints
- SQL injection protection
- XSS prevention
- Rate limiting per IP and API key

### **Error Handling**
- Structured error responses
- No sensitive information in error messages
- Comprehensive logging for debugging

---

## **8. Deployment Configuration**

### **Environment Variables**
```bash
# API Keys
OPENAI_API_KEY=sk-...
OPENALEX_API_KEY=...
SUPABASE_URL=https://...
SUPABASE_KEY=...
REDIS_URL=redis://...

# App Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
RATE_LIMIT_PER_HOUR=100
```

### **Railway Deployment**
```yaml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/health"
```

---

## **9. Success Metrics**

### **Technical Metrics**
- [ ] API response time < 2 seconds
- [ ] 99.9% uptime
- [ ] Zero data hallucinations
- [ ] Comprehensive test coverage (>80%)

### **Business Metrics**
- [ ] 10 developer signups in first month
- [ ] 1,000 API calls in first month
- [ ] At least 1 integration (Zotero/Overleaf)
- [ ] Positive developer feedback

---

## **10. Future Roadmap**

### **Phase 2 (Month 2-3)**
- Add PubMed and arXiv sources
- Implement more citation styles (APA, MLA, Chicago)
- Add paper clustering and similarity search
- Build webhook system for real-time updates

### **Phase 3 (Month 4-6)**
- Advanced synthesis with custom prompts
- PDF parsing and full-text analysis
- Research trend analysis
- Team collaboration features

### **Phase 4 (Month 7-12)**
- AI-powered research recommendations
- Integration marketplace
- Enterprise features and SSO
- Mobile SDKs

---

## **11. Constraints & Limitations**

### **What We're NOT Building (Yet)**
- ❌ Full session management
- ❌ User authentication beyond API keys
- ❌ PDF parsing and full-text search
- ❌ Google Scholar scraping (legal gray area)
- ❌ Advanced billing and subscription management
- ❌ Real-time collaboration features

### **Technical Constraints**
- Keep it simple and focused
- Prioritize reliability over features
- Use proven, stable technologies
- Maintain clear API contracts

---

This specification provides a complete blueprint for building a production-ready academic research API. The modular design allows for incremental development while maintaining high quality and reliability standards.
