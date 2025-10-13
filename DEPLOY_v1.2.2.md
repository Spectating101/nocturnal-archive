# Deployment Guide - v1.2.2

## ✅ **COMMITTED AND READY TO DEPLOY**

**Commits:**
- `0b433e9` - v1.2.2 main release (workflow integration, Cerebras, UX polish)
- `db026d8` - Auto-updater package name fix

**Total Changes**: 24 files, 6,892 insertions

---

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Push to GitHub**
```bash
git push origin production-backend-only
```

This makes the code available for anyone to:
- Clone the repo
- Install from source: `pip install -e .`
- See the changes

---

### **Step 2: Deploy Backend to Heroku**
```bash
# This updates the live API with Cerebras support
git push heroku production-backend-only:main

# Restart dynos to apply changes
heroku restart -a cite-agent-api
```

**What this deploys:**
- `cite-agent-api/src/routes/query.py` - Cerebras priority + api_context support
- Enables production users to get real paper data in responses

---

### **Step 3: Publish to PyPI** (Optional - can wait)
```bash
# Update version if desired
# vim setup.py  # Change to 1.3.0 if you want

# Build distribution
python3 setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/cite_agent-1.2.2*

# Or upload to Test PyPI first:
twine upload --repository testpypi dist/cite_agent-1.2.2*
```

**After PyPI publish:**
- Users can: `pip install --upgrade cite-agent`
- Auto-updater will detect new version on next launch
- Shows: "New version available, run cite-agent --update"

---

## ✅ **WHAT WORKS AFTER DEPLOYMENT**

### **For Users (After GitHub Push):**
```bash
# Install from GitHub
pip install git+https://github.com/Spectating101/nocturnal-archive.git@production-backend-only
```

### **For Users (After PyPI Publish):**
```bash
# Install from PyPI
pip install cite-agent

# Auto-updates when you publish new versions
cite-agent --update
```

---

## ⚠️ **KNOWN ISSUES**

### **FinSight Financial API**

**Status**: ❌ **Not Working in Production**

**Problem**: 
```
curl "https://cite-agent-api.../v1/finance/calc/TSLA/revenue" \
  -H "Authorization: Bearer <jwt_token>"
  
# Returns: {"error": "Invalid API key"}
```

**Root Cause**: FinSight endpoints expect `X-API-Key` header, not JWT Bearer tokens

**Workaround Options:**

1. **Add JWT support to FinSight middleware** (recommended):
   ```python
   # cite-agent-api/src/middleware/api_auth.py
   # Accept both X-API-Key AND Authorization: Bearer
   ```

2. **Use demo key for authenticated users**:
   ```python
   # Client sends:
   headers = {"X-API-Key": "demo-key-123"}  # Instead of JWT
   ```

3. **Mark as "Coming Soon"** in docs until fixed

**Current State**: Backend LLM hallucinates financial data instead of getting real SEC filings

---

## 📊 **AUTO-UPDATER STATUS**

✅ **WORKS** (after my fix)

**How it works:**
1. On launch, checks PyPI for `cite-agent` package
2. Compares local version (1.2.2) vs PyPI latest
3. If newer version exists, shows notification
4. User runs: `cite-agent --update`
5. Auto-installs from PyPI

**Before my fix**: ❌ Was checking "nocturnal-archive" (wrong package)
**After my fix**: ✅ Checks "cite-agent" (correct)

---

## 🎯 **DEPLOYMENT PRIORITY**

### **Must Do Now:**
1. ✅ Commit done (0b433e9 + db026d8)
2. ⏳ Push to GitHub origin
3. ⏳ Push to Heroku (for backend Cerebras)

### **Should Do Soon:**
4. Fix FinSight JWT auth
5. Publish to PyPI as v1.3.0
6. Update README/docs

### **Can Wait:**
7. Browser extensions
8. Zotero plugin

---

## 🏆 **WHAT USERS GET (After Heroku Deploy)**

✅ Academic paper search with real DOIs
✅ Conversational workflow ("show library")
✅ Automatic history tracking  
✅ Proactive AI suggestions
✅ Backend uses Cerebras (14.4K RPD)
✅ Fact-checking with citations
✅ Auto-update notifications
❌ Financial data (FinSight broken)

**Rating**: **8/10** - Production ready for academic use

---

## 💡 **NEXT COMMANDS TO RUN:**

```bash
# 1. Push to GitHub
git push origin production-backend-only

# 2. Deploy to Heroku
git push heroku production-backend-only:main
heroku restart -a cite-agent-api

# 3. Test production
cite-agent "Find papers on transformers"
# Should return real papers!

# 4. (Optional) Publish to PyPI
python3 setup.py sdist bdist_wheel
twine upload dist/cite_agent-1.2.2*
```

---

**TL;DR**: 
- ✅ Code committed locally
- ✅ Auto-updater works (fixed package name)
- ⏳ Need to push to GitHub + Heroku
- ⚠️ FinSight needs JWT auth support (backend issue)

