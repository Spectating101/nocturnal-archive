# Cite-Agent - Independent Action Plan

**Created**: October 9, 2025  
**Purpose**: Step-by-step plan you can execute independently while waiting for Heroku Student Pack approval

---

## 🎯 Current Status

✅ **Code**: 100% complete and tested  
✅ **Heroku App**: Created (`cite-agent-api`)  
✅ **Accuracy System**: Implemented (95-98% accuracy target)  
⏸️ **Waiting**: Student Pack approval (24 hours)  
🎯 **Goal**: Be ready to deploy in 15 minutes once approved

---

## 📋 Phase 1: While Waiting (Today - Next 24 Hours)

### Task 1.1: Verify API Keys ✓

**What**: Make sure all 6 API keys are working  
**Why**: Deployment will fail if keys are invalid  
**How**:

```bash
# Test Groq keys
curl -H "Authorization: Bearer gsk_YOUR_KEY_1" \
  https://api.groq.com/openai/v1/models

curl -H "Authorization: Bearer gsk_YOUR_KEY_2" \
  https://api.groq.com/openai/v1/models

curl -H "Authorization: Bearer gsk_YOUR_KEY_3" \
  https://api.groq.com/openai/v1/models

# Test Cerebras keys  
curl -H "Authorization: Bearer csk_YOUR_KEY_1" \
  https://api.cerebras.ai/v1/models

curl -H "Authorization: Bearer csk_YOUR_KEY_2" \
  https://api.cerebras.ai/v1/models

curl -H "Authorization: Bearer csk_YOUR_KEY_3" \
  https://api.cerebras.ai/v1/models
```

**Success**: Each curl returns a list of models  
**Failure**: Get new keys from respective platforms

---

### Task 1.2: Test Accuracy System (NEW) ✓

**What**: Verify citation verification works locally  
**Why**: Ensure 95-98% accuracy system is functional  
**How**:

```bash
cd /path/to/Cite-Agent

# Activate venv (if exists)
source venv/bin/activate || true

# Install dependencies (if needed)
pip install -q httpx structlog

# Run accuracy tests
python3 test_accuracy_system.py
```

**Success**: All tests pass  
**Failure**: Check error messages, fix issues

**What You'll See**:
```
✅ PASS - citation_verifier
✅ PASS - temperature  
✅ PASS - sql_migration
✅ PASS - accuracy_routes
✅ ALL TESTS PASSED - Ready for deployment!
```

**Files to Review**:
- `ACCURACY_IMPROVEMENTS.md` - Full implementation details
- `TRUTH_SEEKING_AUDIT.md` - Before/after analysis

---

### Task 1.3: Prepare Deployment Script

**What**: Create a deployment script with all your keys  
**Why**: Deploy in 1 command instead of 20  
**How**:

Create `cite-agent-api/deploy.sh`:

```bash
#!/bin/bash
# Cite-Agent Deployment Script

set -e

echo "🚀 Deploying Cite-Agent to Heroku..."

# Set environment variables
heroku config:set \
  JWT_SECRET_KEY=$(openssl rand -hex 32) \
  ENV=production \
  GROQ_API_KEY_1="gsk_YOUR_KEY_1" \
  GROQ_API_KEY_2="gsk_YOUR_KEY_2" \
  GROQ_API_KEY_3="gsk_YOUR_KEY_3" \
  CEREBRAS_API_KEY_1="csk_YOUR_KEY_1" \
  CEREBRAS_API_KEY_2="csk_YOUR_KEY_2" \
  CEREBRAS_API_KEY_3="csk_YOUR_KEY_3" \
  GITHUB_RELEASE_BASE="https://github.com/YOUR_USERNAME/cite-agent/releases/download" \
  VERSION="v1.0.0-beta" \
  --app cite-agent-api

echo "✅ Environment variables set"

# Deploy
echo "📦 Deploying code..."
git push heroku main

echo "✅ Code deployed"

# Run migrations
echo "🗄️  Running database migrations..."
heroku run python run_migrations.py --app cite-agent-api

echo "✅ Migrations complete"

# Test
echo "🧪 Testing deployment..."
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/health

echo ""
echo "🎉 Deployment complete!"
echo "Backend URL: https://cite-agent-api-720dfadd602c.herokuapp.com"
```

Make it executable:
```bash
chmod +x cite-agent-api/deploy.sh
```

---

### Task 1.3: Test Locally (Optional but Recommended)

**What**: Run backend locally to catch bugs before deployment  
**Why**: Faster iteration than deploying to Heroku  
**How**:

