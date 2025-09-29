#!/bin/bash

# Nocturnal Archive - Demo Script
# Tests all critical functionality with clear pass/fail indicators

set -e

echo "🚀 Nocturnal Archive Demo Script"
echo "================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and check result
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    
    echo -n "Testing $test_name... "
    
    if eval "$command" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
}

# Start Interactive Agent
echo "Starting Interactive Agent..."
source server_venv/bin/activate
SERVER_PORT=8011 python interactive_agent.py &
AGENT_PID=$!
sleep 3

# Start FinSight API
echo "Starting FinSight API..."
cd ../nocturnal-archive-api
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8012 &
FINSIGHT_PID=$!
sleep 3
cd ../unified-platform

echo
echo "🧪 Running Demo Tests..."
echo "========================"

# Test 1: Interactive Agent - File Listing
run_test "File Listing" \
    'curl -s -X POST "http://localhost:8011/interactive/chat" -H "Content-Type: application/json" -d "{\"question\":\"List files here\",\"user_id\":\"demo\"}" | python3 -c "import sys,json; data=json.load(sys.stdin); print(\"PASS\" if \"README\" in data.get(\"response\",\"\") else \"FAIL\")"' \
    "PASS"

# Test 2: Interactive Agent - R Programming
run_test "R Programming" \
    'curl -s -X POST "http://localhost:8011/interactive/chat" -H "Content-Type: application/json" -d "{\"question\":\"How do I create a histogram in R?\",\"user_id\":\"demo\"}" | python3 -c "import sys,json; data=json.load(sys.stdin); print(\"PASS\" if \"hist(\" in data.get(\"response\",\"\") else \"FAIL\")"' \
    "PASS"

# Test 3: Interactive Agent - SQL Queries
run_test "SQL Queries" \
    'curl -s -X POST "http://localhost:8011/interactive/chat" -H "Content-Type: application/json" -d "{\"question\":\"Write a SQL query to find top customers\",\"user_id\":\"demo\"}" | python3 -c "import sys,json; data=json.load(sys.stdin); print(\"PASS\" if \"SELECT\" in data.get(\"response\",\"\") else \"FAIL\")"' \
    "PASS"

# Test 4: FinSight API - Sentiment Analysis
run_test "Sentiment Analysis" \
    'curl -s -X POST "http://localhost:8012/v1/nlp/sentiment" -H "Content-Type: application/json" -H "X-API-Key: test-key-123" -d "{\"text\":\"Company beats earnings expectations\"}" | python3 -c "import sys,json; data=json.load(sys.stdin); print(\"PASS\" if \"label\" in data and \"score\" in data else \"FAIL\")"' \
    "PASS"

# Test 5: Rate Limiting Headers
run_test "Rate Limiting" \
    'curl -i -s -X POST "http://localhost:8012/v1/nlp/sentiment" -H "Content-Type: application/json" -H "X-API-Key: test-key-123" -d "{\"text\":\"test\"}" | head -20 | grep -q "x-ratelimit"' \
    "x-ratelimit"

echo
echo "📊 Demo Results"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED - SYSTEM READY FOR PILOT!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED - SYSTEM NEEDS FIXES${NC}"
    exit 1
fi

# Cleanup
echo
echo "Cleaning up..."
kill $AGENT_PID 2>/dev/null || true
kill $FINSIGHT_PID 2>/dev/null || true
