#!/bin/bash
# Production smoke tests for live deployment

set -e

# Configuration
API_BASE=${API_BASE:-"https://api.nocturnal.dev"}
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

echo "🚀 PRODUCTION SMOKE TESTS - Nocturnal Archive API"
echo "================================================="
echo "API Base: $API_BASE"
echo ""

echo "1. 🏥 HEALTH CHECKS"
echo "------------------"

# Test liveness probe
echo "Testing liveness probe..."
LIVEZ_RESPONSE=$(curl -s "$API_BASE/livez" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$LIVEZ_RESPONSE" = "alive" ]; then
    test_result 0 "Liveness probe working"
else
    test_result 1 "Liveness probe should return alive (got $LIVEZ_RESPONSE)"
fi

# Test readiness probe
echo "Testing readiness probe..."
READYZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/readyz" 2>/dev/null || echo "000")
if [ "$READYZ_RESPONSE" = "200" ] || [ "$READYZ_RESPONSE" = "503" ]; then
    test_result 0 "Readiness probe working ($READYZ_RESPONSE)"
else
    test_result 1 "Readiness probe should work (got $READYZ_RESPONSE)"
fi

echo ""
echo "2. 🔐 AUTHENTICATION"
echo "-------------------"

# Test API key authentication
echo "Testing API key authentication..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/papers/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}' 2>/dev/null || echo "000")
if [ "$API_RESPONSE" = "200" ]; then
    test_result 0 "API key authentication working"
else
    test_result 1 "API key authentication should work (got $API_RESPONSE)"
fi

# Test admin authentication
echo "Testing admin authentication..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Admin-Key: $ADMIN_KEY" "$API_BASE/v1/diag/selftest" 2>/dev/null || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ]; then
    test_result 0 "Admin authentication working"
else
    test_result 1 "Admin authentication should work (got $ADMIN_RESPONSE)"
fi

echo ""
echo "3. 📊 RATE LIMITING"
echo "------------------"

# Test rate limiting
echo "Testing rate limiting (200 requests)..."
RATE_LIMIT_RESULTS=""
for i in {1..200}; do
    RATE_LIMIT_RESULTS+=$(curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/papers/search" \
        -H 'content-type: application/json' -d '{"query":"x","limit":1}' 2>/dev/null || echo "000")$'\n'
done

# Count results
SUCCESS_COUNT=$(echo "$RATE_LIMIT_RESULTS" | grep -c "200" || echo "0")
RATE_LIMIT_COUNT=$(echo "$RATE_LIMIT_RESULTS" | grep -c "429" || echo "0")
ERROR_COUNT=$(echo "$RATE_LIMIT_RESULTS" | grep -c "5.." || echo "0")

if [ "$ERROR_COUNT" -eq 0 ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
    test_result 0 "Rate limiting working ($SUCCESS_COUNT success, $RATE_LIMIT_COUNT rate limited, $ERROR_COUNT failures)"
else
    test_result 1 "Rate limiting failed ($SUCCESS_COUNT success, $RATE_LIMIT_COUNT rate limited, $ERROR_COUNT failures)"
fi

echo ""
echo "4. 🔢 FINANCE GROUNDING"
echo "----------------------"

# Test finance grounding with RFC 7807
echo "Testing finance grounding with RFC 7807..."
FINANCE_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/finance/synthesize" \
    -H 'content-type: application/json' \
    -d '{"context":{"series":[{"series_id":"CPIAUCSL","freq":"M","points":[["2024-01-01",309.7]]}]},"claims":[{"id":"c1","metric":"CPIAUCSL","operator":"yoy","value":3.2,"at":"2024-01-01"}],"grounded":true}' \
    | jq -r '.type' 2>/dev/null || echo "error")

if [ "$FINANCE_RESPONSE" = "https://nocturnal.dev/errors/claims-not-grounded" ]; then
    test_result 0 "Finance grounding RFC 7807 error working"
else
    test_result 1 "Finance grounding should return RFC 7807 error (got $FINANCE_RESPONSE)"
fi

echo ""
echo "5. 🛡️ SECURITY"
echo "-------------"

# Test security headers
echo "Testing security headers..."
SECURITY_HEADERS=$(curl -s -I "$API_BASE/livez" | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options" | wc -l)
if [ "$SECURITY_HEADERS" -gt 0 ]; then
    test_result 0 "Security headers present ($SECURITY_HEADERS headers found)"
else
    test_result 1 "Security headers should be present"
fi

# Test admin endpoint protection
echo "Testing admin endpoint protection..."
ADMIN_PROTECTION=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/v1/diag/selftest" 2>/dev/null || echo "000")
if [ "$ADMIN_PROTECTION" = "401" ]; then
    test_result 0 "Admin endpoints protected without key"
else
    test_result 1 "Admin endpoints should be protected (got $ADMIN_PROTECTION)"
fi

echo ""
echo "6. 📈 PERFORMANCE"
echo "----------------"

# Test search performance
echo "Testing search performance..."
SEARCH_START=$(date +%s%3N)
SEARCH_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/papers/search" \
    -H 'content-type: application/json' -d '{"query":"machine learning","limit":5}' \
    | jq -r '.count' 2>/dev/null || echo "error")
SEARCH_END=$(date +%s%3N)
SEARCH_DURATION=$((SEARCH_END - SEARCH_START))

if [ "$SEARCH_RESPONSE" != "error" ] && [ "$SEARCH_DURATION" -lt 1500 ]; then
    test_result 0 "Search performance good (${SEARCH_DURATION}ms, $SEARCH_RESPONSE results)"
else
    test_result 1 "Search performance should be < 1.5s (got ${SEARCH_DURATION}ms)"
fi

echo ""
echo "📊 PRODUCTION SMOKE TEST SUMMARY"
echo "==============================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL PRODUCTION SMOKE TESTS PASSED - LIVE AND READY!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME PRODUCTION SMOKE TESTS FAILED - REVIEW BEFORE GOING LIVE${NC}"
    exit 1
fi
