# Duration Filter Fix - Complete Documentation
**Date:** October 4, 2025
**Status:** ✅ COMPLETE - YTD Bug Fixed, Period Matching Issue Discovered
**For:** Future Claude/Copilot sessions

---

## 🎯 Executive Summary

**Bug Fixed:** Finance API was returning YTD/cumulative values instead of quarterly values, causing 31% revenue overstatement.

**Example (PLTR Q2 2025):**
- ❌ **Before:** Revenue $1,312M, Gross Profit $1,067M (YTD values)
- ✅ **After:** Revenue $1,003.7M, Gross Profit $810.8M (quarterly values)
- **Verification:** Matches Palantir's official Q2 2025 Business Update to the dollar

**Root Cause:** SEC XBRL data contains BOTH quarterly (~90 days) and YTD (~180 days) values for the same period label. The API wasn't filtering by duration, so it grabbed whichever came first.

---

## 🔧 What Was Fixed

### Fix Overview
Added **duration-based filtering** to ensure only facts with appropriate period length are returned:
- **Quarterly (`freq="Q"`)**: 60-120 days duration
- **Annual (`freq="A"`)**: 300-400 days duration

### Files Modified

#### 1. `src/adapters/sec_facts.py` (Commit `f097b2a`)
**Changes:**
- Added `_calculate_fact_duration_days()` method to compute period length from start/end dates
- Added `_filter_by_duration()` method to filter facts list by duration range
- Modified `_find_fact_for_period()` to apply duration filtering before selecting fact

**Key Code:**
```python
def _filter_by_duration(self, facts: List[Dict[str, Any]], freq: str) -> List[Dict[str, Any]]:
    """Filter facts to match expected duration for frequency"""
    if freq == "Q":
        min_days, max_days = 60, 120  # Quarterly: ~90 days
    elif freq == "A":
        min_days, max_days = 300, 400  # Annual: ~365 days

    # Calculate durations and filter
    filtered = [
        fact for fact, duration in facts_with_duration
        if min_days <= duration <= max_days
    ]

    if filtered:
        logger.info(f"Filtered to {len(filtered)} facts with correct duration ({min_days}-{max_days} days)")
        return filtered
```

#### 2. `src/facts/store.py` (Commit `d8e095f`)
**Changes:**
- Added `start_date` and `end_date` fields to `Fact` dataclass
- Populated these fields in `_create_fact_from_data()` from normalized SEC data
- Added `_filter_facts_by_duration()` method (same logic as adapter)
- Applied duration filter in `get_fact()` before selecting latest
- **Changed sorting** from period label string to actual `end_date` for accuracy

**Why Both Files:** API has two code paths:
1. Direct adapter call (used by calculation engine for complex expressions)
2. FactsStore cached lookup (used for simple metric retrieval)

Both needed the same filtering to ensure consistency.

---

## 📊 Test Results

### Round 1: Initial Verification (5 Companies)

| Ticker | Company | Revenue | Gross Profit | Verified |
|--------|---------|---------|--------------|----------|
| **PLTR** | Palantir | $1,003.7M | $810.8M | ✅ **EXACT MATCH** |
| **NVDA** | NVIDIA | $46,743M | $33,853M | ✅ Confirmed |
| **RBLX** | Roblox | $1,080.7M | $844.6M | ✅ Revenue confirmed |
| **ABNB** | Airbnb | $3,096M | $2,552M | ✅ Revenue confirmed |
| **COIN** | Coinbase | $1,497.2M | N/A | ✅ Revenue confirmed |

**Evidence of Fix Working:**
```
2025-10-04 17:25:42 [info] Filtered to 28 facts with correct duration (60-120 days)
2025-10-04 17:25:43 [info] Fact retrieved accession=0001321655-25-000106 value=1003697000
```

**ChatGPT Verification:**
> "From Palantir's Q2 2025 Business Update:
> • Revenue = $1,003,697 thousand = ~$1,003.7 M ✅
> • Gross Profit (GAAP) = $810,763 thousand = ~$810.8 M ✅"

