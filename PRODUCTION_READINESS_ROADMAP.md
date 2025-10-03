# 🚀 Production Readiness Roadmap - Nocturnal Archive
**Goal:** 92%+ reliability, production-grade financial data aggregator for monetization
**Current State:** 69% pass rate, period matching fixed
**Target:** 95%+ reliability, enterprise-grade

---

## 📊 Current Issues from Stress Test

**Test Results (42 tests):**
- ✅ Passed: 29/42 (69%)
- ❌ Failed: 13/42 (31%)

**Failure Breakdown:**
1. **Rate Limiting** (11 tests) - 26% of all tests
   - TSM, BMBL, BYND, GME, AMC, BTC-USD, ETH-USD
   - Root cause: Burst limit too low (20 req/min)

2. **Expression Parsing** (1 test) - RH
   - Error: "Unsafe expression: revenu"
   - Root cause: Typo in expression validator

3. **Old Data** (Not blocking, but concerning)
   - ULTA: 2017-Q3 data
   - BABA: 2020-Q2 data
   - Root cause: Limited SEC data availability

---

## 🎯 Phase 1: Quick Wins (Day 1) - CLAUDE
**Objective:** 69% → 85% pass rate
**Owner:** Claude Code (me)
**Time Estimate:** 4 hours

### Task 1.1: Fix Rate Limiting ⚡ (1 hour)
**File:** `src/middleware/api_auth.py`
**Lines:** 51, 60, 113

**Changes:**
```python
# Current
"burst_limit": 20,
"burst_limit": max(1, self.settings.rate_limit_burst),

# New - Test Environment
if self.settings.environment == "test":
    "burst_limit": 100,  # High limit for testing
    "rate_limit": 500,   # 500 req/hour
else:
    "burst_limit": 60,   # Production: 60 req/min
    "rate_limit": 300,   # Production: 300 req/hour
```

**Acceptance Criteria:**
- All 42 stress tests pass without rate limit errors
- Test: Run `stress_test_diverse_tickers.py` - 0 rate limit failures

### Task 1.2: Add Sanity Checks 🛡️ (2 hours)
**File:** `src/calc/engine.py` (new method)
**Location:** After line 655

**Add method:**
```python
def _validate_calculation_result(self, ticker: str, metric: str, result: float, inputs: Dict[str, Fact]) -> List[str]:
    """Validate calculation makes business sense"""
    flags = []

    # Check 1: Gross profit shouldn't exceed revenue
    if metric == "grossProfit":
        revenue = inputs.get("revenue")
        if revenue and result > revenue.value:
            flags.append("INVALID_GROSS_PROFIT_EXCEEDS_REVENUE")

    # Check 2: COGS should be positive
    if "costOfRevenue" in inputs:
        cogs = inputs["costOfRevenue"].value
        if cogs < 0:
            flags.append("NEGATIVE_COGS")

    # Check 3: Data freshness
    for name, fact in inputs.items():
        if fact.period:
            year = int(fact.period.split("-")[0])
            current_year = 2025  # TODO: Use datetime.now().year
            if current_year - year > 2:
                flags.append(f"OLD_DATA_{name}_{fact.period}")

    return flags
```

**Integration Point:**
- Call in `calculate_metric()` after line 167
- Call in `explain_expression()` after line 256

**Acceptance Criteria:**
- RH period mismatch detected
- ULTA old data flagged
- Negative values caught

### Task 1.3: Better Error Messages (1 hour)
**File:** `src/routes/finance_calc.py`
**Lines:** 126-131, 310-316

**Current:**
```python
return create_problem_response(
    request, 422,
    "validation-error",
    "Calculation failed",
    str(e)
)
```

**New:**
```python
# Parse common errors
error_msg = str(e)
if "Unsafe expression" in error_msg:
    detail = f"Expression validation failed. Check for typos in: {req.expr}"
elif "not found" in error_msg.lower():
    detail = f"Metric '{metric}' not available for {ticker}. Try alternative metrics."
else:
    detail = error_msg

return create_problem_response(
    request, 422,
    "validation-error",
    "Calculation failed",
    detail,
    {"available_metrics": kpi_registry.list_metrics()[:10]}  # Hint
)
```

**Acceptance Criteria:**
- RH error clearly states the issue
- Helpful suggestions included

---

## 🔄 Phase 2: Cross-Source Validation (Day 1-2) - COPILOT
**Objective:** Add trust scores, detect discrepancies
**Owner:** GitHub Copilot (GPT-5 Codex)
**Time Estimate:** 6 hours

### Task 2.1: Create Validation Service (2 hours)
**File:** `src/services/data_validator.py` (NEW FILE)

