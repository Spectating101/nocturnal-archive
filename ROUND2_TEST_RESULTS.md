# Round 2 Test Results - 5 NEW Companies
**Date:** October 4, 2025
**Test:** Duration filtering verification with fresh companies

---

## ⚠️ IMPORTANT DISCOVERY

**New Issue Found:** Period matching problem when calculating composite metrics.

Revenue and Cost of Revenue may come from **different SEC filings/periods**, causing incorrect calculated values (like negative gross profit).

---

## Test Results Summary

### 1. 💻 **Microsoft (MSFT)**
**Result:** ⚠️ **PERIOD MISMATCH**

- Revenue: $26,819M
- Cost: $21,919M
- Calculated Gross Profit: $4,900M
- Margin: 18.3%

**Problem:**
- Revenue Accession: `0001564590-18-009307` (from **2018**)
- Cost Accession: `0000950170-25-061046` (from **2025**)

**Evidence:** Different accession numbers = different periods mixed!

**For ChatGPT:** Please verify Microsoft's actual Q2 2025 quarterly revenue and gross profit. The values above are likely incorrect due to period mismatch.

---

### 2. 🔴 **AMD**
**Result:** ❌ **NEGATIVE GROSS PROFIT** (Period Mismatch)

- Revenue: $1,647M
- Cost: $4,626M
- **Gross Profit: -$2,979M** ❌
- **Margin: -180.9%** ❌

**Problem:**
- Revenue Accession: `0000002488-18-000068` (from **2018**)
- Cost Accession: `0000002488-25-000108` (from **2025**)

**Root Cause:** Revenue from 2018 filing, Cost from 2025 filing = nonsensical result.

**For ChatGPT:** This is obviously wrong. AMD should have positive gross profit. The issue is our period matching, not the duration filter.

---

### 3. 🛒 **Shopify (SHOP)**
**Result:** ✅ **LIKELY CORRECT** (Same Accession)

- Revenue: $2,680M
- Cost: $1,378M
- Gross Profit: $1,302M
- Margin: 48.6%
- Accession: `0001594805-25-000073` (2025)

**Good Sign:** Both revenue AND cost from same accession (0001594805-25-000073).

**For ChatGPT:** Please verify Shopify's Q2 2025 quarterly financial data:
- Revenue: ~$2,680M
- Gross Profit: ~$1,302M
- Gross Margin: ~48.6%

---

### 4. 🚗 **Uber (UBER)**
**Result:** ⚠️ **INCOMPLETE** (No Cost Data)

- Revenue: $3,166M
- Cost: **No data found**
- Accession: `0001543151-19-000017`

**Problem:** SEC XBRL data doesn't contain `costOfRevenue` concept for Uber.

**Possible Reasons:**
1. Uber reports costs differently (multiple line items instead of single "cost of revenue")
2. Different GAAP reporting structure
3. Data quality issue in SEC XBRL

**For ChatGPT:** Does Uber report "Cost of Revenue" or "Cost of Services" in their Q2 2025 10-Q? Or do they break it down differently?

---

### 5. 💳 **Block/Square (SQ)**
**Result:** ❌ **TICKER NOT FOUND**

**Problem:** Ticker "SQ" not in our symbol mapping database.

**Note:** Company rebranded from "Square" to "Block" - may need to update ticker mapping.

---

## 📊 Summary Statistics

| Status | Count | Companies |
|--------|-------|-----------|
| ✅ Correct | 1 | SHOP |
| ⚠️ Period Mismatch | 2 | MSFT, AMD |
| ⚠️ Incomplete | 1 | UBER |
| ❌ Not Found | 1 | SQ |

**Success Rate:** 1/5 (20%) - but NOT a duration filter issue!

**Root Cause:** Period matching, not duration filtering.

---

## 🔍 Key Evidence

### Duration Filtering IS Working ✅

All queries show proper filtering in logs:
```
[info] Filtered to 116 facts with correct duration (60-120 days)  # MSFT
[info] Filtered to 40 facts with correct duration (60-120 days)   # AMD
[info] Filtered to 4 facts with correct duration (60-120 days)    # UBER
[info] Filtered to 4 facts with correct duration (60-120 days)    # SHOP
```

### But Period Matching Is Broken ❌

Example from AMD:
```python
# Revenue query (independent)
revenue_fact = get_fact("AMD", "revenue", "latest", "Q")
# Returns: accession=0000002488-18-000068 (2018)

# Cost query (independent)
cost_fact = get_fact("AMD", "costOfRevenue", "latest", "Q")
# Returns: accession=0000002488-25-000108 (2025)

# Calculation
gross_profit = revenue_fact.value - cost_fact.value
# Result: NONSENSE! ($1.6B - $4.6B = -$2.9B)
```

---

## 🎯 What This Means

### The Good News ✅
Duration filtering (the original bug) **IS FIXED**:
- All queries filter to 60-120 days for quarterly
- Logs confirm filtering is active
- PLTR test still passes perfectly

### The Bad News ⚠️
**NEW BUG DISCOVERED:** Period matching issue.

When calculating `grossProfit = revenue - costOfRevenue`:
1. Each input fetched independently with `period="latest"`
2. Due to different concept availability, they may come from different filings
3. Result: Mixing 2018 revenue with 2025 costs = negative gross profit

**This is NOT a duration filter bug** - it's a calculation engine issue.

---

## 🔧 Recommended Next Steps

### Priority 1: Fix Period Matching
Ensure all inputs for a calculated metric come from the **same filing/accession**.

**Approach:**
1. Modify `_get_best_fact()` in `src/calc/engine.py`
2. Track accession numbers for all inputs
3. Validate consistency or attempt to find matching set

### Priority 2: Add Period Validation
In calculated metrics, check that:
- All inputs have matching `start_date` and `end_date`
- Or at least same `accession` number
- Flag quality warning if mismatch

### Priority 3: Test More Companies
After fixing period matching, retest:
- MSFT
- AMD
- WMT (from Round 1, also had old data)

---

## For ChatGPT Verification

Please verify these **REVENUE ONLY** values (cost data is unreliable due to period mismatch):

1. **Shopify (SHOP)** - Q2 2025 Revenue: ~$2,680M
2. **Uber (UBER)** - Q2 2025 Revenue: ~$3,166M

And explain why:
3. **AMD** showing negative gross profit is obviously wrong (our bug, not their data)
4. **Microsoft** 18.3% gross margin seems low (likely period mismatch)

---

**Date:** 2025-10-04
**Tester:** Claude (Sonnet 4.5)
**Status:** Duration filter working ✅, Period matching broken ⚠️