### Round 2: Additional Testing (5 NEW Companies)

| Ticker | Company | Status | Notes |
|--------|---------|--------|-------|
| MSFT | Microsoft | ⚠️ Period mismatch | Revenue from 2018, Cost from 2025 |
| AMD | AMD | ⚠️ Period mismatch | Negative gross profit (wrong periods) |
| SHOP | Shopify | ✅ Working | $2,680M revenue, $1,302M GP |
| UBER | Uber | ⚠️ No cost data | Missing `costOfRevenue` in SEC data |
| SQ | Block | ❌ Ticker not found | Not in symbol map |

**⚠️ NEW ISSUE DISCOVERED:** Period matching problem - revenue and cost sometimes from different filings!

---

## 🐛 Known Issues

### 1. ✅ **FIXED:** YTD/Cumulative Values Bug
**Status:** RESOLVED
**Fix:** Duration filtering (60-120 days for quarterly)
**Evidence:** PLTR now returns $1,003.7M instead of $1,312M

### 2. ⚠️ **OPEN:** Period Matching Across Metrics
**Status:** DISCOVERED Oct 4, 2025
**Problem:** When calculating `grossProfit = revenue - costOfRevenue`, the two inputs may come from different periods/accessions.

**Example:**
- MSFT: Revenue accession `0001564590-18-009307` (2018) vs Cost accession `0000950170-25-061046` (2025)
- Result: Negative or nonsensical gross profit

**Root Cause:** Each metric is fetched independently with "latest" period. Due to different XBRL concept availability, they may resolve to different filings.

**Potential Fix:** Ensure all inputs for a calculation come from the same accession/filing. Options:
1. Group facts by accession, pick most recent complete set
2. Validate that all inputs have matching `start_date` and `end_date`
3. Add a "period consistency check" in calculation engine

**Priority:** HIGH - Affects calculated metrics reliability

### 3. ⚠️ **OPEN:** Start/End Dates Not Propagating to API Response
**Status:** OPEN
**Problem:** `citation.start` and `citation.end` showing as `None` in API responses, even though data exists in adapter.

**Evidence:**
```json
{
  "citation": {
    "start": null,  // Should be "2025-04-01"
    "end": null     // Should be "2025-06-30"
  }
}
```

**Impact:** Users can't verify period duration without checking SEC filing directly.

**Potential Fix:** Check `_convert_store_fact()` in `src/calc/engine.py` - may not be mapping start/end dates from Fact object to response.

---

## 🔍 How to Verify the Fix

### Quick Test (30 seconds)
```bash
cd nocturnal-archive-api
.venv/bin/python test_duration_fix.py
```

**Expected Output:**
```
✅ Revenue: $1,003,697,000
✅ Gross Profit: $810,763,000
✅ TEST PASSED: Duration filtering is working correctly!
```

### Via API (with server running)
```bash
curl -H 'X-API-Key: demo-key-123' \
  "http://127.0.0.1:8000/v1/finance/calc/PLTR/grossProfit?period=latest" \
  | jq '{value: .value, revenue: .inputs.revenue.value}'
```

**Expected:**
```json
{
  "value": 810763000.0,
  "revenue": 1003697000.0
}
```

### Check Logs for Duration Filtering
```bash
# In server logs, look for:
[info] Filtered to 28 facts with correct duration (60-120 days)
```

---

## 📝 Git Commits

### Commit 1: `f097b2a`
```
fix: Add duration filtering to prevent YTD values in quarterly data

- Added _calculate_fact_duration_days() method
- Added _filter_by_duration() method
- Modified _find_fact_for_period() to apply filtering
- File: src/adapters/sec_facts.py
```

### Commit 2: `d8e095f`
```
fix: Complete duration filtering in FactsStore - Part 2 of YTD bug fix

- Added start_date/end_date to Fact dataclass
- Added _filter_facts_by_duration() method
- Changed sorting from period label to actual end_date
- File: src/facts/store.py
```