**Copilot Instructions:**
```
Create a new service that compares financial data across sources.

Requirements:
1. Class: DataValidator
2. Method: async def cross_validate(ticker: str, metric: str, period: str) -> ValidationResult
3. Fetch same metric from SEC, Yahoo, Alpha Vantage
4. Compare values, flag if >10% difference
5. Return ValidationResult with:
   - trust_score: float (0-100)
   - sources_count: int
   - discrepancies: List[str]
   - consensus_value: float (median)

Use existing adapters:
- src/adapters/sec_facts.py
- src/adapters/yahoo_finance_direct.py
- src/adapters/alpha_vantage.py

Model after src/services/definitive_router.py pattern.
```

**Acceptance Criteria:**
- Can fetch from 3 sources
- Calculates trust score
- Returns ValidationResult dataclass

### Task 2.2: Integrate Validation into Engine (2 hours)
**File:** `src/calc/engine.py`

**Copilot Instructions:**
```
Integrate DataValidator into CalculationEngine.

Add to __init__:
    self.validator = DataValidator()

Add optional parameter to calculate_metric():
    validate: bool = False

If validate=True:
    1. Get result normally
    2. Call self.validator.cross_validate(ticker, metric, period)
    3. Add validation result to metadata
    4. Add trust_score to response

Return enhanced CalculationResult with validation field.
```

**Acceptance Criteria:**
- `/calc/{ticker}/{metric}?validate=true` works
- Trust score in response
- No breaking changes to existing API

### Task 2.3: Add Validation Endpoint (2 hours)
**File:** `src/routes/finance_calc.py`

**Copilot Instructions:**
```
Add new endpoint: POST /v1/finance/calc/validate

Request body:
{
  "ticker": "AAPL",
  "metric": "grossProfit",
  "period": "latest"
}

Response:
{
  "ticker": "AAPL",
  "metric": "grossProfit",
  "trust_score": 95.0,
  "sources": [
    {"source": "sec_edgar", "value": 100000000, "period": "2025-Q2"},
    {"source": "yahoo_finance", "value": 98000000, "period": "2025-Q2"},
    {"source": "alpha_vantage", "value": 99000000, "period": "2025-Q2"}
  ],
  "consensus_value": 99000000,
  "discrepancies": [],
  "validation_time": "2025-10-03T10:00:00Z"
}

Use DataValidator from Task 2.1.
Model after /explain endpoint pattern.
```

**Acceptance Criteria:**
- Endpoint works
- Returns data from multiple sources
- Trust score calculated correctly

---

## 🗺️ Phase 3: Better Concept Mapping (Day 2) - CLAUDE
**Objective:** Handle XBRL variations, fix RH issue
**Owner:** Claude Code (me)
**Time Estimate:** 3 hours

### Task 3.1: Expand Concept Map (2 hours)
**File:** `src/adapters/sec_facts.py`
**Lines:** 128-147 (CONCEPT_MAP)

**Current issues:**
- RH uses different revenue concept
- Some companies report under us-gaap vs dei vs company-specific

**Add to CONCEPT_MAP:**
```python
# Revenue variations
"revenue": [
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:Revenues",
    "us-gaap:SalesRevenueNet",
    "us-gaap:SalesRevenueGoodsNet",
    "us-gaap:SalesRevenueServicesNet",
    "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
],

# COGS variations
"costOfRevenue": [
    "us-gaap:CostOfRevenue",
    "us-gaap:CostOfGoodsAndServicesSold",
    "us-gaap:CostOfGoodsSold",
    "us-gaap:CostOfServicesSold",
],

# Add 20+ more standard metrics
```

**Acceptance Criteria:**
- RH revenue found correctly
- Test with 20 diverse tickers
- No more "concept not found" errors

### Task 3.2: Fallback Logic (1 hour)
**File:** `src/adapters/sec_facts.py`
**Method:** `get_fact()` around line 262

**Add cascading fallback:**
```python
async def get_fact(self, ticker: str, concept: str, **kwargs):
    # Try primary concept
    result = await self._fetch_fact(ticker, concept, **kwargs)
    if result:
        return result

    # Try alternatives from CONCEPT_MAP
    alternatives = self.CONCEPT_MAP.get(concept, [])
    for alt_concept in alternatives:
        result = await self._fetch_fact(ticker, alt_concept, **kwargs)
        if result:
            result["quality_flags"].append(f"FALLBACK_CONCEPT_{alt_concept}")
            return result

    raise ValueError(f"Concept '{concept}' not found for {ticker}")
```

**Acceptance Criteria:**
- RH works
- Quality flag shows when fallback used
- 85% → 92% pass rate

---

## 📊 Phase 4: Quality Dashboard (Day 2) - COPILOT
**Objective:** Transparency dashboard showing system health
**Owner:** GitHub Copilot (GPT-5 Codex)
**Time Estimate:** 4 hours

### Task 4.1: Create Dashboard Endpoint (2 hours)
**File:** `src/routes/finance_status.py`

