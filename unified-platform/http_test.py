#!/usr/bin/env python3
"""
HTTP Test - Test actual API endpoints
"""

import asyncio
import aiohttp
import json

async def test_endpoint(session, url, description):
    """Test a single endpoint"""
    print(f"🔍 Testing {description}...")
    print(f"   URL: {url}")
    
    try:
        async with session.get(url, timeout=10) as response:
            status = response.status
            print(f"   Status: {status}")
            
            if status == 200:
                data = await response.json()
                print(f"   ✅ Success!")
                
                # Check if it's real data
                if 'real_data' in data:
                    print(f"   Real data: {data['real_data']}")
                if 'source' in data:
                    print(f"   Source: {data['source']}")
                if 'data' in data:
                    print(f"   Data points: {len(data['data'])}")
                    
                return True
            else:
                text = await response.text()
                print(f"   ❌ Failed: {text[:100]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_all_endpoints():
    """Test all API endpoints"""
    print("🌐 HTTP API ENDPOINT TEST")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        health_ok = await test_endpoint(session, f"{base_url}/health", "Health Check")
        
        # Test FinSight endpoints
        finsight_ok = await test_endpoint(session, f"{base_url}/finsight/health", "FinSight Health")
        
        # Test Archive endpoints
        archive_ok = await test_endpoint(session, f"{base_url}/archive/health", "Archive Health")
        
        # Test actual data endpoints
        print("\n📊 Testing Data Endpoints...")
        
        # Test Apple revenue
        aapl_ok = await test_endpoint(session, f"{base_url}/finsight/kpis/AAPL/revenue?limit=2", "Apple Revenue")
        
        # Test Microsoft revenue
        msft_ok = await test_endpoint(session, f"{base_url}/finsight/kpis/MSFT/revenue?limit=2", "Microsoft Revenue")
        
        # Test archive search
        archive_search_ok = await test_endpoint(session, f"{base_url}/archive/search?query=machine+learning&limit=2", "Archive Search")
        
        print("\n" + "=" * 50)
        print("📊 HTTP TEST RESULTS:")
        print(f"Health: {'✅ OK' if health_ok else '❌ FAILED'}")
        print(f"FinSight Health: {'✅ OK' if finsight_ok else '❌ FAILED'}")
        print(f"Archive Health: {'✅ OK' if archive_ok else '❌ FAILED'}")
        print(f"Apple Revenue: {'✅ OK' if aapl_ok else '❌ FAILED'}")
        print(f"Microsoft Revenue: {'✅ OK' if msft_ok else '❌ FAILED'}")
        print(f"Archive Search: {'✅ OK' if archive_search_ok else '❌ FAILED'}")
        
        working_count = sum([health_ok, finsight_ok, archive_ok, aapl_ok, msft_ok, archive_search_ok])
        total_count = 6
        
        print(f"\n🎯 OVERALL: {working_count}/{total_count} endpoints working")
        
        if working_count == total_count:
            print("🎉 ALL ENDPOINTS WORKING!")
        elif working_count >= 4:
            print("⚠️ MOSTLY WORKING: Some endpoints need attention.")
        else:
            print("❌ MAJOR ISSUES: Most endpoints not working.")

async def main():
    """Run HTTP tests"""
    print("🚀 Starting HTTP API Tests...")
    print("Make sure the server is running on localhost:8000")
    print("Run: python3 start_real_server.py")
    print()
    
    await test_all_endpoints()

if __name__ == "__main__":
    asyncio.run(main())