---

## 🚀 How to Continue (For Copilot/Future Claude)

### If You Need to Debug Further

**Check Duration Filtering is Active:**
```python
# In Python console:
import asyncio
from src.adapters.sec_facts import SECFactsAdapter

async def test():
    adapter = SECFactsAdapter()
    result = await adapter.get_fact(ticker="PLTR", concept="revenue", period="latest", freq="Q")
    print(f"Revenue: ${result.get('value')/1e6:.1f}M")

    # Check citation dates
    cite = result.get("citation", {})
    print(f"Period: {cite.get('start')} to {cite.get('end')}")

    # Should see in logs: "Filtered to X facts with correct duration (60-120 days)"

asyncio.run(test())
```

**Expected Log Output:**
```
[info] Filtered to 28 facts with correct duration (60-120 days)
```

### Fixing the Period Matching Issue

**Problem:** Revenue and Cost from different periods.

**Solution Approach:**
1. Read `src/calc/engine.py` line ~440 (`_get_best_fact` method)
2. Modify to track accession numbers across all inputs
3. Ensure all inputs come from same filing

**Pseudocode:**
```python
# In calculation engine when evaluating expression:
accessions = {}
for variable, fact in input_facts.items():
    accessions[variable] = fact.accession

# Check all match
if len(set(accessions.values())) > 1:
    logger.warning("Inputs from different filings", accessions=accessions)
    # Either: try to find matching set, or flag quality issue
```

### Testing with ChatGPT

**Prompt Template:**
```
I have financial data from SEC filings for these companies.
Please verify the Q2 2025 (latest quarter) values:

1. [COMPANY] ([TICKER])
   - Revenue: $X.XM
   - Gross Profit: $X.XM
   - Period: YYYY-MM-DD to YYYY-MM-DD
   - SEC Accession: XXXX-XX-XXXXXX

Please check against the company's official Q2 2025 earnings release or 10-Q filing.
```

---

## 📚 Key Files Reference

| File | Purpose | Key Methods |
|------|---------|-------------|
| `src/adapters/sec_facts.py` | Fetches from SEC API | `get_fact()`, `_filter_by_duration()` |
| `src/facts/store.py` | Caches & indexes facts | `get_fact()`, `_filter_facts_by_duration()` |
| `src/calc/engine.py` | Evaluates expressions | `evaluate()`, `_get_best_fact()` |
| `src/calc/registry.py` | Metric definitions | `grossProfit`, `grossMargin`, etc. |
| `test_duration_fix.py` | Test script | `test_palantir_q2_2025()` |

---

## 🔐 Environment Setup

**Required:**
```bash
cd /path/to/Nocturnal-Archive/nocturnal-archive-api
source .venv/bin/activate  # Or use .venv/bin/python directly
```

**API Key for Testing:**
```bash
export NOCTURNAL_KEY=demo-key-123
# Or pass as header: -H 'X-API-Key: demo-key-123'
```

**Start Server:**
```bash
.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## ✅ Success Criteria

The fix is working if:

1. ✅ PLTR Q2 2025 returns $1,003.7M revenue (not $1,312M)
2. ✅ Logs show "Filtered to X facts with correct duration (60-120 days)"
3. ✅ ChatGPT verification confirms values match official filings
4. ⚠️ **NEW:** All inputs for calculated metrics come from same period/accession

---

## 📞 Contact / Handoff

**For Next Session:**
- Read this document first
- Run `test_duration_fix.py` to verify fix still works
- Check open issues section above
- Priority: Fix period matching for calculated metrics

**Test Command:**
```bash
cd nocturnal-archive-api
.venv/bin/python test_duration_fix.py && echo "✅ FIX VERIFIED"
```

**Branch:** `overnight-backup-20251003`

**Last Updated:** 2025-10-04 by Claude (Sonnet 4.5)

---

**END OF DOCUMENTATION**
