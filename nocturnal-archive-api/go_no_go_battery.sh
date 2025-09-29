#!/bin/bash
# Go/No-Go Battery for FinSight Production Readiness
# Run this script to verify all systems are production-ready

set -e

echo "=== FinSight Go/No-Go Battery ==="
echo "Goal: Prove strict mode = real data only, IFRS + FX are truly sourced, segments carry XBRL dimensions, PDF isn't a stub"
echo ""

API_BASE="http://localhost:8000"
API_KEY="demo-key-123"

# Test A: Strict mode truly strict
echo "A) Testing strict mode with ASML (should fail):"
export FINSIGHT_STRICT=1
curl -s -H "X-API-Key:$API_KEY" -H "Content-Type: application/json" \
  -X POST "$API_BASE/v1/finance/calc/explain" \
  -d '{"ticker":"ASML","expr":"revenue - costOfRevenue","period":"latest","freq":"Q"}' \
| jq -r '.type, .detail'
echo ""

# Test B: US-GAAP identity (AAPL) - accessions + math
echo "B) Testing AAPL US-GAAP with real accessions:"
curl -s -H "X-API-Key:$API_KEY" -H "Content-Type: application/json" \
  -X POST "$API_BASE/v1/finance/calc/explain" \
  -d '{"ticker":"AAPL","expr":"grossProfit = revenue - costOfRevenue","period":"latest","freq":"Q"}' \
| jq '{
  residual: ((.right.terms[0].value - .right.terms[1].value) - .left.value),
  accs: [.left.accession, .right.terms[0].accession, .right.terms[1].accession],
  cites: [.citations[]?.url]
}'
echo ""

# Test C: IFRS + FX (TSM)
echo "C) Testing TSM IFRS + FX with ECB provenance:"
curl -s -H "X-API-Key:$API_KEY" \
  "$API_BASE/v1/finance/calc/series/TSM/revenue?freq=Q&limit=1" \
| jq '.series[0] | {
      taxonomy: .citation.taxonomy,
      unit: .citation.unit,
      fx_used: .citation.fx_used
    }'
echo ""

# Test C2: IFRS + FX (SAP)
echo "C2) Testing SAP IFRS + FX with ECB provenance:"
curl -s -H "X-API-Key:$API_KEY" \
  "$API_BASE/v1/finance/calc/series/SAP/revenue?freq=Q&limit=1" \
| jq '.series[0] | {
      taxonomy: .citation.taxonomy,
      unit: .citation.unit,
      fx_used: .citation.fx_used
    }'
echo ""

# Test D: Segments carry XBRL dimensions (AAPL)
echo "D) Testing AAPL segments with XBRL dimensions:"
curl -s -H "X-API-Key:$API_KEY" \
  "$API_BASE/v1/finance/segments/AAPL/revenue?dim=Geography&freq=Q&limit=4" \
| jq '.series[0].points[0].citation | {dimension, member, url}'
echo ""

# Test E: PDF is a real report
echo "E) Testing PDF generation:"
curl -s -H "X-API-Key:$API_KEY" \
  -o AAPL-2024Q4.pdf \
  "$API_BASE/v1/finance/reports/AAPL/2024-Q4.pdf"
echo "PDF size: $(ls -lh AAPL-2024Q4.pdf | awk '{print $5}')"
echo "File type: $(file AAPL-2024Q4.pdf)"
echo ""

echo "=== PASS/FAIL CRITERIA ==="
echo "A) PASS if: Returns RFC7807 error with 'unsupported_foreign_issuer' or similar"
echo "B) PASS if: residual == 0, accessions match ^\d{10}-\d{2}-\d{6}$, cites are sec.gov URLs"
echo "C) PASS if: taxonomy is 'ifrs-full', fx_used has ECB provenance, no 'demo' source"
echo "D) PASS if: dimension/member are XBRL qnames, URL points to sec.gov filing"
echo "E) PASS if: PDF size > 50KB, file reports 'PDF document, version 1.x'"
echo ""
echo "If all tests PASS → Ready for production flip"
echo "If any test FAILS → Fix before production deployment"