```bash
# 1. Set environment variables
cd cite-agent-api
cp env.template .env
# Edit .env with your actual keys

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Run backend
uvicorn src.main:app --reload --port 8000

# 4. In another terminal, test
curl http://localhost:8000/api/health

# 5. Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

**Success**: Health check returns `{"status": "healthy"}`, registration creates user  
**Skip if**: You trust the tests (they already passed)

---

### Task 1.4: Prepare Client for Backend URL

**What**: Update client to use Heroku URL instead of localhost  
**Why**: Users need to connect to deployed backend  
**How**:

Edit `cite_agent/enhanced_ai_agent.py` around line 1150:

```python
# Find this line:
backend_api_url = config.get("backend_api_url", "http://localhost:8000")

# Change to:
backend_api_url = config.get("backend_api_url", "https://cite-agent-api-720dfadd602c.herokuapp.com")
```

**Or** set environment variable (recommended):
```bash
export NOCTURNAL_API_URL="https://cite-agent-api-720dfadd602c.herokuapp.com"
```

---

### Task 1.5: Create GitHub Release (for download tracking)

**What**: Upload placeholder installers to GitHub Releases  
**Why**: Download URLs need to point somewhere  
**How**:

1. Go to https://github.com/YOUR_USERNAME/cite-agent/releases
2. Click "Draft a new release"
3. Tag: `v1.0.0-beta`
4. Title: "Cite-Agent Beta Launch"
5. Upload 3 placeholder files:
   - `cite-agent-windows.exe` (can be empty for now)
   - `cite-agent-macos.dmg` (can be empty for now)
   - `cite-agent-linux.tar.gz` (can be empty for now)
6. Click "Publish release"

**URLs will be**:
- Windows: `https://github.com/YOUR_USERNAME/cite-agent/releases/download/v1.0.0-beta/cite-agent-windows.exe`
- macOS: `https://github.com/YOUR_USERNAME/cite-agent/releases/download/v1.0.0-beta/cite-agent-macos.dmg`
- Linux: `https://github.com/YOUR_USERNAME/cite-agent/releases/download/v1.0.0-beta/cite-agent-linux.tar.gz`

---

## 📋 Phase 2: After Heroku Student Pack Approval (Day 2)

### Task 2.1: Deploy Backend ⚡ (15 minutes)

**What**: Deploy to Heroku  
**Why**: Make backend live  
**How**:

```bash
cd cite-agent-api

# Option A: Use the script you created
./deploy.sh

# Option B: Manual deployment
heroku config:set [... all environment variables ...]
git push heroku main

# IMPORTANT: Run BOTH migrations
heroku run python run_migrations.py --app cite-agent-api
# This runs:
#   - 001_initial_schema.sql (users, queries, sessions, downloads)
#   - 002_accuracy_tracking.sql (response_quality, citation_details, views)
```

**Success**: 
- Health check works: `curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/health`
- Returns: `{"status": "healthy", "timestamp": "...", "database": "connected"}`

**Troubleshooting**:
```bash
# View logs
heroku logs --tail --app cite-agent-api

# Check status
heroku ps --app cite-agent-api

# Restart if needed
heroku restart --app cite-agent-api
```

---

### Task 2.2: Test Accuracy Endpoints 📊 (5 minutes)

**What**: Verify accuracy system is working  
**Why**: Ensure citation verification is live  
**How**:

```bash
# Test accuracy stats
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/accuracy/stats

# Should return (may be empty if no queries yet):
{
  "unsupported_claim_rate": 0.0,
  "false_citation_rate": 0.0,
  "avg_quality_score": 0.0,
  "total_responses": 0,
  ...
}
```

**Success**: Endpoint returns JSON with accuracy metrics  
**Failure**: Check Heroku logs, ensure migration ran

---

### Task 2.3: Test End-to-End 🧪 (10 minutes)

**What**: Test full user flow  
**Why**: Make sure everything works together  
**How**:

```bash
# Test 1: Registration
curl -X POST https://cite-agent-api-720dfadd602c.herokuapp.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Save the token from response

# Test 2: Query (use token from Test 1)
curl -X POST https://cite-agent-api-720dfadd602c.herokuapp.com/api/query/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query": "What is 2+2?", "conversation_history": []}'

# Test 3: Analytics
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/stats

# Test 4: Download tracking
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/downloads/windows
```

**Success**: All 4 tests return valid responses

---

### Task 2.3: Test Client Locally 💻 (5 minutes)

**What**: Test client connects to deployed backend  
**Why**: Make sure user experience works  
**How**:

```bash
# Run the client
cd cite_agent
python3 cli.py

# Or if you have it installed
cite-agent

# Test:
# 1. Register with email/password
# 2. Ask a question
# 3. Verify you get a response
```

