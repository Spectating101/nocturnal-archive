# Nocturnal Archive

**API-first backend for academic research** - Find, format, and synthesize academic papers from trusted sources.

## 🎯 What is Nocturnal Archive?

Nocturnal Archive is a **production-ready API** that provides clean endpoints for academic research workflows. It's designed for developers building AI research assistants, academic tools, and research automation systems.

### Core Features

- **🔍 Search** academic papers from OpenAlex, PubMed, arXiv
- **📝 Format** citations in BibTeX, APA, MLA, Chicago, Harvard styles  
- **🧠 Synthesize** research findings using LLMs
- **✅ No hallucinations** - only real papers with verified metadata

## 🚀 Quick Start

### 1. Get the API

```bash
# Clone the repository
git clone https://github.com/Spectating101/nocturnal-archive.git
cd nocturnal-archive/nocturnal-archive-api

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your API keys
```

### 2. Run the API

```bash
# Development
python -m uvicorn src.main:app --reload

# Production
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 3. Use the API

Visit **http://localhost:8000/docs** for interactive API documentation.

## 📚 API Endpoints

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

## 🏗️ Architecture

```
nocturnal-archive-api/
├── src/
│   ├── main.py              # FastAPI application
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   ├── middleware/          # Rate limiting, tracing
│   └── config/              # Settings management
├── docker/                  # Containerization
├── docs/                    # API documentation
└── tests/                   # Test suite
```

## 🎯 Use Cases

### For Developers
- **AI Research Assistants** - Add academic search to your AI apps
- **Academic Tools** - Integrate with Zotero, Overleaf, Obsidian
- **Research Automation** - Build automated literature review systems
- **Content Generation** - Create research summaries and reports

### For Researchers
- **Literature Reviews** - Find and synthesize relevant papers
- **Citation Management** - Format citations in any style
- **Research Discovery** - Explore academic literature efficiently
- **Collaboration** - Share research findings with proper citations

## 🔧 Technology Stack

- **FastAPI** - Modern Python web framework
- **OpenAI GPT-3.5** - LLM synthesis and analysis
- **OpenAlex** - Academic paper database
- **PostgreSQL** - Data persistence
- **Redis** - Caching and rate limiting
- **Docker** - Containerization
- **Railway** - Deployment platform

## 📖 Documentation

- **[API Build Specification](API_BUILD_SPECIFICATION.md)** - Complete technical specification
- **[OpenAPI Specification](docs/api_spec.yaml)** - Machine-readable API docs
- **[Engine Extraction Guide](ENGINE_EXTRACTION_GUIDE.md)** - How to extract components for other projects
- **[API Documentation](nocturnal-archive-api/README.md)** - Detailed setup and usage guide

## 🚀 Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main

### Docker
```bash
docker-compose up -d
```

### Manual Deployment
```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for synthesis | Yes |
| `OPENALEX_API_KEY` | OpenAlex API key for search | No |
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `REDIS_URL` | Redis connection URL | No |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running the API
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

---

**Built for developers, by developers. No more chatbot complexity - just clean, reliable API endpoints for academic research.** 🎯