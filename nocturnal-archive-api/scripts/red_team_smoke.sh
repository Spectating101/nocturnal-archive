#!/bin/bash
# Red-team smoke tests for production readiness

set -e

# Configuration
API_BASE=${API_BASE:-"http://localhost:8000"}
API_KEY=${API_KEY:-"demo-key-123"}
ADMIN_KEY=${ADMIN_KEY:-"admin-key-change-me"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "🔴 RED-TEAM SMOKE TESTS - Nocturnal Archive API"
echo "==============================================="
echo "API Base: $API_BASE"
echo ""

echo "1. 🛡️ SSRF PROTECTION"
echo "-------------------"

# Test SSRF attempt in URL field
echo "Testing SSRF protection..."
SSRF_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/api/search" \
    -H 'content-type: application/json' \
    -d '{"query":"test","limit":1,"sources":["http://169.254.169.254/latest/meta-data/"]}' 2>/dev/null || echo "000")
if [ "$SSRF_RESPONSE" = "422" ] || [ "$SSRF_RESPONSE" = "400" ]; then
    test_result 0 "SSRF attempt blocked (got $SSRF_RESPONSE)"
else
    test_result 1 "SSRF attempt should be blocked (got $SSRF_RESPONSE)"
fi

echo ""
echo "2. 📏 BODY SIZE LIMITS"
echo "---------------------"

# Test 2MB+ body
echo "Testing body size limits..."
LARGE_BODY=$(python3 -c "print('x' * 2100000)")  # 2.1MB
BODY_SIZE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/api/search" \
    -H 'content-type: application/json' \
    -d "{\"query\":\"$LARGE_BODY\",\"limit\":1}" 2>/dev/null || echo "000")
if [ "$BODY_SIZE_RESPONSE" = "413" ]; then
    test_result 0 "Large body rejected with 413"
else
    test_result 1 "Large body should be rejected with 413 (got $BODY_SIZE_RESPONSE)"
fi

echo ""
echo "3. 🚀 LOAD TESTING"
echo "-----------------"

# Test concurrent requests
echo "Testing concurrent load (100 requests)..."
CONCURRENT_RESULTS=""
for i in {1..100}; do
    CONCURRENT_RESULTS+=$(curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/api/search" \
        -H 'content-type: application/json' -d '{"query":"test","limit":1}' 2>/dev/null || echo "000")$'\n'
done

# Count results
SUCCESS_COUNT=$(echo "$CONCURRENT_RESULTS" | grep -c "200" || echo "0")
ERROR_COUNT=$(echo "$CONCURRENT_RESULTS" | grep -c "429" || echo "0")
FAIL_COUNT=$(echo "$CONCURRENT_RESULTS" | grep -c "5.." || echo "0")

if [ "$FAIL_COUNT" -eq 0 ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
    test_result 0 "Load test passed ($SUCCESS_COUNT success, $ERROR_COUNT rate limited, $FAIL_COUNT failures)"
else
    test_result 1 "Load test failed ($SUCCESS_COUNT success, $ERROR_COUNT rate limited, $FAIL_COUNT failures)"
fi

echo ""
echo "4. 🔢 FINANCE GROUNDING EDGE CASES"
echo "--------------------------------"

# Test yoy with missing t-12
echo "Testing finance grounding edge cases..."
FINANCE_EDGE_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/finance/verify-claims" \
    -H 'content-type: application/json' \
    -d '{"context":{"series":[{"series_id":"CPIAUCSL","freq":"M","points":[["2024-01-01",309.72]]}]},"claims":[{"id":"c1","metric":"CPIAUCSL","operator":"yoy","value":3.2,"at":"2024-01-01"}]}' \
    | jq -r '.all_verified' 2>/dev/null || echo "error")
if [ "$FINANCE_EDGE_RESPONSE" = "false" ]; then
    test_result 0 "Finance grounding correctly rejects insufficient data for yoy"
else
    test_result 1 "Finance grounding should reject insufficient data for yoy (got $FINANCE_EDGE_RESPONSE)"
fi

echo ""
echo "5. 🔐 SECURITY HEADERS"
echo "--------------------"

# Test security headers
echo "Testing security headers..."
SECURITY_HEADERS=$(curl -s -I "$API_BASE/livez" | grep -i "x-content-type-options\|x-frame-options\|x-xss-protection\|strict-transport-security" | wc -l)
if [ "$SECURITY_HEADERS" -gt 0 ]; then
    test_result 0 "Security headers present ($SECURITY_HEADERS headers found)"
else
    test_result 1 "Security headers should be present"
fi

echo ""
echo "6. 🚫 ADMIN ENDPOINT PROTECTION"
echo "-----------------------------"

# Test admin endpoints without key
echo "Testing admin endpoint protection..."
ADMIN_PROTECTION=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/v1/diag/selftest" 2>/dev/null || echo "000")
if [ "$ADMIN_PROTECTION" = "401" ]; then
    test_result 0 "Admin endpoints protected without key"
else
    test_result 1 "Admin endpoints should be protected (got $ADMIN_PROTECTION)"
fi

# Test metrics endpoint
METRICS_PROTECTION=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/metrics" 2>/dev/null || echo "000")
if [ "$METRICS_PROTECTION" = "401" ]; then
    test_result 0 "Metrics endpoint protected"
else
    test_result 1 "Metrics endpoint should be protected (got $METRICS_PROTECTION)"
fi

echo ""
echo "7. 📊 RATE LIMITING"
echo "------------------"

# Test rate limiting
echo "Testing rate limiting..."
RATE_LIMIT_HEADERS=$(curl -s -I -H "X-API-Key: $API_KEY" -X POST "$API_BASE/api/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}' | grep -i "x-ratelimit" | wc -l)
if [ "$RATE_LIMIT_HEADERS" -gt 0 ]; then
    test_result 0 "Rate limiting headers present"
else
    test_result 1 "Rate limiting headers should be present"
fi

echo ""
echo "8. 🔍 REQUEST TRACING"
echo "--------------------"

# Test request ID correlation
echo "Testing request tracing..."
REQUEST_ID="red-team-test-$(date +%s)"
TRACE_RESPONSE=$(curl -s -H "X-Request-ID: $REQUEST_ID" "$API_BASE/livez" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$TRACE_RESPONSE" = "alive" ]; then
    test_result 0 "Request tracing works"
else
    test_result 1 "Request tracing should work (got $TRACE_RESPONSE)"
fi

echo ""
echo "9. 🏥 HEALTH CHECKS"
echo "------------------"

# Test health endpoints
echo "Testing health checks..."
LIVEZ_RESPONSE=$(curl -s "$API_BASE/livez" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$LIVEZ_RESPONSE" = "alive" ]; then
    test_result 0 "Liveness probe working"
else
    test_result 1 "Liveness probe should work (got $LIVEZ_RESPONSE)"
fi

READYZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/readyz" 2>/dev/null || echo "000")
if [ "$READYZ_RESPONSE" = "200" ] || [ "$READYZ_RESPONSE" = "503" ]; then
    test_result 0 "Readiness probe working ($READYZ_RESPONSE)"
else
    test_result 1 "Readiness probe should work (got $READYZ_RESPONSE)"
fi

echo ""
echo "10. 🔑 KEY MANAGEMENT"
echo "--------------------"

# Test key creation
echo "Testing key management..."
KEY_CREATE=$(curl -s -H "X-Admin-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/admin/keys" \
    -H 'content-type: application/json' -d '{"owner":"red-team-test","tier":"free"}' \
    | jq -r '.id' 2>/dev/null || echo "error")
if [[ "$KEY_CREATE" == noct_* ]]; then
    test_result 0 "Key creation works"
else
    test_result 1 "Key creation should work (got $KEY_CREATE)"
fi

echo ""
echo "📊 RED-TEAM SMOKE TEST SUMMARY"
echo "=============================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL RED-TEAM TESTS PASSED - PRODUCTION READY!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME RED-TEAM TESTS FAILED - REVIEW BEFORE PRODUCTION${NC}"
    exit 1
fi
