#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE STRESS TEST - Diverse Tickers
Tests the system with 20+ diverse companies across industries, not just AAPL!
"""

import asyncio
import json
import time
from typing import Dict, List, Any
import httpx
from dataclasses import dataclass, asdict

@dataclass
class TestResult:
    ticker: str
    industry: str
    test_type: str
    success: bool
    response_time_ms: int
    status_code: int
    data: Any
    error: str = None
    notes: str = None

# DIVERSE TEST SUITE - NOT JUST AAPL!
TEST_TICKERS = [
    # Footwear & Apparel
    {"ticker": "CROX", "cik": "1334036", "name": "Crocs Inc", "industry": "Footwear"},
    {"ticker": "NKE", "cik": "0000320187", "name": "Nike Inc", "industry": "Footwear"},
    {"ticker": "LULU", "cik": "0001397187", "name": "Lululemon", "industry": "Apparel"},

    # Automotive & Transportation
    {"ticker": "KMX", "cik": "0001170010", "name": "CarMax", "industry": "Used Cars"},
    {"ticker": "TSLA", "cik": "0001318605", "name": "Tesla", "industry": "EVs"},
    {"ticker": "F", "cik": "0000037996", "name": "Ford", "industry": "Auto"},

    # Retail & Consumer
    {"ticker": "ULTA", "cik": "0001403568", "name": "Ulta Beauty", "industry": "Beauty Retail"},
    {"ticker": "ZUMZ", "cik": "0001300936", "name": "Zumiez", "industry": "Retail"},
    {"ticker": "RH", "cik": "0001528849", "name": "RH (Restoration Hardware)", "industry": "Furniture"},

    # Services
    {"ticker": "HRB", "cik": "0000012659", "name": "H&R Block", "industry": "Tax Services"},
    {"ticker": "FUN", "cik": "0001564902", "name": "Six Flags", "industry": "Amusement Parks"},

    # Tech (not AAPL/MSFT!)
    {"ticker": "NVDA", "cik": "0001045810", "name": "NVIDIA", "industry": "Semiconductors"},
    {"ticker": "AMD", "cik": "0000002488", "name": "AMD", "industry": "Semiconductors"},
    {"ticker": "INTC", "cik": "0000050863", "name": "Intel", "industry": "Semiconductors"},

    # Foreign ADRs
    {"ticker": "BABA", "cik": "0001577552", "name": "Alibaba (ADR)", "industry": "China E-commerce"},
    {"ticker": "TSM", "cik": "0001046179", "name": "TSMC (ADR)", "industry": "Taiwan Semiconductor"},

    # Small Cap (< $2B market cap)
    {"ticker": "BMBL", "cik": "0001803925", "name": "Bumble", "industry": "Dating App"},
    {"ticker": "BYND", "cik": "0001655210", "name": "Beyond Meat", "industry": "Plant-Based Food"},

    # Edge Cases
    {"ticker": "GME", "cik": "0001326380", "name": "GameStop", "industry": "Gaming Retail"},
    {"ticker": "AMC", "cik": "0001411579", "name": "AMC Entertainment", "industry": "Theaters"},
]

# Crypto tickers (if supported)
CRYPTO_TICKERS = [
    {"ticker": "BTC-USD", "name": "Bitcoin", "industry": "Cryptocurrency"},
    {"ticker": "ETH-USD", "name": "Ethereum", "industry": "Cryptocurrency"},
]

BASE_URL = "http://127.0.0.1:8000"

async def test_ticker_basic(client: httpx.AsyncClient, ticker: str) -> TestResult:
    """Test basic ticker data retrieval"""
    url = f"{BASE_URL}/v1/finance/calc/{ticker}/grossProfit"

    start = time.time()
    try:
        response = await client.get(
            url,
            headers={"X-API-Key": "na_test_api_key_123"},
            timeout=10.0
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = response.json()
            return TestResult(
                ticker=ticker,
                industry=get_industry(ticker),
                test_type="basic_metric",
                success=True,
                response_time_ms=elapsed_ms,
                status_code=200,
                data=data,
                notes=f"Value: {data.get('value', 'N/A')}, Period: {data.get('period', 'N/A')}"
            )
        else:
            return TestResult(
                ticker=ticker,
                industry=get_industry(ticker),
                test_type="basic_metric",
                success=False,
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
                data=response.json() if response.status_code != 500 else None,
                error=response.text
            )
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return TestResult(
            ticker=ticker,
            industry=get_industry(ticker),
            test_type="basic_metric",
            success=False,
            response_time_ms=elapsed_ms,
            status_code=0,
            data=None,
            error=str(e)
        )

async def test_expression(client: httpx.AsyncClient, ticker: str) -> TestResult:
    """Test expression calculation"""
    url = f"{BASE_URL}/v1/finance/calc/explain"

    start = time.time()
    try:
        response = await client.post(
            url,
            json={
                "ticker": ticker,
                "expr": "revenue - costOfRevenue",
                "period": "latest",
                "freq": "Q"
            },
            headers={"X-API-Key": "na_test_api_key_123"},
            timeout=15.0
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = response.json()
            return TestResult(
                ticker=ticker,
                industry=get_industry(ticker),
                test_type="expression_calc",
                success=True,
                response_time_ms=elapsed_ms,
                status_code=200,
                data=data,
                notes=f"Calculated value: {data.get('value', 'N/A')}"
            )
        else:
            return TestResult(
                ticker=ticker,
                industry=get_industry(ticker),
                test_type="expression_calc",
                success=False,
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
                data=None,
                error=response.text[:200] if response.text else None
            )
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return TestResult(
            ticker=ticker,
            industry=get_industry(ticker),
            test_type="expression_calc",
            success=False,
            response_time_ms=elapsed_ms,
            status_code=0,
            data=None,
            error=str(e)
        )

async def test_sec_facts_direct(ticker: str, cik: str) -> Dict[str, Any]:
    """Fetch SEC facts directly for validation"""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    headers = {"User-Agent": "Nocturnal Archive Test Suite test@nocturnal.com"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"SEC direct fetch failed for {ticker}: {e}")
    return None

def get_industry(ticker: str) -> str:
    """Get industry for ticker"""
    for t in TEST_TICKERS:
        if t["ticker"] == ticker:
            return t["industry"]
    for t in CRYPTO_TICKERS:
        if t["ticker"] == ticker:
            return t["industry"]
    return "Unknown"

def get_cik(ticker: str) -> str:
    """Get CIK for ticker"""
    for t in TEST_TICKERS:
        if t["ticker"] == ticker:
            return t["cik"]
    return None

async def run_comprehensive_tests():
    """Run all tests"""
    results: List[TestResult] = []

    print("🔥 STARTING COMPREHENSIVE STRESS TEST - NO MORE AAPL BS!\n")
    print(f"Testing {len(TEST_TICKERS)} diverse companies across industries\n")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        # Test each ticker
        for ticker_info in TEST_TICKERS:
            ticker = ticker_info["ticker"]
            name = ticker_info["name"]
            industry = ticker_info["industry"]

            print(f"\n📊 Testing {ticker} ({name}) - {industry}")
            print("-" * 80)

            # Test 1: Basic metric
            result1 = await test_ticker_basic(client, ticker)
            results.append(result1)
            print(f"  ✓ Basic metric: {'✅ PASS' if result1.success else '❌ FAIL'} ({result1.response_time_ms}ms)")
            if not result1.success:
                print(f"    Error: {result1.error[:100] if result1.error else 'Unknown'}")

            # Test 2: Expression calculation
            result2 = await test_expression(client, ticker)
            results.append(result2)
            print(f"  ✓ Expression: {'✅ PASS' if result2.success else '❌ FAIL'} ({result2.response_time_ms}ms)")
            if not result2.success:
                print(f"    Error: {result2.error[:100] if result2.error else 'Unknown'}")

            # Small delay to not hammer the server
            await asyncio.sleep(0.5)

        # Test crypto if endpoints support it
        print(f"\n\n🪙 TESTING CRYPTO (if supported)")
        print("=" * 80)
        for crypto_info in CRYPTO_TICKERS[:2]:  # Just test 2
            ticker = crypto_info["ticker"]
            print(f"\n📊 Testing {ticker} ({crypto_info['name']})")
            result = await test_ticker_basic(client, ticker)
            results.append(result)
            print(f"  ✓ Basic: {'✅ PASS' if result.success else '❌ FAIL (expected if not supported)'}")

    # Generate summary report
    print("\n\n" + "=" * 80)
    print("📈 STRESS TEST SUMMARY")
    print("=" * 80)

    total_tests = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total_tests - passed

    avg_response_time = sum(r.response_time_ms for r in results) / total_tests if total_tests > 0 else 0

    print(f"\n📊 Overall Results:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed} ({'%.1f' % (passed/total_tests*100)}%)")
    print(f"  Failed: {failed} ({'%.1f' % (failed/total_tests*100)}%)")
    print(f"  Avg response time: {avg_response_time:.0f}ms")

    # Response time buckets
    fast = sum(1 for r in results if r.response_time_ms < 1000)
    medium = sum(1 for r in results if 1000 <= r.response_time_ms < 3000)
    slow = sum(1 for r in results if r.response_time_ms >= 3000)

    print(f"\n⏱️  Response Time Distribution:")
    print(f"  < 1s (fast): {fast}")
    print(f"  1-3s (ok): {medium}")
    print(f"  > 3s (slow): {slow}")

    # Industry breakdown
    print(f"\n🏭 Results by Industry:")
    industries = {}
    for r in results:
        if r.industry not in industries:
            industries[r.industry] = {"pass": 0, "fail": 0}
        if r.success:
            industries[r.industry]["pass"] += 1
        else:
            industries[r.industry]["fail"] += 1

    for industry in sorted(industries.keys()):
        stats = industries[industry]
        total = stats["pass"] + stats["fail"]
        print(f"  {industry}: {stats['pass']}/{total} passed")

    # Failed tests detail
    failed_results = [r for r in results if not r.success]
    if failed_results:
        print(f"\n❌ Failed Tests Detail:")
        for r in failed_results:
            print(f"  - {r.ticker} ({r.industry}): {r.error[:80] if r.error else 'Unknown error'}")

    # Save detailed results to JSON
    results_dict = [asdict(r) for r in results]
    with open("stress_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed/total_tests*100 if total_tests > 0 else 0,
                "avg_response_time_ms": avg_response_time
            },
            "results": results_dict
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: stress_test_results.json")

    # THE HONEST TRUTH
    print(f"\n\n🔥 THE HONEST VERDICT:")
    print("=" * 80)

    if passed / total_tests > 0.8:
        print("✅ GOOD: System works for most tickers (>80% pass rate)")
    elif passed / total_tests > 0.5:
        print("⚠️  MIXED: System works for some tickers (50-80% pass rate)")
    else:
        print("❌ POOR: System fails for most tickers (<50% pass rate)")

    if avg_response_time < 1000:
        print("✅ FAST: Average response time < 1 second")
    elif avg_response_time < 3000:
        print("⚠️  OK: Average response time 1-3 seconds")
    else:
        print("❌ SLOW: Average response time > 3 seconds")

    print("\n📝 Next: Review stress_test_results.json for detailed analysis")
    print("📝 Then: Fact-check specific values against SEC EDGAR filings")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