**Success**: Client connects, registers user, gets AI responses

---

## 📋 Phase 3: Beta Launch (Week 1)

### Task 3.1: Invite Beta Testers (Day 3)

**What**: Send invites to 10-20 people  
**Why**: Get real user feedback  
**How**:

Email template:
```
Subject: Cite-Agent Beta Access 🔍

Hi [Name],

You're invited to try Cite-Agent - an AI research assistant 
that's half the price of ChatGPT but just as powerful.

What you get:
• Access to 70B AI models
• 50 queries/day
• Terminal-based interface
• $10/month (first 3 months FREE for beta testers)

Download for your OS:
• Windows: https://cite-agent-api-720dfadd602c.herokuapp.com/api/downloads/windows
• macOS: https://cite-agent-api-720dfadd602c.herokuapp.com/api/downloads/macos
• Linux: https://cite-agent-api-720dfadd602c.herokuapp.com/api/downloads/linux

Just click, download, install, and open. Register with your email.

Let me know what you think!

Best,
[Your Name]
```

**Target**: 10-20 beta testers

---

### Task 3.2: Monitor Daily (Week 1)

**What**: Check logs and analytics every day  
**Why**: Catch issues early  
**How**:

```bash
# Morning routine (5 minutes)
heroku logs --tail --app cite-agent-api | grep ERROR
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/stats

# Look for:
# - Any error messages?
# - How many queries today?
# - Any rate limit hits?
# - Response time good?
```

**Success**: No critical errors, users are active

---

### Task 3.3: Gather Feedback (Week 1)

**What**: Ask beta users what they think  
**Why**: Improve product  
**How**:

Email them after 3 days:
```
Subject: Cite-Agent Feedback?

Hi [Name],

Quick check-in on Cite-Agent. Three questions:

1. What do you like most?
2. What's frustrating or confusing?
3. What feature would you pay extra for?

Thanks!
```

**Success**: Get 5-10 responses with actionable feedback

---

## 📋 Phase 4: Growth & Iteration (Month 1-3)

### Task 4.1: Weekly Metrics Review

**Every Monday**:
```bash
# Get usage stats
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/stats

# Get accuracy stats (NEW)
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/accuracy/stats

# Get accuracy trends (NEW)
curl https://cite-agent-api-720dfadd602c.herokuapp.com/api/analytics/accuracy/trends?days=7

# Check database
heroku pg:psql --app cite-agent-api
> SELECT COUNT(*) as total_users FROM users;
> SELECT COUNT(*) as active_today FROM queries 
  WHERE timestamp > NOW() - INTERVAL '1 day';
```

Track in spreadsheet:
- Total users
- Active users (last 7 days)
- Queries per user
- Revenue (users × $10)
- Churn rate
- **UCR (Unsupported Claim Rate)** - target: <2%
- **FCR (False Citation Rate)** - target: ~0%
- **Quality Score** - target: >0.9

---

### Task 4.2: Feature Prioritization

**Based on feedback, add**:
1. Most requested features first
2. Quick wins (easy + high impact)
3. Competitive differentiators

**Example priorities**:
- Week 2-3: Fix critical bugs
- Week 4-6: Add 1-2 requested features
- Week 7-12: Improve onboarding

---

### Task 4.3: Public Launch Prep (Month 3)

**When you have**:
- 20+ active beta users
- No critical bugs
- Positive feedback

**Then**:
1. Create landing page (optional)
2. Announce on Twitter/Reddit/HN
3. Submit to Product Hunt
4. Write blog post

---

## 🎯 Decision Tree: What to Do When

### Scenario 1: "Heroku Student Pack approved!"

✅ **Action**: Run Phase 2 (deploy backend)  
⏱️ **Time**: 15 minutes  
📝 **Next**: Task 2.1

---

### Scenario 2: "I want to test before deploying"

✅ **Action**: Task 1.3 (test locally)  
⏱️ **Time**: 30 minutes  
📝 **Next**: Wait for approval, then Task 2.1

---

### Scenario 3: "Backend is deployed, now what?"

✅ **Action**: Task 2.2 (test end-to-end)  
⏱️ **Time**: 10 minutes  
📝 **Next**: Task 2.3 (test client)

---

### Scenario 4: "Everything works, ready to launch"

✅ **Action**: Task 3.1 (invite beta testers)  
⏱️ **Time**: 1 hour  
📝 **Next**: Task 3.2 (monitor daily)

---

### Scenario 5: "I found a bug!"

✅ **Action**: 
1. Check logs: `heroku logs --tail --app cite-agent-api`
2. Fix in code
3. Deploy: `git push heroku main`
4. Test: `curl https://cite-agent-api.herokuapp.com/api/health`

