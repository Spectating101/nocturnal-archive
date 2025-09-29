#!/usr/bin/env python3
"""
Cache Priming Script for FinSight API
Warms up the cache with hot paths before production launch
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict

API_BASE = "http://localhost:8000"
API_KEY = "demo-key-123"

# Hot paths to prime
HOT_PATHS = [
    # AAPL - Most requested US GAAP company
    {"method": "POST", "url": "/v1/finance/calc/explain", "data": {"ticker": "AAPL", "expr": "grossProfit = revenue - costOfRevenue", "period": "latest", "freq": "Q"}},
    {"method": "GET", "url": "/v1/finance/calc/series/AAPL/revenue?freq=Q&limit=12"},
    {"method": "GET", "url": "/v1/finance/segments/AAPL/revenue?dim=Geography&freq=Q&limit=4"},
    {"method": "GET", "url": "/v1/finance/reports/AAPL/2024-Q4.pdf"},
    
    # TSM - IFRS + FX normalization
    {"method": "GET", "url": "/v1/finance/calc/series/TSM/revenue?freq=Q&limit=12"},
    {"method": "GET", "url": "/v1/finance/calc/series/TSM/grossProfit?freq=Q&limit=12"},
    
    # SAP - IFRS + FX normalization
    {"method": "GET", "url": "/v1/finance/calc/series/SAP/revenue?freq=Q&limit=12"},
    {"method": "GET", "url": "/v1/finance/calc/series/SAP/grossProfit?freq=Q&limit=12"},
    
    # Other major US GAAP companies
    {"method": "GET", "url": "/v1/finance/calc/series/MSFT/revenue?freq=Q&limit=12"},
    {"method": "GET", "url": "/v1/finance/calc/series/NVDA/revenue?freq=Q&limit=12"},
    {"method": "GET", "url": "/v1/finance/calc/series/AMZN/revenue?freq=Q&limit=12"},
    
    # Status endpoint
    {"method": "GET", "url": "/v1/finance/status/"},
]

async def make_request(session: aiohttp.ClientSession, path: Dict) -> Dict:
    """Make a single request and return timing info"""
    start_time = time.time()
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        if path["method"] == "POST":
            headers["Content-Type"] = "application/json"
            async with session.post(
                f"{API_BASE}{path['url']}", 
                json=path["data"], 
                headers=headers
            ) as response:
                content = await response.text()
                status = response.status
        else:
            async with session.get(
                f"{API_BASE}{path['url']}", 
                headers=headers
            ) as response:
                content = await response.text()
                status = response.status
        
        duration = time.time() - start_time
        
        return {
            "url": path["url"],
            "method": path["method"],
            "status": status,
            "duration": duration,
            "success": 200 <= status < 300,
            "size": len(content)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "url": path["url"],
            "method": path["method"],
            "status": 0,
            "duration": duration,
            "success": False,
            "error": str(e)
        }

async def prime_cache():
    """Prime the cache with hot paths"""
    print("🔥 Starting cache priming for FinSight API...")
    print(f"📍 Target: {API_BASE}")
    print(f"🎯 Priming {len(HOT_PATHS)} hot paths")
    print()
    
    async with aiohttp.ClientSession() as session:
        # First pass - cold cache
        print("❄️  First pass (cold cache):")
        cold_results = []
        for path in HOT_PATHS:
            result = await make_request(session, path)
            cold_results.append(result)
            status_emoji = "✅" if result["success"] else "❌"
            print(f"  {status_emoji} {result['method']} {result['url']} - {result['duration']:.3f}s - {result['status']}")
        
        print()
        
        # Second pass - warm cache
        print("🔥 Second pass (warm cache):")
        warm_results = []
        for path in HOT_PATHS:
            result = await make_request(session, path)
            warm_results.append(result)
            status_emoji = "✅" if result["success"] else "❌"
            print(f"  {status_emoji} {result['method']} {result['url']} - {result['duration']:.3f}s - {result['status']}")
        
        print()
        
        # Calculate improvements
        print("📊 Cache Performance Analysis:")
        total_cold_time = sum(r["duration"] for r in cold_results if r["success"])
        total_warm_time = sum(r["duration"] for r in warm_results if r["success"])
        
        successful_cold = [r for r in cold_results if r["success"]]
        successful_warm = [r for r in warm_results if r["success"]]
        
        if successful_cold and successful_warm:
            avg_cold = total_cold_time / len(successful_cold)
            avg_warm = total_warm_time / len(successful_warm)
            improvement = ((avg_cold - avg_warm) / avg_cold) * 100
            
            print(f"  📈 Average cold cache time: {avg_cold:.3f}s")
            print(f"  📈 Average warm cache time: {avg_warm:.3f}s")
            print(f"  🚀 Cache improvement: {improvement:.1f}%")
            
            if improvement > 50:
                print("  ✅ Excellent cache performance!")
            elif improvement > 25:
                print("  ✅ Good cache performance!")
            else:
                print("  ⚠️  Cache performance could be improved")
        
        print()
        print("🎉 Cache priming complete!")

if __name__ == "__main__":
    asyncio.run(prime_cache())


