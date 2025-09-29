#!/bin/bash
# Prime Cache with Key Tickers
# Pre-loads cache with 8 key companies for optimal performance

set -e

echo "🚀 FinSight Cache Priming"
echo "========================="

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-demo-key-123}"

# Key tickers to prime
TICKERS=("AAPL" "MSFT" "NVDA" "AMZN" "ASML" "TSM" "SAP" "SHEL")

echo "Priming cache for: ${TICKERS[*]}"
echo "API Base: $API_BASE"
echo ""

# Function to prime a ticker
prime_ticker() {
    local ticker=$1
    echo "📊 Priming $ticker..."
    
    # Revenue series (12Q)
    echo "  Revenue series..."
    curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/kpis/$ticker/revenue?freq=Q&limit=12" > /dev/null
    
    # Key metrics
    for metric in "grossMargin" "ebitdaMargin" "netIncome" "fcf"; do
        echo "  $metric..."
        curl -s -H "X-API-Key:$API_KEY" \
            "$API_BASE/v1/finance/calc/$ticker/$metric?period=latest&freq=Q" > /dev/null
    done
    
    # TTM calculations
    echo "  TTM calculations..."
    curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/calc/series/$ticker/roe?freq=Q&limit=12&ttm=true" > /dev/null
    
    # Geography segments
    echo "  Geography segments..."
    curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/segments/$ticker/revenue?dim=Geography&freq=Q&limit=8" > /dev/null
    
    echo "  ✅ $ticker primed"
    echo ""
}

# Prime all tickers
for ticker in "${TICKERS[@]}"; do
    prime_ticker "$ticker"
done

echo "🎯 Cache Priming Complete"
echo "========================="
echo "Primed ${#TICKERS[@]} tickers with:"
echo "  - Revenue series (12Q)"
echo "  - Key metrics (grossMargin, ebitdaMargin, netIncome, fcf)"
echo "  - TTM calculations (roe)"
echo "  - Geography segments"
echo ""
echo "Cache is now optimized for production traffic! 🚀"
