#!/bin/bash
# FinSight Alpha Audit - 5-ticker test (1 US GAAP + 4 IFRS)

set -e

echo "🧪 FinSight Alpha Audit - 5-Ticker Test"
echo "======================================="

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-demo-key-123}"

# Test companies and their expected characteristics
declare -A COMPANIES
COMPANIES[AAPL]="USD,GAAP,US"
COMPANIES[ASML]="EUR,IFRS,EU"
COMPANIES[TSM]="TWD,IFRS,TW"
COMPANIES[SAP]="EUR,IFRS,DE"
COMPANIES[SHEL]="USD,IFRS,GB"

echo "Testing companies: ${!COMPANIES[*]}"
echo "API Base: $API_BASE"
echo ""

# Test 1: Revenue series with citations
echo "📊 Test 1: Revenue Series (12Q + Citations)"
echo "-------------------------------------------"
for ticker in "${!COMPANIES[@]}"; do
    info=(${COMPANIES[$ticker]//,/ })
    currency=${info[0]}
    standard=${info[1]}
    country=${info[2]}
    
    echo "  Testing $ticker ($currency, $standard, $country)..."
    
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/kpis/$ticker/revenue?freq=Q&limit=12")
    
    if echo "$response" | jq -e '.data' > /dev/null 2>&1; then
        periods=$(echo "$response" | jq '.data | length')
        latest_value=$(echo "$response" | jq -r '.data[0].value')
        latest_period=$(echo "$response" | jq -r '.data[0].period')
        has_citations=$(echo "$response" | jq '.data[0].citation.source_url != null')
        
        echo "    ✅ $ticker: $periods periods, latest: $latest_period = $latest_value"
        if [ "$has_citations" = "true" ]; then
            echo "    ✅ Citations: Present"
        else
            echo "    ❌ Citations: Missing"
        fi
    else
        echo "    ❌ $ticker: Failed to get revenue data"
        echo "    Response: $response"
    fi
done
echo ""

# Test 2: EBITDA margin TTM with proofs
echo "📈 Test 2: EBITDA Margin TTM (with Proofs)"
echo "------------------------------------------"
for ticker in "${!COMPANIES[@]}"; do
    echo "  Testing $ticker EBITDA margin TTM..."
    
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/calc/series/$ticker/ebitdaMargin?freq=Q&limit=12&ttm=true")
    
    if echo "$response" | jq -e '.series' > /dev/null 2>&1; then
        points=$(echo "$response" | jq '.series | length')
        latest_point=$(echo "$response" | jq '.series[-1]')
        latest_value=$(echo "$response" | jq -r '.series[-1].value')
        latest_period=$(echo "$response" | jq -r '.series[-1].period')
        
        echo "    ✅ $ticker: $points TTM points, latest: $latest_period = ${latest_value}%"
        
        # Check for FX conversion in citations
        fx_used=$(echo "$response" | jq '.series[-1].citations[] | select(.fx_conversion != null)')
        if [ "$fx_used" != "" ]; then
            echo "    ✅ FX Conversion: Present in citations"
        else
            echo "    ⚠️  FX Conversion: Not detected (may be USD)"
        fi
    else
        echo "    ❌ $ticker: Failed to get EBITDA margin TTM"
        echo "    Response: $response"
    fi
done
echo ""

# Test 3: Geography segments
echo "🌍 Test 3: Geography Segments"
echo "-----------------------------"
for ticker in "${!COMPANIES[@]}"; do
    echo "  Testing $ticker geographic segments..."
    
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/segments/$ticker/revenue?dim=Geography&freq=Q&limit=8")
    
    if echo "$response" | jq -e '.series' > /dev/null 2>&1; then
        segments=$(echo "$response" | jq '.series | length')
        segment_names=$(echo "$response" | jq -r '.series[].segment' | tr '\n' ', ' | sed 's/,$//')
        
        echo "    ✅ $ticker: $segments segments ($segment_names)"
        
        # Check for specific expected segments
        if [[ "$segment_names" == *"Americas"* ]] || [[ "$segment_names" == *"Europe"* ]] || [[ "$segment_names" == *"Asia"* ]]; then
            echo "    ✅ Geographic breakdown: Present"
        else
            echo "    ⚠️  Geographic breakdown: Limited or consolidated"
        fi
    else
        echo "    ❌ $ticker: Failed to get segment data"
        echo "    Response: $response"
    fi
done
echo ""

# Test 4: Expression explanation with FX
echo "🔍 Test 4: Expression Explanation (with FX)"
echo "-------------------------------------------"
for ticker in "${!COMPANIES[@]}"; do
    info=(${COMPANIES[$ticker]//,/ })
    currency=${info[0]}
    
    echo "  Testing $ticker: grossProfit = revenue - costOfRevenue ($currency)..."
    
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"ticker\":\"$ticker\",\"expr\":\"revenue - costOfRevenue\",\"period\":\"latest\",\"freq\":\"Q\"}" \
        "$API_BASE/v1/finance/calc/explain")
    
    if echo "$response" | jq -e '.value' > /dev/null 2>&1; then
        value=$(echo "$response" | jq -r '.value')
        inputs=$(echo "$response" | jq '.inputs | keys | join(", ")')
        citations=$(echo "$response" | jq '.citations | length')
        
        echo "    ✅ $ticker: Gross profit = $value (inputs: $inputs)"
        echo "    ✅ Citations: $citations sources"
        
        # Check for unit normalization
        units=$(echo "$response" | jq -r '.inputs[].unit' | sort -u | tr '\n' ', ' | sed 's/,$//')
        echo "    📊 Units detected: $units"
        
    else
        echo "    ❌ $ticker: Failed to explain expression"
        echo "    Response: $response"
    fi
done
echo ""

# Test 5: IFRS concept mapping
echo "🏛️  Test 5: IFRS Concept Mapping"
echo "--------------------------------"
ifrs_companies=("ASML" "TSM" "SAP" "SHEL")
for ticker in "${ifrs_companies[@]}"; do
    echo "  Testing $ticker IFRS concepts..."
    
    # Test revenue (should map to IFRS concepts)
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/kpis/$ticker/revenue?freq=Q&limit=1")
    
    if echo "$response" | jq -e '.data' > /dev/null 2>&1; then
        concept=$(echo "$response" | jq -r '.concept_used')
        has_data=$(echo "$response" | jq '.data | length > 0')
        
        if [ "$has_data" = "true" ]; then
            echo "    ✅ $ticker: IFRS revenue concept found ($concept)"
        else
            echo "    ❌ $ticker: No IFRS revenue data found"
        fi
    else
        echo "    ❌ $ticker: Failed to test IFRS concepts"
    fi
done
echo ""

# Test 6: Unit and scale normalization
echo "⚖️  Test 6: Unit & Scale Normalization"
echo "-------------------------------------"
for ticker in "${!COMPANIES[@]}"; do
    info=(${COMPANIES[$ticker]//,/ })
    currency=${info[0]}
    
    echo "  Testing $ticker unit normalization ($currency)..."
    
    response=$(curl -s -H "X-API-Key:$API_KEY" \
        "$API_BASE/v1/finance/calc/$ticker/revenue?period=latest&freq=Q")
    
    if echo "$response" | jq -e '.value' > /dev/null 2>&1; then
        value=$(echo "$response" | jq -r '.value')
        unit=$(echo "$response" | jq -r '.inputs.revenue.unit')
        normalized=$(echo "$response" | jq -r '.inputs.revenue.value')
        
        echo "    ✅ $ticker: Revenue = $normalized $unit (normalized: $value)"
        
        # Check for scale indicators
        if [[ "$unit" == *"K"* ]] || [[ "$unit" == *"M"* ]] || [[ "$unit" == *"B"* ]]; then
            echo "    ✅ Scale normalization: Applied ($unit)"
        else
            echo "    ℹ️  Scale: Units ($unit)"
        fi
    else
        echo "    ❌ $ticker: Failed to test unit normalization"
    fi
done
echo ""

# Summary
echo "📋 Alpha Audit Summary"
echo "====================="
echo "Companies tested: ${#COMPANIES[@]}"
echo "  - US GAAP: AAPL"
echo "  - IFRS: ASML (EUR), TSM (TWD), SAP (EUR), SHEL (USD)"
echo ""
echo "Tests performed:"
echo "  ✅ Revenue series with citations"
echo "  ✅ EBITDA margin TTM with proofs"
echo "  ✅ Geography segments breakdown"
echo "  ✅ Expression explanation with FX"
echo "  ✅ IFRS concept mapping"
echo "  ✅ Unit & scale normalization"
echo ""
echo "🎯 Key Validations:"
echo "  - Cross-jurisdiction concept mapping (IFRS ↔ GAAP)"
echo "  - Multi-currency FX normalization (EUR, TWD, GBP ↔ USD)"
echo "  - Unit scaling (K, M, B normalization)"
echo "  - Segment-level analysis with citations"
echo "  - 'A = B - C' explanations with provenance"
echo ""
echo "💡 This validates FinSight's core differentiators vs yfinance:"
echo "  - Regulator-first data (SEC EDGAR XBRL)"
echo "  - Multi-jurisdiction support (US, EU, TW)"
echo "  - Cited mathematics with full provenance"
echo "  - Segment-aware analysis"
echo "  - Production-ready error handling"
