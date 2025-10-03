# 🔧 Script Consolidation Guide

All scattered scripts have been consolidated into **`manage.py`** - a unified CLI tool.

## ✅ New Unified Interface

```bash
# Cleanup
./manage.py cleanup              # Clean all (venv, cache, artifacts)
./manage.py cleanup cache        # Clean only Python cache

# Setup
./manage.py setup dev            # Minimal install (1.3GB)
./manage.py setup dev --type dev # Dev install (1.6GB)
./manage.py setup dev --type full # Full install with ML (7.8GB)
./manage.py setup env            # Create .env from template

# Testing
./manage.py test api             # Run pytest
./manage.py test api --coverage  # Run with coverage
./manage.py test stress          # Run stress tests
./manage.py test smoke           # Run smoke tests

# Server
./manage.py server start         # Start production server
./manage.py server start --reload # Start with auto-reload
./manage.py server start --port 3000 # Custom port
./manage.py server stop          # Stop running server

# Utilities
./manage.py status               # Repository status
./manage.py security             # Security audit
```

---

## 🗑️ Deprecated Scripts (Can Be Removed)

### Root Directory
- ❌ `cleanup_repository.sh` → Use `./manage.py cleanup`
- ❌ `optimize_git_history.sh` → Keep (specialized operation)
- ❌ `install.py` → Use `./manage.py setup dev`
- ❌ `install_simple.py` → Use `./manage.py setup dev`
- ❌ `FIX_AND_DEMO.py` → Remove (one-time fix)
- ❌ `SIMPLE_DEMO.py` → Remove (archived demo)
- ❌ `stress_test_diverse_tickers.py` → Keep but called via `./manage.py test stress`

### scripts/ Directory
- ❌ `backup_env.py` → Integrated into `./manage.py setup env`
- ❌ `smoke_test.py` → Use `./manage.py test smoke`
- ❌ `security_audit.py` → Use `./manage.py security`

### nocturnal-archive-api/scripts/
These can remain for now (specialized operations):
- ✅ `alpha_audit.sh` - Advanced auditing
- ✅ `backup_dr.sh` - Disaster recovery
- ✅ `check_logs_secrets.sh` - Security checks
- ✅ `check_sources.py` - Data source validation
- ✅ `demo.sh` - Live demo
- ✅ `deploy_production.sh` - Production deployment
- ✅ `keys_rotate.sh` - Key rotation
- ✅ `prime_cache.sh` - Cache warming
- ✅ `production_smoke.sh` - Production smoke tests
- ✅ `red_team_smoke.sh` - Security testing
- ❌ `run_notebooks_ci.sh` - Remove (not using notebooks in CI)
- ✅ `smoke_finance.sh` - Finance API smoke tests
- ✅ `test_edgar_reality.py` - SEC EDGAR validation
- ✅ `validate_production.sh` - Production validation

### unified-platform/ Scripts
All can be removed if unified-platform is deprecated:
- ❌ All `deploy_*.sh` scripts
- ❌ All `setup_*.sh` scripts
- ❌ All `install_*.sh` scripts

---

## 📦 Migration Commands

### Before (scattered)
```bash
# Cleanup
./cleanup_repository.sh

# Setup
python3 install.py
python3 install_simple.py

# Test
cd nocturnal-archive-api && pytest
python3 stress_test_diverse_tickers.py
python3 scripts/smoke_test.py

# Security
python3 scripts/security_audit.py
```

### After (unified)
```bash
# Cleanup
./manage.py cleanup

# Setup
./manage.py setup dev --type dev

# Test
./manage.py test api
./manage.py test stress
./manage.py test smoke

# Security
./manage.py security
```

---

## 🎯 Benefits

1. **Single Entry Point** - One command for everything
2. **Consistent Interface** - All commands follow same pattern
3. **Better Help** - Built-in help and examples
4. **Error Handling** - Proper error messages
5. **Cross-Platform** - Pure Python (works on Windows/Mac/Linux)
6. **Extensible** - Easy to add new commands

---

## 🚀 Quick Start

```bash
# First time setup
./manage.py cleanup              # Clean old artifacts
./manage.py setup dev --type dev # Set up development environment
./manage.py setup env            # Create .env file
./manage.py test api             # Run tests
./manage.py server start --reload # Start dev server

# Daily development
./manage.py server start --reload # Start server
./manage.py test api --coverage   # Test changes
./manage.py cleanup cache         # Clean cache

# Before committing
./manage.py test api --coverage   # Ensure tests pass
./manage.py security              # Check for security issues
./manage.py status                # Check repository status
```

---

## 📋 Next Steps

1. Test the new `manage.py` interface
2. Update README.md to reference `manage.py`
3. Remove deprecated scripts (see commands below)
4. Update CI/CD to use `manage.py`

---

## 🗑️ Cleanup Commands

To remove deprecated scripts:

```bash
# Remove root-level deprecated scripts
rm -f install.py install_simple.py FIX_AND_DEMO.py SIMPLE_DEMO.py cleanup_repository.sh

# Remove deprecated utility scripts
rm -f scripts/backup_env.py scripts/smoke_test.py

# Remove unified-platform if not used
# rm -rf unified-platform

# Keep these for now
# - optimize_git_history.sh (specialized)
# - stress_test_diverse_tickers.py (called by manage.py)
# - nocturnal-archive-api/scripts/* (production operations)
```