**Copilot Instructions:**
```
Add endpoint: GET /v1/finance/status/quality

Returns system-wide quality metrics:

{
  "overall_pass_rate": 0.92,
  "total_tickers_tested": 20,
  "last_test_run": "2025-10-03T10:00:00Z",
  "by_ticker": [
    {
      "ticker": "AAPL",
      "pass_rate": 1.0,
      "data_freshness": "2025-Q3",
      "quality_flags": []
    },
    ...
  ],
  "by_industry": {
    "Semiconductors": {"pass_rate": 1.0, "count": 6},
    "Footwear": {"pass_rate": 1.0, "count": 4},
    ...
  },
  "common_issues": [
    {"issue": "rate_limit", "count": 0},
    {"issue": "old_data", "count": 2},
    ...
  ]
}

Parse stress_test_results.json for data.
Add caching (Redis if available, else in-memory).
```

**Acceptance Criteria:**
- Endpoint returns quality metrics
- Caching works (5min TTL)
- JSON format matches spec

### Task 4.2: Add per-Ticker Quality Endpoint (2 hours)
**File:** `src/routes/finance_calc.py`

**Copilot Instructions:**
```
Add endpoint: GET /v1/finance/calc/{ticker}/quality

Returns quality metrics for specific ticker:

{
  "ticker": "AAPL",
  "overall_score": 95,
  "data_coverage": {
    "revenue": {"available": true, "freshness": "2025-Q3", "sources": 3},
    "grossProfit": {"available": true, "freshness": "2025-Q3", "sources": 3},
    "netIncome": {"available": true, "freshness": "2025-Q3", "sources": 2}
  },
  "data_freshness": {
    "latest_filing": "2025-Q3",
    "filing_date": "2025-08-03",
    "days_old": 60
  },
  "known_issues": [],
  "trust_level": "high"
}

Call SEC adapter to check available concepts.
Check filing dates.
Calculate freshness score.
```

**Acceptance Criteria:**
- Works for all test tickers
- Shows data coverage
- Trust level accurate

---

## 📈 Phase 5: Historical Time Series (Day 3) - COPILOT
**Objective:** 10-year historical data
**Owner:** GitHub Copilot (GPT-5 Codex)
**Time Estimate:** 6 hours

### Task 5.1: Enhance Series Endpoint (3 hours)
**File:** `src/routes/finance_calc.py`
**Current:** `/series/{ticker}/{metric}` (lines 148-221)

**Copilot Instructions:**
```
Enhance existing /series endpoint:

Current limitations:
- Only returns limited periods
- No date range filtering
- No TTM support

Add query parameters:
- start_date: str = "2015-01-01"
- end_date: str = "2025-12-31"
- ttm: bool = False
- fill_missing: bool = False (interpolate gaps)

Return:
{
  "ticker": "AAPL",
  "metric": "revenue",
  "freq": "Q",
  "start_date": "2015-Q1",
  "end_date": "2025-Q3",
  "series": [
    {
      "period": "2015-Q1",
      "value": 58000000000,
      "date": "2015-03-31",
      "accession": "...",
      "quality_flags": []
    },
    ...
  ],
  "stats": {
    "count": 43,
    "mean": 75000000000,
    "median": 72000000000,
    "growth_rate": 0.15,  # CAGR
    "volatility": 0.08
  }
}

Use existing facts_store.get_series() as base.
Add statistical calculations.
```

**Acceptance Criteria:**
- Returns 10 years of data
- Statistics calculated correctly
- TTM calculation works

### Task 5.2: Add Comparison Endpoint (3 hours)
**File:** `src/routes/finance_calc.py` (NEW)

**Copilot Instructions:**
```
Create new endpoint: POST /v1/finance/calc/compare

Request:
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "metric": "revenue",
  "start_date": "2020-Q1",
  "end_date": "2025-Q3",
  "normalize": true  // Normalize to 100 at start
}

Response:
{
  "metric": "revenue",
  "period": "2020-Q1 to 2025-Q3",
  "series": {
    "AAPL": [...],
    "MSFT": [...],
    "GOOGL": [...]
  },
  "normalized": true,
  "stats": {
    "AAPL": {"growth": 0.15, "volatility": 0.08},
    "MSFT": {"growth": 0.18, "volatility": 0.06},
    "GOOGL": {"growth": 0.12, "volatility": 0.10}
  }
}

Use /series endpoint internally.
Add normalization logic.
Calculate comparative stats.
```

**Acceptance Criteria:**
- Compare up to 10 tickers
- Normalization works
- Returns aligned time periods

---

## 🧪 Phase 6: Testing & Validation (Day 3) - CLAUDE
**Objective:** Comprehensive testing, 95%+ reliability
**Owner:** Claude Code (me)
**Time Estimate:** 4 hours

### Task 6.1: Expand Stress Test (2 hours)
**File:** `stress_test_diverse_tickers.py`

**Additions:**
- 40 tickers (20 → 40)
- Include international: TSM, BABA, SAP, ASML
- Test all new endpoints: /validate, /quality, /series
- Test edge cases: crypto, penny stocks, recently IPOd

**Acceptance Criteria:**
- 95%+ pass rate on 40 tickers
- All new endpoints tested
- Results documented

### Task 6.2: Add Unit Tests (2 hours)
**File:** `tests/test_validation.py` (NEW)

**Test coverage:**
- Sanity checks function
- Concept mapping fallbacks
- Cross-source validation
- Quality score calculation
- Time series statistics

**Acceptance Criteria:**
- 80%+ code coverage
- All critical paths tested
- CI/CD ready

---

## 📝 Phase 7: Documentation (Day 3-4) - SHARED
**Objective:** Production-ready docs
**Time Estimate:** 4 hours

### Task 7.1: API Documentation (2 hours) - COPILOT
**File:** `docs/API_REFERENCE.md`

**Copilot Instructions:**
```
Create comprehensive API documentation:

Sections:
1. Authentication (API keys)
2. Rate Limits (per tier)
3. All endpoints with examples
4. Response formats
5. Error codes
6. Quality flags glossary
7. Best practices
8. Code examples (Python, JavaScript, cURL)

Format: Markdown
Style: Clear, concise, example-heavy
```

### Task 7.2: Quality & Reliability Guide (2 hours) - CLAUDE
**File:** `docs/DATA_QUALITY.md`

**Content:**
- How citations work
- Quality flag meanings
- When to use validation
- Data freshness expectations
- Known limitations
- Troubleshooting guide

---

## 🚢 Phase 8: Deployment Prep (Day 4) - CLAUDE
**Objective:** Production-ready configuration
**Time Estimate:** 3 hours

### Task 8.1: Environment Configuration
**Files:**
- `src/config/settings.py`
- `.env.production.template`
- `docker-compose.prod.yml`

**Add:**
- Production rate limits
- API key tiers (free, pro, enterprise)
- Monitoring endpoints
- Health checks
- Graceful shutdown

### Task 8.2: Monitoring & Alerting
**File:** `src/middleware/monitoring.py`

**Add:**
- Request success rate tracking
- Response time percentiles
- Error rate alerts
- Data quality metrics
- Usage by API key

---

## ✅ Acceptance Criteria - Overall

### Phase 1-3 (Day 1-2):
- ✅ 92%+ pass rate on stress test
- ✅ All sanity checks implemented
- ✅ Cross-source validation working
- ✅ Better error messages

### Phase 4-5 (Day 2-3):
- ✅ Quality dashboard live
- ✅ Historical data (10 years)
- ✅ Comparison endpoint working

### Phase 6-7 (Day 3-4):
- ✅ 95%+ pass rate on expanded test
- ✅ 80%+ code coverage
- ✅ Complete documentation

### Phase 8 (Day 4):
- ✅ Production config ready
- ✅ Monitoring in place
- ✅ Ready for monetization

---

## 🎯 Success Metrics

**Quantitative:**
- Pass rate: 95%+ (currently 69%)
- Response time: <1s (currently 895ms) ✅
- Uptime: 99.9%
- API coverage: 100% documented

**Qualitative:**
- Users trust the data
- Citations are clear
- Error messages are helpful
- Dashboard provides transparency

---

## 🔄 Task Assignments Summary

### Claude (Me):
- Phase 1: Quick wins (rate limiting, sanity checks)
- Phase 3: Concept mapping improvements
- Phase 6: Testing & validation
- Phase 7.2: Data quality documentation
- Phase 8: Deployment prep

### Copilot (GPT-5):
- Phase 2: Cross-source validation service
- Phase 4: Quality dashboard
- Phase 5: Historical time series
- Phase 7.1: API documentation

**Coordination:**
- Claude commits after each phase
- Copilot reads git log for context
- Use separate branches if needed
- No concurrent edits to same files

---

## 🚀 Execution Order

1. **Claude:** Phase 1 (4 hours) → Commit
2. **Copilot:** Phase 2 (6 hours) → Commit
3. **Claude:** Phase 3 (3 hours) → Commit
4. **Copilot:** Phase 4 (4 hours) → Commit
5. **Copilot:** Phase 5 (6 hours) → Commit
6. **Claude:** Phase 6 (4 hours) → Commit
7. **Both:** Phase 7 (4 hours) → Commit
8. **Claude:** Phase 8 (3 hours) → Final commit

**Total Time:** ~34 hours (~4 days with breaks)

---

**Last Updated:** 2025-10-03
**Status:** Ready to execute
**Next Action:** Claude starts Phase 1