⏱️ **Time**: 10-30 minutes  
📝 **Next**: Continue where you left off

---

### Scenario 6: "User says it's not working"

✅ **Action**:
1. Ask for their email
2. Check database: `SELECT * FROM users WHERE email = 'their@email.com';`
3. Check their queries: `SELECT * FROM queries WHERE user_id = 'their_id';`
4. Look for errors in logs
5. Reply with fix or workaround

---

### Scenario 7: "I want to add a new feature"

✅ **Action**:
1. Add code to `cite_agent/` or `cite-agent-api/src/`
2. Test locally
3. Commit & push: `git commit -am "Add feature X"`
4. Deploy: `git push heroku main`
5. Test in production

---

## 📊 Key Metrics Dashboard

### Track These Weekly

```bash
# Users
heroku pg:psql --app cite-agent-api -c \
  "SELECT COUNT(*) FROM users;"

# Active users (last 7 days)
heroku pg:psql --app cite-agent-api -c \
  "SELECT COUNT(DISTINCT user_id) FROM queries 
   WHERE timestamp > NOW() - INTERVAL '7 days';"

# Total queries
heroku pg:psql --app cite-agent-api -c \
  "SELECT COUNT(*) FROM queries;"

# Average queries per user
heroku pg:psql --app cite-agent-api -c \
  "SELECT AVG(query_count) FROM 
   (SELECT user_id, COUNT(*) as query_count FROM queries GROUP BY user_id) t;"

# Revenue estimate
heroku pg:psql --app cite-agent-api -c \
  "SELECT COUNT(*) * 10 as monthly_revenue FROM users WHERE is_active = true;"
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Health check failing"

**Symptom**: `curl https://cite-agent-api.herokuapp.com/api/health` returns error  
**Fix**:
```bash
heroku logs --tail --app cite-agent-api
heroku restart --app cite-agent-api
```

---

### Issue 2: "Rate limit hit immediately"

**Symptom**: User says "rate limit exceeded" on first query  
**Fix**: Reset their tokens
```sql
UPDATE users SET tokens_used_today = 0 WHERE email = 'their@email.com';
```

---

### Issue 3: "LLM provider error"

**Symptom**: Queries return "provider error"  
**Fix**: Check API keys
```bash
heroku config:get CEREBRAS_API_KEY_1 --app cite-agent-api
curl -H "Authorization: Bearer <that_key>" https://api.cerebras.ai/v1/models
```

---

### Issue 4: "Database full"

**Symptom**: "database connection failed"  
**Fix**: Upgrade Heroku Postgres
```bash
heroku addons:upgrade postgresql-colorful-85267:standard-0 --app cite-agent-api
```

---

## 📞 When to Ask for Help

### Ask me (or ChatGPT with PROJECT_COMPLETE_STATUS.md) if:

1. **Code changes needed**: "How do I add feature X?"
2. **Architecture questions**: "Should I use Redis for this?"
3. **Bug troubleshooting**: "This error doesn't make sense"
4. **Scaling issues**: "Can the system handle 1000 users?"

### Google/Stack Overflow if:

1. **Heroku commands**: "How to view Heroku logs?"
2. **SQL queries**: "How to count distinct users in PostgreSQL?"
3. **Python syntax**: "How to parse JSON in Python?"
4. **Git commands**: "How to revert a commit?"

---

## ✅ Completion Criteria

### You're ready to launch when:

- ✅ Backend deployed and health check passes
- ✅ Client connects to backend successfully
- ✅ End-to-end test works (register → query → response)
- ✅ Analytics dashboard shows data
- ✅ Download URLs redirect properly

### You're ready to scale when:

- ✅ 20+ active beta users
- ✅ < 5% error rate
- ✅ Positive user feedback
- ✅ All critical bugs fixed
- ✅ Revenue > $100/month

---

## 🎯 TL;DR: Your Next 3 Steps

**Today (While Waiting)**:
1. Verify API keys work (Task 1.1)
2. Create deployment script (Task 1.2)
3. Prepare client for backend URL (Task 1.4)

**Tomorrow (After Approval)**:
1. Run `./deploy.sh` (Task 2.1)
2. Test everything (Task 2.2, 2.3)
3. Invite 10 beta testers (Task 3.1)

**Next Week**:
1. Monitor daily (Task 3.2)
2. Gather feedback (Task 3.3)
3. Fix bugs & iterate

---

**You can execute this plan 100% independently. Everything is documented, tested, and ready to go.** 🚀

*Questions? Re-read PROJECT_COMPLETE_STATUS.md or ask ChatGPT with that file as context.*

