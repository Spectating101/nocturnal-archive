#!/bin/bash
# FinSight smoke tests for AAPL/MSFT/TSLA

set -e

echo "🧪 Running FinSight smoke tests..."

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-demo-key-123}"

# Test companies
COMPANIES=("AAPL" "MSFT" "TSLA")

echo "Testing API base: $API_BASE"
echo "Testing companies: ${COMPANIES[*]}"
echo ""

# Test 1: KPI retrieval
echo "📊 Test 1: KPI Retrieval"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company revenue..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/kpis/$company/revenue?freq=Q&limit=4")
    
    if echo "$response" | jq -e '.data' > /dev/null 2>&1; then
        periods=$(echo "$response" | jq '.data | length')
        echo "    ✅ $company: $periods periods returned"
    else
        echo "    ❌ $company: Failed to get revenue data"
        echo "    Response: $response"
    fi
done
echo ""

# Test 2: Metric calculation
echo "🧮 Test 2: Metric Calculation"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company gross margin..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/calc/$company/grossMargin?period=latest&freq=Q")
    
    if echo "$response" | jq -e '.value' > /dev/null 2>&1; then
        value=$(echo "$response" | jq -r '.value')
        formula=$(echo "$response" | jq -r '.formula')
        echo "    ✅ $company: Gross margin = $value ($formula)"
    else
        echo "    ❌ $company: Failed to calculate gross margin"
        echo "    Response: $response"
    fi
done
echo ""

# Test 3: Expression explanation
echo "🔍 Test 3: Expression Explanation"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company: revenue - costOfRevenue..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"ticker\":\"$company\",\"expr\":\"revenue - costOfRevenue\",\"period\":\"latest\",\"freq\":\"Q\"}" \
        "$API_BASE/v1/finance/calc/explain")
    
    if echo "$response" | jq -e '.value' > /dev/null 2>&1; then
        value=$(echo "$response" | jq -r '.value')
        inputs=$(echo "$response" | jq -r '.inputs | keys | join(", ")')
        echo "    ✅ $company: Gross profit = $value (inputs: $inputs)"
    else
        echo "    ❌ $company: Failed to explain expression"
        echo "    Response: $response"
    fi
done
echo ""

# Test 4: Expression verification
echo "✅ Test 4: Expression Verification"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company: grossMargin ≈ 0.4..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"ticker\":\"$company\",\"expr\":\"grossProfit / revenue\",\"assert_value\":\"≈ 0.4\",\"tolerance\":0.1,\"period\":\"latest\",\"freq\":\"Q\"}" \
        "$API_BASE/v1/finance/calc/verify-expression")
    
    if echo "$response" | jq -e '.verified' > /dev/null 2>&1; then
        verified=$(echo "$response" | jq -r '.verified')
        observed=$(echo "$response" | jq -r '.observed')
        echo "    ✅ $company: Verification = $verified (observed: $observed)"
    else
        echo "    ❌ $company: Failed to verify expression"
        echo "    Response: $response"
    fi
done
echo ""

# Test 5: Financial statements
echo "📋 Test 5: Financial Statements"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company income statement..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/kpis/$company/statements/income?period=latest&freq=Q")
    
    if echo "$response" | jq -e '.line_items' > /dev/null 2>&1; then
        items=$(echo "$response" | jq '.line_items | length')
        echo "    ✅ $company: Income statement with $items line items"
    else
        echo "    ❌ $company: Failed to get income statement"
        echo "    Response: $response"
    fi
done
echo ""

# Test 6: Segments
echo "🏢 Test 6: Segment Analysis"
for company in "${COMPANIES[@]}"; do
    echo "  Testing $company geographic segments..."
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/segments/$company/revenue?dim=Geography&freq=Q&limit=4")
    
    if echo "$response" | jq -e '.series' > /dev/null 2>&1; then
        segments=$(echo "$response" | jq '.series | length')
        echo "    ✅ $company: $segments geographic segments"
    else
        echo "    ❌ $company: Failed to get segment data"
        echo "    Response: $response"
    fi
done
echo ""

# Test 7: Registry endpoints
echo "📚 Test 7: Registry Endpoints"
echo "  Testing available KPIs..."
response=$(curl -s -H "X-API-Key:$API_KEY" \
    "$API_BASE/v1/finance/calc/registry/metrics")

if echo "$response" | jq -e '.metrics' > /dev/null 2>&1; then
    kpi_count=$(echo "$response" | jq '.metrics | length')
    echo "    ✅ Available KPIs: $kpi_count"
else
    echo "    ❌ Failed to get available KPIs"
fi

echo "  Testing available inputs..."
response=$(curl -s -H "X-API-Key:$API_KEY" \
    "$API_BASE/v1/finance/calc/registry/inputs")

if echo "$response" | jq -e '.inputs' > /dev/null 2>&1; then
    input_count=$(echo "$response" | jq '.inputs | length')
    echo "    ✅ Available inputs: $input_count"
else
    echo "    ❌ Failed to get available inputs"
fi
echo ""

# Test 8: Performance check
echo "⚡ Test 8: Performance Check"
start_time=$(date +%s)
response=$(curl -s -H "X-API-Key:$API_KEY" \
    "$API_BASE/v1/finance/calc/AAPL/grossMargin?period=latest&freq=Q")
end_time=$(date +%s)
duration=$((end_time - start_time))

if echo "$response" | jq -e '.value' > /dev/null 2>&1; then
    echo "    ✅ AAPL gross margin calculation: ${duration}s"
    if [ $duration -lt 5 ]; then
        echo "    ✅ Performance: Good (< 5s)"
    elif [ $duration -lt 10 ]; then
        echo "    ⚠️  Performance: Acceptable (< 10s)"
    else
        echo "    ❌ Performance: Slow (> 10s)"
    fi
else
    echo "    ❌ Performance test failed"
fi
echo ""

echo "🎉 FinSight smoke tests completed!"
echo ""
echo "Summary:"
echo "  - Companies tested: ${#COMPANIES[@]}"
echo "  - Endpoints tested: 8"
echo "  - Total API calls: ~24"
echo ""
echo "💡 Tips:"
echo "  - Check API logs for any errors"
echo "  - Verify data accuracy against SEC filings"
echo "  - Monitor response times for performance issues"

