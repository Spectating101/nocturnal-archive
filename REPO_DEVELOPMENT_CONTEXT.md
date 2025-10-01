# Nocturnal Archive Repository Development Context

## 🎯 **Project Overview**
**Goal**: Build a unified research assistant platform that combines an Academic Research API (Archive), a Financial Data API (FinSight), and an AI Agent with persistent shell access—originally targeting a "free Cursor Agent" vision, now matured into a production-grade, integrated system.

## 📚 **Repository Structure & Purpose**
- **Integrated Architecture**: Archive API + FinSight API + Enhanced AI Agent
- **Tech Stack**: FastAPI, PostgreSQL, Redis (with in-memory fallback), Rust for performance-critical operations
- **Core Differentiator**: Cohesive integration of research and finance with robust LLM routing and secure shell tools
- **Main Challenges**: Production hardening, rate limits, security posture, and consistent developer ergonomics

## 🔄 **Development Progression**

### **Phase 1: Initial Repository Analysis & Integration**
- **Started with**: Comprehensive analysis of existing codebase
- **Key Discovery**: Repository had research and finance systems that could be leveraged
- **Integration Focus**: Connected Groq API to existing research/finance services
- **Files Created**: 
  - `src/services/integrated_analysis_service.py` - Cross-system analysis
  - `src/routes/integrated_analysis.py` - API endpoints
  - Updated multiple services to use Groq instead of other LLMs

### **Phase 2: Groq Model Optimization**
- **Initial Model**: `llama-3.1-70b-versatile` (decommissioned)
- **Migration**: Updated to `llama-3.3-70b-versatile` across all services
- **Rate Limit Issues**: Discovered token limits (12K TPM, 100K TPD) constraining complex workflows
- **Model Experimentation**: Tested various Groq models for optimal balance

### **Phase 3: Interactive Chatbot Development**
- **First Attempt**: `groq_chatbot.py` - Basic interactive interface
- **Critical Issue**: Groq hallucinating file system contents instead of using real terminal access
- **Solution**: Implemented `subprocess.run()` to execute commands suggested by Groq and feed real results back
- **Persistent Shell Problem**: Commands like `cd` weren't persisting between interactions
- **Major Fix**: Implemented persistent bash session using `subprocess.Popen()`

### **Phase 4: User Experience Optimization**
- **Problem**: Groq outputting `<think>` tags, wasting tokens and cluttering interface
- **Solution**: Updated system prompts to enforce direct, concise responses
- **Token Management**: Reduced max_tokens, truncated outputs, limited conversation history
- **Rate Limit Optimization**: Implemented multiple API key support for better limits

### **Phase 5: Architecture Evolution & Cleanup**
- **Model Selection Debate**: 
  - 8B models: Too weak for complex reasoning
  - 32B models: Better but still constrained by rate limits
  - 70B models: Best capability but expensive and rate-limited
- **Hybrid Architecture Concept**: "8B Intern → 32B/70B Supervisor" approach
- **Repository Cleanup**: Consolidated agents into `ai_agent.py`, removed redundant files, organized documentation

### **Phase 6: Justice for Archive API & AI Agent (Recent)**
- **Upgrades**: Real data sources (OpenAlex, PubMed), Redis caching with fallback, LLM synthesis via Groq; AI Agent integrated both APIs with smart routing and token management
- **Security**: Argon2 password hashing, principal-aware rate limits, strict shell allowlist/denylist
- **Reliability**: App runs in degraded mode without Redis; structured logging and metrics added
- **Result**: Archive and Agent elevated to parity with FinSight

## 🧠 **Key Technical Challenges Discovered**

### **1. Model Capability Limitations**
- **8B Models**: Insufficient for complex multi-step reasoning
- **32B Models**: Better but still struggle with Cursor Agent-level tasks
- **70B Models**: Capable but constrained by rate limits
- **Fundamental Issue**: Advanced reasoning requires advanced models, which cost money

