# Nocturnal Archive API

API-first backend for academic research. Find, format, and synthesize academic papers from trusted sources.

## Features

- **Search** academic papers from OpenAlex, PubMed, arXiv
- **Format** citations in BibTeX, APA, MLA, Chicago, Harvard styles
- **Synthesize** research findings using LLMs
- **No hallucinations** - only real papers with verified metadata

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nocturnal-archive-api.git
cd nocturnal-archive-api

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=sk-your-key-here
# OPENALEX_API_KEY=your-key-here
```

### Running the API

```bash
# Development
python -m uvicorn src.main:app --reload

# Production
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## API Endpoints

### Search Papers
```bash
POST /api/search
{
  "query": "CRISPR base editing efficiency",
  "limit": 10,
  "sources": ["openalex"]
}
```

### Format Citations
```bash
POST /api/format
{
  "paper_ids": ["W2981234567"],
  "style": "bibtex"
}
```

### Synthesize Research
```bash
POST /api/synthesize
{
  "paper_ids": ["W2981234567", "W2981234568"],
  "max_words": 300,
  "focus": "key_findings"
}
```

### Health Check
```bash
GET /api/health
```

## Development

### Project Structure

```
src/
├── main.py              # FastAPI app entrypoint
├── config/
│   └── settings.py      # Environment configuration
├── routes/
│   ├── search.py        # /api/search endpoint
│   ├── format.py        # /api/format endpoint
│   ├── synthesize.py    # /api/synthesize endpoint
│   └── health.py        # /api/health endpoint
├── services/
│   ├── paper_search.py  # OpenAlex integration
│   ├── citation_formatter.py # Citation formatting
│   └── synthesizer.py   # LLM synthesis
├── models/
│   ├── paper.py         # Paper data models
│   ├── request.py       # Request models
│   └── response.py      # Response models
├── middleware/
│   ├── rate_limit.py    # Rate limiting
│   └── tracing.py       # Request tracing
└── utils/
    └── logger.py        # Structured logging
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_search.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main

### Docker

```bash
# Build image
docker build -t nocturnal-archive-api .

# Run container
docker run -p 8000:8000 --env-file .env nocturnal-archive-api
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for synthesis | Yes |
| `OPENALEX_API_KEY` | OpenAlex API key for search | No |
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `REDIS_URL` | Redis connection URL | No |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |
| `ENVIRONMENT` | Environment (development/staging/production) | No |
| `LOG_LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR) | No |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
