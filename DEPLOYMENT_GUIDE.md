# Cite-Agent Deployment Guide

## 📊 Current State Analysis

### ⚠️ CRITICAL: Mixed Architecture Detected

The codebase has **TWO different auth systems** that need to be reconciled:

#### System A: "Control Plane" (account_client.py)
- User provides email/password
- Backend provisions API keys to user
- User stores API key locally
- ❌ Problem: Defeats backend-only monetization

#### System B: "Backend-Only" (enhanced_ai_agent.py line 1247)
- Sets `self.api_keys = []` (ignores any local keys)
- Forces all calls through backend
- ✅ Correct for monetization

**Result:** Users see confusing setup asking for "Groq API key" but it's ignored anyway.

---

## ✅ What SHOULD Happen (Backend-Only Flow)

### User Experience:
```
1. User: pip install cite-agent
2. User: cite-agent
3. CLI: "First time? Let's sign you up!"
4. CLI: "Email: ___"
5. User: student@university.edu
6. CLI: "Password: ___"
7. User: [creates password]
8. CLI: "Registered! $10/month for 50k tokens/day"
9. CLI saves JWT token to ~/.nocturnal_archive/session.json
10. User: "What is a p-value?"
11. CLI → Backend API (with JWT)
12. Backend → Groq (with YOUR keys)
13. CLI ← Response
```

**User NEVER sees:**
- Groq API key prompts
- Cerebras API key prompts
- Any mention of API keys

**They only see:**
- Email/password signup
- Usage ($10/month, 50k tokens/day)
- Their queries + answers

---

## 🔧 What Needs Fixing

### Fix 1: Remove API key prompts from setup_config.py
```python
# REMOVE these from MANAGED_SECRETS:
"GROQ_API_KEY": {...}  # Users don't need this
"OPENALEX_API_KEY": {...}  # Optional, can stay
```

### Fix 2: Simplify account_client.py
```python
# Change AccountCredentials to NOT include api_key
@dataclass
class AccountCredentials:
    account_id: str
    email: str
    auth_token: str  # JWT for backend auth
    # REMOVED: api_key (backend has the keys, not user)
```

### Fix 3: Update setup flow
```
OLD: "Enter your Groq API key"
NEW: "Create an account (email/password)"
```

---

## 📊 Monitoring & Admin (What YOU See)

### Backend Tracking (cite-agent-api/src/routes/query.py)

**Database schema (migrations/002_accuracy_tracking.sql):**
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    created_at TIMESTAMP,
    tokens_used_today INTEGER,
    last_token_reset DATE
);

CREATE TABLE queries (
    query_id TEXT PRIMARY KEY,
    user_id TEXT,
    query_text TEXT,
    response_text TEXT,
    tokens_used INTEGER,
    timestamp TIMESTAMP,
    model TEXT
);
```

**Admin endpoints you'll need to add:**
```python
@router.get("/admin/users")
async def list_users():
    """See all users + usage"""

@router.get("/admin/usage/{user_id}")
async def get_user_usage(user_id: str):
    """Detailed usage for one user"""

@router.get("/admin/stats")
async def get_stats():
    """Total queries/day, revenue, etc."""
```

---

## 🚀 Deployment Checklist

### Pre-Deploy:
- [ ] Fix setup_config.py (remove Groq API key prompt)
- [ ] Fix account_client.py (remove api_key from credentials)
- [ ] Add admin routes to backend
- [ ] Set environment variables on Heroku

### Heroku Environment Variables:
```bash
JWT_SECRET_KEY=<generate-random-32-bytes>
GROQ_API_KEY_1=gsk_...
GROQ_API_KEY_2=gsk_...
GROQ_API_KEY_3=gsk_...
CEREBRAS_API_KEY=csk_...
DATABASE_URL=<heroku-provides-this>
```

### Deploy:
```bash
git push heroku production-backend-only:main
heroku run python cite-agent-api/migrations/001_initial_schema.sql
heroku run python cite-agent-api/migrations/002_accuracy_tracking.sql
```

### Post-Deploy Test:
```bash
pip install cite-agent
cite-agent
# Go through signup
# Ask: "What is 2+2?"
# Verify: Works + usage tracked
```

---

## ❓ Your Questions Answered

**Q: How does it look to the user?**
**A:** Clean signup (email/password), then chat. NO API key hassle.

**Q: How do we monitor usage?**
**A:** Backend logs every query to PostgreSQL. Add admin dashboard.

**Q: Is backend REALLY required?**
**A:** YES. Client has `self.api_keys = []` + `self.client = None`

**Q: Can we deploy now?**
**A:** Almost. Fix setup prompts first (10 min), then deploy.

---

## 🎯 Next Steps

1. Fix setup_config.py (remove API key prompt)
2. Add admin routes (optional, can add later)
3. Deploy to Heroku
4. Test as real user
5. Open beta

Want me to make those fixes now?