### **2. Rate Limit Constraints**
- **Groq Free Tier**: 30 RPM, 6K-12K TPM, 500K TPD
- **Complex Tasks**: Require 3-5 API calls (routing + execution + analysis)
- **Reality**: Free tier insufficient for daily development assistance

### **3. Shell State Management**
- **Problem**: Each `subprocess.run()` call is isolated
- **Solution**: Persistent bash session with `subprocess.Popen()`
- **Benefit**: Directory changes and environment variables persist

### **4. Token Efficiency**
- **Issue**: Verbose responses and internal reasoning waste tokens
- **Solution**: Concise prompts, truncated outputs, limited context
- **Trade-off**: Balancing intelligence vs. token limits

## 🎯 **Current Architecture (Production)**
- **FinSight API**: Regulator-first financial data with citations, rate limiting, caching
- **Archive API**: OpenAlex/PubMed search, synthesis with LLM, caching, RFC 7807-style errors
- **Enhanced AI Agent**: Persistent shell via `subprocess.Popen()`, smart routing across APIs, token management
- **Security & Ops**: Argon2 hashing, JWT/API keys, principal-aware rate limits, Redis fallback, Prometheus metrics, structured logs

## 💡 **Proposed Hybrid Architecture**
**8B Intern → 32B Supervisor Model**:
- **8B Intern**: Handles simple tasks, routing decisions, user interaction
- **32B Supervisor**: Executes complex tasks, provides quality analysis
- **Benefits**: Cost efficiency, better capability distribution
- **Implementation**: Smart escalation based on task complexity

## 🚧 **Current Status & Limitations**
- **Working**: Production-grade APIs and integrated agent workflows
- **Functional**: Auth, rate limiting, caching, degraded mode without Redis
- **Known Issues**: Minor shell test edge case; synthesis constructor requires adjustment for strict fallback
- **Constraints**: Free-tier rate limits still shape throughput under heavy load

## 🤔 **Fundamental Question**
**Is a truly functional "free Cursor Agent" achievable?**
- **Technical Feasibility**: Yes, with hybrid routing and careful budgeting
- **Rate Limit Reality**: Free tier remains constraining at scale; graceful degradation implemented
- **Model Capability**: 32B/70B excel but require budgets; fallbacks are in place
- **Alternative**: Paid tier or local models; current system remains usable within limits

## 📁 **Key Files**
- `ai_agent.py` - Consolidated agent
- `groq_fixed.py` - Original working chatbot (kept for reference)
- `nocturnal-archive-api/src/main_production.py` - Production FastAPI app
- `nocturnal-archive-api/src/middleware/rate_limiting.py` - Redis-backed RL with headers
- `nocturnal-archive-api/src/auth/security.py` - JWT/API key auth with Argon2
- `nocturnal-archive-api/src/services/paper_search.py` - OpenAlex/PubMed integration
- `nocturnal-archive-api/src/services/synthesizer.py` - LLM synthesis
- `nocturnal-archive-api/src/middleware/redis_fallback.py` - In-memory degraded mode
- `docs/` - All documentation

## 🎯 **Next Steps Discussion Points**
1. **LLM Circuit Breaker**: Expand template-based fallback coverage across endpoints
2. **Shell Security**: Close remaining edge case in input redirection parsing
3. **KPI Discovery**: Publish `/v1/finance/kpis/registry` and alias common terms
4. **Idempotency**: Add `Idempotency-Key` to write-ish endpoints
5. **Dashboards**: Route latency, RL hits, token usage, shell execs, cache hit rate

## 🔑 **Key Insights for Opus 4**
- **Strong foundation** with integrated research and finance systems
- **Production hardening** completed: auth, rate limits, degraded mode, structured errors
- **Persistent shell access** is secure and stateful; validations in place
- **Main challenge**: Balancing capability, cost, and throughput under free tiers
- **Architecture decisions**: Hybrid routing and fallbacks sustain a solid beta experience

