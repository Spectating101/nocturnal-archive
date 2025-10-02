# 🚀 NOCTURNAL ARCHIVE - QUICK START GUIDE

## Installation (5 minutes)

```bash
# 1. Clone and enter directory
cd Nocturnal-Archive

# 2. Run simple installer
python3 install_simple.py

# 3. Or manual install
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e .
```

## Configuration (2 minutes)

```bash
# 1. Copy environment template
cp .env.production.example .env.local

# 2. Add your API keys
nano .env.local

# Required:
GROQ_API_KEY=your-groq-key-here
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Optional:
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
```

## Run the System (1 minute)

### Start the AI Agent
```bash
# Interactive mode
nocturnal

# Single query
nocturnal "What is AAPL's Q4 revenue?"
```

### Start the API
```bash
cd nocturnal-archive-api
uvicorn src.main:app --reload
```

### Test it works
```bash
# Health check
curl http://localhost:8000/health

# Get financial data
curl http://localhost:8000/v1/finance/calc/AAPL/revenue
```

## Key Commands

```bash
# Setup
nocturnal --setup        # Interactive setup wizard
nocturnal --version      # Check version

# Development
pytest tests/ -v         # Run tests
black .                  # Format code
mypy .                   # Type check

# Deployment
docker-compose up        # Run with Docker
gunicorn src.main:app    # Production server
```

## Common Issues

### "No module named 'structlog'"
```bash
pip install -r nocturnal-archive-api/requirements.txt
```

### "SECRET_KEY not set"
```bash
export JWT_SECRET_KEY="your-secret-here"
```

### Tests failing
```bash
cd nocturnal-archive-api
PYTHONPATH=. pytest tests/
```

## Next Steps

1. Read `PRODUCTION_READY_STATUS.md` for full details
2. Check `COMPREHENSIVE_SYSTEM_DOCUMENTATION.md` for architecture
3. Review `nocturnal-archive-api/README.md` for API docs

## Support

- **Issues**: Check logs in `nocturnal-archive-api/api.log`
- **Debug**: Set `LOG_LEVEL=DEBUG` in environment
- **Help**: Run `nocturnal --help`

---

**Ready in under 10 minutes!** 🎉
