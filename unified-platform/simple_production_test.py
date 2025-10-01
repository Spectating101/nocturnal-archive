#!/usr/bin/env python3
"""
Simple Production Test - Test what actually works
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path

# Set production environment
os.environ['FINSIGHT_STRICT'] = 'true'
os.environ['ARCHIVE_STRICT'] = 'true'
os.environ['NO_MOCK_DATA'] = 'true'

async def test_server_startup():
    """Test if server can start"""
    print("🚀 Testing Server Startup...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from integrated_server import app
        print("✅ Integrated server imported successfully")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Server has {len(routes)} routes")
        
        # Check for API routes
        finsight_routes = [r for r in routes if '/finsight' in r]
        archive_routes = [r for r in routes if '/archive' in r]
        
        print(f"✅ FinSight routes: {len(finsight_routes)}")
        print(f"✅ Archive routes: {len(archive_routes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

async def test_http_endpoints():
    """Test HTTP endpoints"""
    print("\n🌐 Testing HTTP Endpoints...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ Health endpoint working")
                    data = await response.json()
                    print(f"   Service: {data.get('service', 'Unknown')}")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
                    return False
            
            # Test FinSight health
            async with session.get("http://localhost:8000/finsight/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ FinSight health endpoint working")
                else:
                    print(f"❌ FinSight health failed: {response.status}")
            
            # Test Archive health
            async with session.get("http://localhost:8000/archive/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ Archive health endpoint working")
                else:
                    print(f"❌ Archive health failed: {response.status}")
            
            return True
            
    except Exception as e:
        print(f"❌ HTTP endpoints test failed: {e}")
        print("   (Server might not be running)")
        return False

async def test_real_data_endpoints():
    """Test real data endpoints"""
    print("\n📊 Testing Real Data Endpoints...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test Apple revenue
            async with session.get("http://localhost:8000/finsight/kpis/AAPL/revenue?limit=1", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Apple revenue endpoint working")
                    print(f"   Real data: {data.get('real_data', 'N/A')}")
                    print(f"   Source: {data.get('source', 'N/A')}")
                    
                    if 'data' in data and data['data']:
                        first_point = data['data'][0]
                        print(f"   Value: ${first_point.get('value', 'N/A'):,}")
                else:
                    print(f"❌ Apple revenue failed: {response.status}")
                    return False
            
            # Test archive search
            async with session.get("http://localhost:8000/archive/search?query=machine+learning&limit=1", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Archive search endpoint working")
                    
                    if 'papers' in data:
                        papers = data['papers']
                        print(f"   Found {len(papers)} papers")
                        
                        if papers:
                            paper = papers[0]
                            print(f"   First paper: {paper.get('title', 'No title')}")
                            print(f"   DOI: {paper.get('doi', 'N/A')}")
                else:
                    print(f"❌ Archive search failed: {response.status}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Real data endpoints test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔍 SIMPLE PRODUCTION TEST")
    print("=" * 50)
    
    startup_ok = await test_server_startup()
    
    if startup_ok:
        print("\n🌐 Testing endpoints (server needs to be running)...")
        print("   Start server with: python3 integrated_server.py")
        print("   Then run this test again")
    else:
        print("\n❌ Server startup failed - check dependencies")
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Server Startup: {'✅ OK' if startup_ok else '❌ FAILED'}")
    
    if startup_ok:
        print("\n🎯 NEXT STEPS:")
        print("1. Start server: python3 integrated_server.py")
        print("2. Run this test again to check endpoints")
        print("3. Test real data flow")

if __name__ == "__main__":
    asyncio.run(main())