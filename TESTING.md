# Agent Intelligence Testing

## Basic Test (No API Keys Required)
Test fast-path queries without credentials:
```bash
python3 test_agent_basic.py
```
Tests "where are we?" and "test" queries that work without LLM calls.

## Quick Test
Run a simple 5-query test (requires API keys):
```bash
python3 test_agent_live.py
```

## Comprehensive Test
Run full autonomy evaluation - 7 scenarios (requires API keys):
```bash
python3 test_agent_comprehensive.py
```

## Detailed Scoring Test
Run 5 tests with detailed scoring (requires API keys):
```bash
python3 test_agent_autonomy.py
```

---

## Current Results

**Overall Score: 91.4/100** ✅
- **Verdict:** Claude-level intelligence
- **Strengths:** Natural communication, proactive tool usage, no asking user to work
- **Minor Issue:** Slight verbosity on file listings (acceptable trade-off)

See `docs/AGENT_INTELLIGENCE_REPORT.md` for full analysis.

---

## Test Requirements

The tests require valid API keys or backend access to test LLM-dependent features:

```bash
export CEREBRAS_API_KEY="your_key"
export GROQ_API_KEY="your_key"
python3 test_agent_live.py
```

Without API keys:
- Fast-path queries ("where are we?", "test") will still work
- LLM-dependent queries will fail or attempt backend mode
- Tests will show which features require credentials

The test scripts use relative paths (`Path(__file__).parent.absolute()`) so they work regardless of where the repository is located.

---

## What We Test

1. **Location queries** - "where are we?" → Natural, concise response
2. **File operations** - "what files are here?" → Lists files without asking user
3. **Test probes** - "test" → Quick acknowledgment, no lecture
4. **File reading** - "show me setup.py" → Reads and displays content
5. **Information finding** - "find the version" → Searches and reports
6. **Summarization** - "tell me about this project" → Concise overview
7. **Search tasks** - "are there test files?" → Searches and answers

---

## Evaluation Criteria

Each test scored on:
- **No errors** (50 points) - Response works, no "❌" errors
- **Doesn't ask user** (30 points) - No "you can run", "try running"
- **Concise** (20 points) - Appropriate length for query

**Pass threshold:** 80/100
**Claude-level threshold:** 90+ average

---

## Key Changes That Achieved Claude-Level

1. **Simplified system prompt** (250+ lines → 40 lines)
   - Removed verbose instructions
   - Added personality guidance
   - Focus on behavioral principles

2. **Fast-path queries** for common patterns
   - "where are we?" → instant pwd
   - "test" → instant probe response

3. **Shell result formatting** updated
   - Changed from "present exactly" to "summarize key info"
   - Encourages concise answers over full output dumps

---

Last Updated: 2025-11-04
Version: 1.3.9 → 1.4.0
