# 🚀 Optimized Setup Guide - Nocturnal Archive

**Goal:** Keep repository under 500MB (from 8.7GB!)

## 📊 Size Optimization Summary

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Virtual Environments | 8.1GB | 0MB* | 100% |
| Git History | 566MB | ~100MB | 82% |
| Cache Files | 20MB | 0MB | 100% |
| **Total** | **8.7GB** | **<500MB** | **94%** |

*Virtual environments are now created on-demand per machine

---

## 🎯 Quick Start (Optimized)

### 1. Clone & Cleanup (First Time)

```bash
# Clone repository
git clone <your-repo-url>
cd Nocturnal-Archive

# Run cleanup script (removes bloat)
chmod +x cleanup_repository.sh
./cleanup_repository.sh

# Optional: Optimize git history (advanced users)
chmod +x optimize_git_history.sh
./optimize_git_history.sh
```

### 2. Set Up Virtual Environment

```bash
cd nocturnal-archive-api

# Create fresh virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Choose your installation option:
```

#### Option A: Minimal Install (RECOMMENDED) - ~1.3GB
Perfect for production and most development work.

```bash
pip install -r requirements.txt
```

**Includes:**
- FastAPI + Uvicorn
- SEC EDGAR integration
- Yahoo Finance, Alpha Vantage
- Database (PostgreSQL, Redis)
- Basic monitoring

**Excludes:**
- PyTorch/CUDA (7GB!)
- FinGPT sentiment analysis
- Development tools

#### Option B: Development Install - ~1.6GB
For active development with testing tools.

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**Additional features:**
- pytest + coverage
- black + flake8 (linting)
- mypy (type checking)

#### Option C: Full ML Install - ~7.8GB
Only if you need FinGPT sentiment analysis features.

```bash
pip install -r requirements.txt -r requirements-ml.txt
```

**Additional features:**
- PyTorch + CUDA
- Transformers (Hugging Face)
- sentence-transformers
- FinGPT models

⚠️ **Warning:** This increases venv to 7.8GB! Only use if you need ML features.

---

## 🔧 Configuration

### Environment Variables

```bash
# Copy example environment file
cp env.example .env

# Edit with your API keys
nano .env
```

Required keys:
- `NOCTURNAL_KEY` - API authentication
- `GROQ_API_KEY` - LLM synthesis (or use OpenAI)
- `OPENAI_API_KEY` - Alternative LLM

Optional:
- `ALPHA_VANTAGE_API_KEY` - Stock data
- `DATABASE_URL` - PostgreSQL (defaults to SQLite)
- `REDIS_URL` - Caching (optional, uses in-memory fallback)

---

## 🚀 Running the API

```bash
# Development (with auto-reload)
uvicorn src.main:app --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

---

## 🧪 Testing

```bash
# Install dev dependencies first (if not already)
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

---

## 📦 What Gets Excluded from Git

The updated `.gitignore` prevents these from being committed:

### Large Files
- ✅ Virtual environments (`.venv/`, `**/.venv/`)
- ✅ Python cache (`__pycache__/`, `*.pyc`)
- ✅ Test coverage (`htmlcov/`, `.coverage`)
- ✅ Large data files (`*.parquet`, `*.h5`)
- ✅ ML model weights (`*.pt`, `*.pth`)
- ✅ Stress test results (`stress_test_results.json`)

### Sensitive Files
- ✅ Environment files (`.env`, `.env.local`, `.env.production`)
- ✅ Database files (`*.db`, `*.sqlite`)
- ✅ Credentials (`deployment/credentials.md`)

---

## 🔄 Maintenance

### Regular Cleanup (Run Monthly)

```bash
# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Clean test artifacts
rm -rf htmlcov .coverage .pytest_cache

# Regenerate virtual environment if needed
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Git History Optimization

Only needed if repository grows > 200MB:

```bash
./optimize_git_history.sh
```

⚠️ **Warning:** This rewrites git history! Coordinate with team first.

---

## 🎯 Best Practices

### For Developers
1. **Never commit `.venv/`** - Use `.gitignore` (already configured)
2. **Use minimal install** - Only install ML deps if needed
3. **Clean cache regularly** - Run cleanup monthly
4. **Keep data out of repo** - Use external storage for large datasets

### For CI/CD
```yaml
# GitHub Actions example
- name: Install dependencies (minimal)
  run: |
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
```

### For Docker
```dockerfile
# Use slim Python image
FROM python:3.11-slim

# Install only minimal requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Don't include ML dependencies in production
```

---

## 📚 Dependency Management

### Core Requirements (`requirements.txt`)
- **Size:** ~1.3GB installed
- **Purpose:** Production runtime
- **Update frequency:** As needed

### Dev Requirements (`requirements-dev.txt`)
- **Size:** ~300MB additional
- **Purpose:** Testing, linting, type checking
- **Update frequency:** Monthly

### ML Requirements (`requirements-ml.txt`)
- **Size:** ~6.5GB additional
- **Purpose:** FinGPT sentiment, RAG features
- **Update frequency:** Quarterly
- **Usage:** Feature-flagged (`ENABLE_RAG=true`)

---

## 🚨 Troubleshooting

### Issue: "Repository still large after cleanup"
```bash
# Check what's using space
du -sh .[!.]* * | sort -hr | head -20

# Force remove large files
git filter-repo --path-glob '**/*.parquet' --invert-paths --force
git gc --prune=now --aggressive
```

### Issue: "Import errors after cleanup"
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Tests failing with ML dependencies"
```bash
# Either install ML deps or disable ML tests
export ENABLE_RAG=false
pytest -k "not ml and not rag"
```

---

## 📈 Monitoring Repository Size

```bash
# Check total size
du -sh .

# Check components
du -sh .git .venv nocturnal-archive-api/.venv data

# Alert if over 500MB
SIZE=$(du -sm . | cut -f1)
if [ $SIZE -gt 500 ]; then
    echo "⚠️  Repository over 500MB! Run cleanup."
fi
```

---

## 🎉 Success Criteria

✅ Repository < 500MB (excluding `.venv`)
✅ Fresh clone < 200MB
✅ `git clone` time < 30 seconds
✅ Minimal install < 5 minutes
✅ No large files in git history
✅ All tests passing with minimal deps

---

## 📞 Support

Questions about optimization?
- Check size: `du -sh .`
- Run cleanup: `./cleanup_repository.sh`
- Report issues: GitHub Issues

**Remember:** Virtual environments should be created per-machine, never committed to git! 🎯
