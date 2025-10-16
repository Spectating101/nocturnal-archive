# Comprehensive Audit & Fix Plan - v1.3.0

**Status**: IN PROGRESS  
**Goal**: NO hardcoded patterns, perfect execution order, all features tested

---

## Critical Issues Found

### 🔴 **ISSUE 1: Wrong Execution Order**

**Current**:
```
1. Archive API (line 2617)
2. FinSight API (line 2632)
3. Web Search (line 2686) ← Grabs "look into it", web searches
4. Shell Planning (line 2745) ← Never runs
```

**Problem**: Web search handles "look into it" before shell planner can resolve pronoun

**Fix**: Reorder to:
```
1. Shell Planning ← FIRST (reasoning/intent layer)
2. Archive API (only if shell_action = "none")
3. FinSight API (only if shell_action = "none")
4. Web Search (only if shell_action = "none" AND no data found)
```

**Why**: Shell planning = understanding WHAT user wants (intent classifier)  
Data APIs = fetching data AFTER understanding intent

---

### 🔴 **ISSUE 2: Shell Planning Isolated from Main Flow**

**Current**: Shell planning inside `if self.client is None:` (production mode only)

**Problem**: Dev mode doesn't get shell planning!

**Fix**: Move shell planning OUTSIDE mode check, runs for BOTH modes

---

### 🔴 **ISSUE 3: Multiple LLM Calls Not Tracked**

**Current**: Shell planner, finance planner, web decision all make backend calls  
**Problem**: No tracking of how many intelligence calls made

**Fix**: Track all LLM calls for debugging/telemetry

---

## Audit Checklist

### Execution Flow
- [ ] Shell planning runs FIRST (before any data APIs)
- [ ] Shell planning works in dev AND production
- [ ] If shell handles query (pwd/ls/find), data APIs optionally skip
- [ ] Web search only if shell says "none" and no data found

### LLM Planners
- [ ] Shell planner: Returns valid JSON always
- [ ] Finance planner: Handles all company name variations
- [ ] Web decision: Understands when web is needed vs not

### Error Handling
- [ ] If shell planner fails → graceful fallback
- [ ] If finance planner fails → graceful fallback
- [ ] If web decision fails → graceful fallback
- [ ] Never shows users "JSON parse error"

### Conversation Context
- [ ] Shell planner gets last 2 messages (for pronouns)
- [ ] Finance planner gets conversation (for "what about Microsoft?")
- [ ] History saved correctly after response

---

## Test Matrix

### Shell Commands
- [ ] `where am i?` → pwd
- [ ] `what files are here?` → ls current directory
- [ ] `find cm522 in downloads` → find with correct target
- [ ] `look into it` (after find) → ls target directory

### Finance Queries
- [ ] `Tesla revenue` → Ticker: TSLA, Metric: revenue
- [ ] `What's Apple worth?` → Ticker: AAPL, Metric: marketCap
- [ ] `tsla stock price` → Ticker: TSLA (lowercase), Metric: price
- [ ] `Microsoft profit` → Ticker: MSFT, Metric: netIncome

### Web Search
- [ ] `Bitcoin price` → Should web search (current data)
- [ ] `Snowflake market share` → Should web search (not in SEC)
- [ ] `Tesla revenue` → Should NOT web search (FinSight has it)

### Pronoun Resolution
- [ ] `find X` then `look into it` → Lists directory X
- [ ] `Tesla revenue` then `what about Apple?` → Gets Apple revenue
- [ ] `show library` then `export it` → Exports library

---

## Implementation Steps

1. **Fix execution order** (shell first)
2. **Add error handling** (all planners)
3. **Test all 15 test cases** (document results)
4. **Publish v1.3.1** (only if ALL tests pass)

---

**Current Status**: Code restored to last commit (clean state)  
**Next**: Implement fixes systematically, test thoroughly


