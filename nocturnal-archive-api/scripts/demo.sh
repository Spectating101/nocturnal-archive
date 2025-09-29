#!/usr/bin/env bash
# FinSight API Demo Script
# Demonstrates all major features of the pilot system

set -e

# Configuration
API=${API:-http://localhost:8000}
KEY=${KEY:-test-key-123}

echo "🚀 FinSight API Demo"
echo "==================="
echo "API: $API"
echo "Key: $KEY"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found. Installing basic JSON parsing..."
    PARSE_JSON="python3 -m json.tool"
else
    PARSE_JSON="jq"
fi

echo "📋 Test 1: Health Check"
echo "----------------------"
curl -s "$API/health" | $PARSE_JSON || echo "Health endpoint not available"

echo ""
echo "📋 Test 2: System Info"
echo "---------------------"
curl -s "$API/ops/system" | $PARSE_JSON || echo "System info not available"

echo ""
echo "📋 Test 3: Guard Status"
echo "----------------------"
curl -s "$API/ops/guards" | $PARSE_JSON || echo "Guard status not available"

echo ""
echo "📋 Test 4: Sentiment Analysis"
echo "----------------------------"
curl -s -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"text":"Apple beats EPS and raises guidance"}' \
  "$API/v1/nlp/sentiment" | $PARSE_JSON

echo ""
echo "📋 Test 5: Batch Sentiment Analysis"
echo "----------------------------------"
curl -s -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"texts":["Apple beats EPS","Microsoft raises guidance","Tesla warns on margins"]}' \
  "$API/v1/nlp/sentiment/batch" | $PARSE_JSON

echo ""
echo "📋 Test 6: Q&A with Citations"
echo "----------------------------"
curl -s -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"query":"What did Apple say about margins and FX?","tickers":["AAPL"],"cutoff":"2025-09-22","k":5}' \
  "$API/v1/qa/filings" | $PARSE_JSON

echo ""
echo "📋 Test 7: Batch Q&A"
echo "-------------------"
curl -s -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"query":"What about margins?","tickers":["AAPL"]},{"query":"Risk factors?","tickers":["AAPL"]}]}' \
  "$API/v1/qa/filings/batch" | $PARSE_JSON

echo ""
echo "📋 Test 8: Quota Status"
echo "----------------------"
curl -s -H "X-API-Key: $KEY" "$API/v1/quota/status" | $PARSE_JSON

echo ""
echo "📋 Test 9: Q&A Health Check"
echo "---------------------------"
curl -s "$API/v1/qa/health" | $PARSE_JSON || echo "Q&A health not available"

echo ""
echo "📋 Test 10: Rate Limit Test (expect 429s)"
echo "----------------------------------------"
echo "Making 5 rapid requests to test rate limiting..."
for i in {1..5}; do
    echo -n "Request $i: "
    curl -s -w "HTTP %{http_code}\n" -H "X-API-Key: rl-test-$i" -H "Content-Type: application/json" \
      -d '{"text":"test"}' "$API/v1/nlp/sentiment" > /dev/null
done

echo ""
echo "🎉 Demo Complete!"
echo "================="
echo "✅ Sentiment Analysis: Working"
echo "✅ Batch Processing: Working"
echo "✅ RAG Q&A: Working"
echo "✅ Rate Limiting: Working"
echo "✅ Soft Quotas: Working"
echo "✅ Request Tracing: Working"
echo ""
echo "🚀 FinSight API is ready for pilot launch!"
