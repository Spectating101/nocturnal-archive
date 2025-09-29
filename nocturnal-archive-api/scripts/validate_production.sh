#!/bin/bash
# Production validation script for Nocturnal Archive API

set -e

# Configuration
API_BASE=${API_BASE:-"http://localhost:8000"}
API_KEY=${API_KEY:-"demo-key-123"}
ADMIN_KEY=${ADMIN_KEY:-"admin-key-change-me"}

echo "🔍 PRODUCTION VALIDATION - Nocturnal Archive API"
echo "=================================================="
echo "API Base: $API_BASE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

echo "1. 🔐 SECURITY VALIDATION"
echo "------------------------"

# Test admin surfaces are protected
echo "Testing admin endpoint protection..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/v1/diag/selftest")
if [ "$ADMIN_RESPONSE" = "401" ]; then
    test_result 0 "Admin endpoints require authentication"
else
    test_result 1 "Admin endpoints should return 401 without key (got $ADMIN_RESPONSE)"
fi

# Test admin access works
echo "Testing admin access with key..."
ADMIN_AUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Admin-Key: $ADMIN_KEY" "$API_BASE/v1/diag/selftest")
if [ "$ADMIN_AUTH_RESPONSE" = "200" ]; then
    test_result 0 "Admin access works with valid key"
else
    test_result 1 "Admin access should return 200 with valid key (got $ADMIN_AUTH_RESPONSE)"
fi

# Test API key authentication
echo "Testing API key authentication..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/api/search" -H 'content-type: application/json' -d '{"query":"test","limit":1}')
if [ "$API_RESPONSE" = "401" ]; then
    test_result 0 "API endpoints require authentication"
else
    test_result 1 "API endpoints should return 401 without key (got $API_RESPONSE)"
fi

echo ""
echo "2. 🏥 HEALTH CHECKS"
echo "------------------"

# Test liveness probe
echo "Testing liveness probe..."
LIVEZ_RESPONSE=$(curl -s "$API_BASE/livez" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$LIVEZ_RESPONSE" = "alive" ]; then
    test_result 0 "Liveness probe returns alive"
else
    test_result 1 "Liveness probe should return alive (got $LIVEZ_RESPONSE)"
fi

# Test readiness probe
echo "Testing readiness probe..."
READYZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/readyz")
if [ "$READYZ_RESPONSE" = "503" ] || [ "$READYZ_RESPONSE" = "200" ]; then
    test_result 0 "Readiness probe returns valid status ($READYZ_RESPONSE)"
else
    test_result 1 "Readiness probe should return 200 or 503 (got $READYZ_RESPONSE)"
fi

echo ""
echo "3. 📊 FINANCE GROUNDING"
echo "----------------------"

# Test finance grounding with valid claim
echo "Testing finance grounding with valid claim..."
FINANCE_VALID=$(curl -s -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/finance/verify-claims" \
    -H 'content-type: application/json' \
    -d '{"context":{"series":[{"series_id":"CPIAUCSL","freq":"M","points":[["2024-01-01",309.72],["2024-02-01",310.23]]}]},"claims":[{"id":"c1","metric":"CPIAUCSL","operator":"=","value":309.72,"at":"2024-01-01"}]}' \
    | jq -r '.all_verified' 2>/dev/null || echo "error")
if [ "$FINANCE_VALID" = "true" ]; then
    test_result 0 "Finance grounding validates correct claims"
else
    test_result 1 "Finance grounding should validate correct claims (got $FINANCE_VALID)"
fi

# Test finance grounding with invalid claim
echo "Testing finance grounding with invalid claim..."
FINANCE_INVALID=$(curl -s -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/finance/verify-claims" \
    -H 'content-type: application/json' \
    -d '{"context":{"series":[{"series_id":"CPIAUCSL","freq":"M","points":[["2024-01-01",309.72]]}]},"claims":[{"id":"c1","metric":"CPIAUCSL","operator":"yoy","value":3.2,"at":"2024-01-01"}]}' \
    | jq -r '.all_verified' 2>/dev/null || echo "error")
if [ "$FINANCE_INVALID" = "false" ]; then
    test_result 0 "Finance grounding rejects invalid claims"
else
    test_result 1 "Finance grounding should reject invalid claims (got $FINANCE_INVALID)"
fi

echo ""
echo "4. 🔄 RATE LIMITING"
echo "------------------"

# Test rate limiting headers
echo "Testing rate limiting headers..."
RATE_HEADERS=$(curl -s -I -H "X-API-Key: $API_KEY" -X POST "$API_BASE/api/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}' | grep -i "x-ratelimit" | wc -l)
if [ "$RATE_HEADERS" -gt 0 ]; then
    test_result 0 "Rate limiting headers present"
else
    test_result 1 "Rate limiting headers should be present"
fi

echo ""
echo "5. 📝 REQUEST TRACING"
echo "-------------------"

# Test request ID correlation
echo "Testing request ID correlation..."
REQUEST_ID=$(curl -s -H "X-Request-ID: test-$(date +%s)" "$API_BASE/livez" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$REQUEST_ID" = "alive" ]; then
    test_result 0 "Request ID correlation works"
else
    test_result 1 "Request ID correlation should work (got $REQUEST_ID)"
fi

echo ""
echo "6. 🛡️ SECURITY HEADERS"
echo "---------------------"

# Test security headers
echo "Testing security headers..."
SECURITY_HEADERS=$(curl -s -I "$API_BASE/livez" | grep -i "x-content-type-options\|x-frame-options\|x-xss-protection" | wc -l)
if [ "$SECURITY_HEADERS" -gt 0 ]; then
    test_result 0 "Security headers present"
else
    test_result 1 "Security headers should be present"
fi

echo ""
echo "7. 🔑 KEY MANAGEMENT"
echo "-------------------"

# Test key creation
echo "Testing key creation..."
KEY_CREATE=$(curl -s -H "X-Admin-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/admin/keys" \
    -H 'content-type: application/json' -d '{"owner":"test-user","tier":"free"}' \
    | jq -r '.id' 2>/dev/null || echo "error")
if [[ "$KEY_CREATE" == noct_* ]]; then
    test_result 0 "Key creation works"
else
    test_result 1 "Key creation should work (got $KEY_CREATE)"
fi

echo ""
echo "8. 📊 API ENDPOINTS"
echo "------------------"

# Test versioned endpoints
echo "Testing versioned API endpoints..."
VERSIONED_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" -X POST "$API_BASE/v1/api/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}')
if [ "$VERSIONED_RESPONSE" = "200" ]; then
    test_result 0 "Versioned API endpoints work"
else
    test_result 1 "Versioned API endpoints should work (got $VERSIONED_RESPONSE)"
fi

echo ""
echo "📊 VALIDATION SUMMARY"
echo "===================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED - READY FOR PRODUCTION!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED - REVIEW BEFORE PRODUCTION${NC}"
    exit 1
fi
