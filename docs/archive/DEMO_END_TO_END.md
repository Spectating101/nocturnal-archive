# 🎬 NOCTURNAL ARCHIVE - END-TO-END DEMO

## 🧩 Understanding Why Tests Fail

### The Problem:
```python
# In finance_calc.py (line 23-24)
facts_store = FactsStore()  # ← Empty in-memory store!
calc_engine = CalculationEngine(facts_store, kpi_registry)
```

**Why it's empty:**
- FactsStore is created fresh on each API startup
- No data loaded automatically
- Tests expect SEC data to be populated
- Data must be fetched from SEC API or loaded from cache

### The Data Flow:
```
User Query
    ↓
Finance API (/v1/finance/calc/AAPL/grossProfit)
    ↓
Calculation Engine (needs: revenue, costOfRevenue)
    ↓
FactsStore.get_fact() → Returns None! (store is empty)
    ↓
Error: 'inputs' KeyError
```

## 🔧 How To Fix It

### Option 1: Multi-Source Router (REAL FIX)
The system has a `MultiSourceRouter` that:
1. Checks FactsStore first
2. Falls back to SEC EDGAR API
3. Falls back to Yahoo Finance
4. Caches results in FactsStore

**This is how it SHOULD work!**

### Current Issue:
The finance_calc route uses `FactsStore()` directly instead of going through the multi-source router!

Let me show you the fix:

