# FinSight Production Flip Checklist

## Pre-Flip Verification

### ✅ Completed Fixes
- [x] **Strict Mode Enforcement**: `FINSIGHT_STRICT=1` hard-fails on mock/demo data
- [x] **FX Provenance**: ECB SDW source with dataset, date, rate, method details
- [x] **XBRL Segments**: Dimension/member qnames in segment citations
- [x] **Real PDF Generation**: ReportLab-based reports >50KB with tables/citations
- [x] **CIK Corrections**: Updated SAP (0001000184), ASML (0000931825), SHEL (0001306965)
- [x] **Real IFRS Sources**: TSM, SAP, ASML, SHEL all have real SEC CIKs

### 🔍 Go/No-Go Battery
Run: `./go_no_go_battery.sh`

**PASS Criteria:**
- A) ASML fails with RFC7807 error in strict mode
- B) AAPL math residual = 0, real SEC accessions, sec.gov URLs
- C) TSM/SAP return ifrs-full taxonomy with ECB fx_used provenance
- D) AAPL segments have XBRL dimension/member qnames
- E) PDF >50KB, proper PDF document format

## Production Flip Steps

### 1. Prime Live Cache
```bash
# Ensure cache warming calls live adapters (strict mode OFF for caching)
bash scripts/prime_cache.sh
```

### 2. Security & Compliance
- [ ] **Rotate API Keys**: Generate new admin + demo keys
- [ ] **Set SEC User-Agent**: `FinSight Financial Data (contact@nocturnal.dev)`
- [ ] **Enable Rate Limiting**: 1-2 req/sec for EDGAR compliance
- [ ] **IP Allowlisting**: Admin surfaces restricted to known IPs

### 3. Production Environment
- [ ] **Enable Strict Mode**: `FINSIGHT_STRICT=1` in production
- [ ] **SSL/TLS**: HTTPS termination with valid certificates
- [ ] **Security Headers**: HSTS, CSP, X-Frame-Options
- [ ] **Monitoring**: Prometheus metrics, alerting rules

### 4. SLO Monitoring
- [ ] **Cache Performance**: p95 ≤ 350ms for cached responses
- [ ] **EDGAR Fetch**: p95 ≤ 1.5s for SEC data retrieval
- [ ] **Error Rate**: 5xx ≤ 0.1% of total requests
- [ ] **Availability**: 99.9% uptime target

### 5. Documentation & Demo
- [ ] **README Update**: 3-curl demo using only real tickers (AAPL, TSM, SAP)
- [ ] **API Documentation**: OpenAPI spec with real examples
- [ ] **Error Catalog**: RFC7807 problem types documented
- [ ] **Postman Collection**: Updated with real endpoints

## Post-Flip Validation

### 6. Smoke Tests
```bash
# Run production smoke tests
bash scripts/production_smoke.sh
```

### 7. Monitoring Verification
- [ ] **Health Endpoints**: `/health` and `/v1/finance/status` responding
- [ ] **Metrics Collection**: Prometheus scraping successfully
- [ ] **Log Aggregation**: Structured logs flowing to monitoring
- [ ] **Alert Rules**: Test alerting on simulated failures

### 8. Beta Launch
- [ ] **Paid Beta Access**: Enable billing for real customers
- [ ] **Issuer Coverage**: US GAAP + 2 IFRS issuers (TSM, SAP)
- [ ] **Rate Limits**: Production quotas per API key
- [ ] **Support Channels**: Customer support workflows active

## Rollback Plan

If issues arise:
```bash
# One-liner rollback
bash deploy/rollback.sh
```

## Success Metrics

### Week 1 Targets
- [ ] **Customer Adoption**: 10+ beta customers
- [ ] **API Usage**: 1000+ requests/day
- [ ] **Data Quality**: <1% error rate on real data
- [ ] **Performance**: 95% requests <500ms

### Expansion Plan
- [ ] **Weekly Issuer Additions**: 2-3 new tickers per week
- [ ] **Feature Rollout**: Segments, advanced calculations
- [ ] **Data Sources**: Additional regulatory feeds
- [ ] **Enterprise Features**: Custom calculations, bulk exports

---

**Status**: Ready for production flip if Go/No-Go battery passes
**Next Action**: Run `./go_no_go_battery.sh` and proceed with flip if all tests pass
