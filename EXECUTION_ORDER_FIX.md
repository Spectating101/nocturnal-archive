# Execution Order Fix - Complete Strategy

## Current Architecture (v1.3.0 - BROKEN)

```python
async def process_request(request):
    # 1. Workflow commands (library, export, etc.)
    if workflow: return workflow_response
    
    # 2. Request analysis (vague detection)
    request_analysis = analyze_request_type()
    
    # 3. Archive API (if not vague)
    if "archive" in apis:
        search_papers()
    
    # 4. FinSight API (if not vague)  
    if "finsight" in apis:
        LLM_FINANCE_PLANNER()  # Extracts ticker + metric
        call_finsight()
    
    # 5. Web Search
    LLM_WEB_DECISION()  # Should we web search?
    if yes: web_search()
    
    # 6. Shell Planning (PRODUCTION MODE ONLY)
    if self.client is None:  # Production mode
        LLM_SHELL_PLANNER()  # pwd/ls/find
        execute_shell()
    
    # 7. Main LLM
    call_backend_query()
```

**Problems**:
1. Shell planning comes LAST → Web search grabs "look into it" first
2. Shell planning only in production → Dev mode doesn't get it
3. Archive might search for papers on "cm522" (waste)
4. No coordination between planners

---

## Fixed Architecture (v1.3.1 - TARGET)

```python
async def process_request(request):
    # 1. Workflow commands
    if workflow: return workflow_response
    
    # 2. SHELL PLANNING (FIRST - for BOTH modes)
    # Acts as "reasoning" layer - understands INTENT
    LLM_SHELL_PLANNER(query, conversation_history)
    → Returns: {"action": "pwd|ls|find|none", ...}
    
    shell_action = plan["action"]
    
    if shell_action in ["pwd", "ls", "find"]:
        execute_shell_command(plan)
        # Shell handled it - skip data APIs (optional)
    
    # 3. Data APIs (ONLY if shell didn't fully handle it)
    if shell_action == "none":
        # 3a. Archive API
        if needs_research:
            search_papers()
        
        # 3b. FinSight API
        if needs_finance:
            LLM_FINANCE_PLANNER()  # Extract ticker + metric
            call_finsight()
        
        # 3c. Web Search (fallback)
        if no_data_yet:
            LLM_WEB_DECISION()  # Should we web search?
            if yes: web_search()
    
    # 4. Main LLM (with all gathered data)
    call_backend_query(api_results)
```

**Benefits**:
1. Shell planning FIRST → Understands intent before data fetching
2. Prevents wasted API calls ("cm522" won't trigger Archive)
3. Works in BOTH production and dev modes
4. Proper fallback chain: shell → data APIs → web → main LLM

---

## Code Changes Required

### Change 1: Extract Shell Planning from Production Mode Block
**Current**: Lines 2745-2850 inside `if self.client is None:`  
**New**: Lines ~2600 (right after workflow check, before any APIs)  
**Scope**: Move ~105 lines

### Change 2: Add Conditional Data API Calls
**Current**: Archive/FinSight always run if in request_analysis  
**New**: Only run if `shell_action == "none"`

### Change 3: Web Search Becomes True Fallback
**Current**: Web search based on LLM decision (ignores shell)  
**New**: Only considers web if `shell_action == "none" AND not api_results`

---

## Testing Required (15 test cases)

### Shell Operations (Should NOT trigger data APIs)
1. `where am i?` → pwd, no Archive/FinSight/Web
2. `what files here?` → ls, no Archive/FinSight/Web
3. `find cm522 in downloads` → find, no Archive/FinSight/Web
4. `look into it` → ls target, no Web search

### Finance Queries (Should NOT trigger shell)
5. `Tesla revenue` → FinSight only
6. `What's Apple worth?` → FinSight only
7. `tsla stock price` → FinSight only

### Research Queries (Should NOT trigger shell/finance)
8. `Papers on transformers` → Archive only
9. `Machine learning research` → Archive only

### Mixed Queries (Should trigger multiple)
10. `Tesla revenue and recent news` → FinSight + Web
11. `Papers on Tesla AND current stock price` → Archive + FinSight

### Pronoun/Context (Should use conversation)
12. `find cm522` then `look into it` → Shell planner resolves
13. `Tesla revenue` then `what about Apple?` → Finance planner infers
14. `show library` then `export it` → Workflow handles

### Fallback Cases
15. `What's the meaning of life?` → None of above, straight to main LLM

---

## Implementation Priority

**Phase 1** (Critical): Fix execution order  
**Phase 2** (Important): Test all 15 cases  
**Phase 3** (Polish): Error handling for all planners  
**Phase 4** (Deploy): Only if ALL tests pass

---

**Status**: Ready to implement Phase 1



