#!/usr/bin/env python3
"""
Test script to verify Archive API and AI Agent upgrades
Tests real data integration, caching, and API connectivity
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class UpgradeTester:
    """Test the upgraded Archive API and AI Agent"""
    
    def __init__(self):
        self.archive_base = "http://localhost:8000/api"
        self.finsight_base = "http://localhost:8000/v1/finance"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_archive_search(self) -> Dict[str, Any]:
        """Test Archive API search with real data"""
        print("🔍 Testing Archive API Search...")
        
        try:
            search_data = {
                "query": "machine learning artificial intelligence",
                "limit": 5,
                "sources": ["openalex", "pubmed"]
            }
            
            async with self.session.post(f"{self.archive_base}/search", json=search_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Search successful: {result.get('count', 0)} papers found")
                    return {"status": "success", "count": result.get('count', 0), "data": result}
                else:
                    print(f"❌ Search failed: {response.status}")
                    return {"status": "error", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_archive_synthesis(self) -> Dict[str, Any]:
        """Test Archive API synthesis"""
        print("📝 Testing Archive API Synthesis...")
        
        try:
            # Use some sample paper IDs
            synthesis_data = {
                "paper_ids": ["paper_1", "paper_2", "paper_3"],
                "max_words": 300,
                "focus": "key_findings",
                "style": "academic"
            }
            
            async with self.session.post(f"{self.archive_base}/synthesize", json=synthesis_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Synthesis successful: {result.get('word_count', 0)} words")
                    return {"status": "success", "word_count": result.get('word_count', 0), "data": result}
                else:
                    print(f"❌ Synthesis failed: {response.status}")
                    return {"status": "error", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_finsight_api(self) -> Dict[str, Any]:
        """Test FinSight API"""
        print("💰 Testing FinSight API...")
        
        try:
            # Test a simple KPI request
            async with self.session.get(f"{self.finsight_base}/kpis/AAPL/revenue?limit=4") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ FinSight successful: {len(result.get('data', []))} data points")
                    return {"status": "success", "data_points": len(result.get('data', [])), "data": result}
                else:
                    print(f"❌ FinSight failed: {response.status}")
                    return {"status": "error", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            print(f"❌ FinSight error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoints"""
        print("🏥 Testing API Health...")
        
        health_results = {}
        
        # Test Archive API health
        try:
            async with self.session.get(f"{self.archive_base}/health") as response:
                if response.status == 200:
                    health_results["archive"] = "healthy"
                    print("✅ Archive API: Healthy")
                else:
                    health_results["archive"] = f"unhealthy ({response.status})"
                    print(f"❌ Archive API: Unhealthy ({response.status})")
        except Exception as e:
            health_results["archive"] = f"error: {e}"
            print(f"❌ Archive API: Error - {e}")
        
        # Test FinSight API health
        try:
            async with self.session.get(f"{self.finsight_base}/health") as response:
                if response.status == 200:
                    health_results["finsight"] = "healthy"
                    print("✅ FinSight API: Healthy")
                else:
                    health_results["finsight"] = f"unhealthy ({response.status})"
                    print(f"❌ FinSight API: Unhealthy ({response.status})")
        except Exception as e:
            health_results["finsight"] = f"error: {e}"
            print(f"❌ FinSight API: Error - {e}")
        
        return health_results
    
    async def test_caching_performance(self) -> Dict[str, Any]:
        """Test caching performance"""
        print("⚡ Testing Caching Performance...")
        
        # Test search caching
        search_data = {
            "query": "caching performance test",
            "limit": 3,
            "sources": ["openalex"]
        }
        
        # First request (should be slow)
        start_time = time.time()
        async with self.session.post(f"{self.archive_base}/search", json=search_data) as response:
            first_request_time = time.time() - start_time
        
        # Second request (should be fast due to caching)
        start_time = time.time()
        async with self.session.post(f"{self.archive_base}/search", json=search_data) as response:
            second_request_time = time.time() - start_time
        
        cache_speedup = first_request_time / second_request_time if second_request_time > 0 else 0
        
        print(f"📊 First request: {first_request_time:.2f}s")
        print(f"📊 Second request: {second_request_time:.2f}s")
        print(f"📊 Cache speedup: {cache_speedup:.1f}x")
        
        return {
            "first_request_time": first_request_time,
            "second_request_time": second_request_time,
            "cache_speedup": cache_speedup,
            "caching_working": cache_speedup > 1.5
        }
    
    async def run_comprehensive_test(self):
        """Run all tests and generate report"""
        print("🚀 Starting Comprehensive Upgrade Test")
        print("=" * 60)
        
        results = {}
        
        # Test API health
        results["health"] = await self.test_api_health()
        print()
        
        # Test Archive API
        results["archive_search"] = await self.test_archive_search()
        print()
        results["archive_synthesis"] = await self.test_archive_synthesis()
        print()
        
        # Test FinSight API
        results["finsight"] = await self.test_finsight_api()
        print()
        
        # Test caching
        results["caching"] = await self.test_caching_performance()
        print()
        
        # Generate report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results: Dict[str, Any]):
        """Generate upgrade test report"""
        print("📋 UPGRADE TEST REPORT")
        print("=" * 60)
        
        # Health status
        health = results.get("health", {})
        print(f"🏥 Archive API Health: {health.get('archive', 'Unknown')}")
        print(f"🏥 FinSight API Health: {health.get('finsight', 'Unknown')}")
        print()
        
        # Archive API results
        archive_search = results.get("archive_search", {})
        archive_synthesis = results.get("archive_synthesis", {})
        print(f"🔍 Archive Search: {archive_search.get('status', 'Unknown')}")
        if archive_search.get('status') == 'success':
            print(f"   📊 Papers found: {archive_search.get('count', 0)}")
        print(f"📝 Archive Synthesis: {archive_synthesis.get('status', 'Unknown')}")
        if archive_synthesis.get('status') == 'success':
            print(f"   📊 Words generated: {archive_synthesis.get('word_count', 0)}")
        print()
        
        # FinSight API results
        finsight = results.get("finsight", {})
        print(f"💰 FinSight API: {finsight.get('status', 'Unknown')}")
        if finsight.get('status') == 'success':
            print(f"   📊 Data points: {finsight.get('data_points', 0)}")
        print()
        
        # Caching results
        caching = results.get("caching", {})
        print(f"⚡ Caching Performance:")
        print(f"   📊 First request: {caching.get('first_request_time', 0):.2f}s")
        print(f"   📊 Second request: {caching.get('second_request_time', 0):.2f}s")
        print(f"   📊 Speedup: {caching.get('cache_speedup', 0):.1f}x")
        print(f"   ✅ Caching working: {caching.get('caching_working', False)}")
        print()
        
        # Overall assessment
        success_count = 0
        total_tests = 0
        
        for test_name, test_result in results.items():
            if test_name == "health":
                for api, status in test_result.items():
                    total_tests += 1
                    if "healthy" in str(status):
                        success_count += 1
            elif isinstance(test_result, dict) and "status" in test_result:
                total_tests += 1
                if test_result["status"] == "success":
                    success_count += 1
        
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        print("🎯 OVERALL ASSESSMENT")
        print("=" * 60)
        print(f"✅ Tests passed: {success_count}/{total_tests}")
        print(f"📊 Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT! Archive API and AI Agent upgrades are working well!")
            print("🚀 Ready for production use!")
        elif success_rate >= 60:
            print("👍 GOOD! Most upgrades are working, some issues to address.")
        else:
            print("⚠️ NEEDS WORK! Several issues need to be resolved.")
        
        print("=" * 60)

async def main():
    """Main test function"""
    print("🧪 Nocturnal Archive Upgrade Test Suite")
    print("Testing Archive API and AI Agent improvements")
    print()
    
    async with UpgradeTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
