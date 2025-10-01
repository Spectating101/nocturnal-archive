#!/usr/bin/env python3
"""
Production Test - Test real data flow end-to-end
"""

import asyncio
import sys
import os
from pathlib import Path

# Set production environment
os.environ['FINSIGHT_STRICT'] = 'true'
os.environ['ARCHIVE_STRICT'] = 'true'
os.environ['NO_MOCK_DATA'] = 'true'

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

async def test_production_sec():
    """Test production SEC data"""
    print("💰 Testing Production SEC Data...")
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        
        adapter = SECFactsAdapter()
        print(f"✅ SEC adapter created in production mode")
        
        # Test Apple revenue
        print("📊 Testing Apple (AAPL) revenue...")
        result = await adapter.get_fact("AAPL", "revenue")
        
        if result:
            print("✅ Production SEC data retrieved!")
            print(f"   Value: ${result.get('value', 'N/A'):,}")
            print(f"   Period: {result.get('period', 'N/A')}")
            print(f"   Source: {result.get('citation', {}).get('source', 'N/A')}")
            print(f"   URL: {result.get('citation', {}).get('url', 'N/A')}")
            
            # Verify it's real data
            citation = result.get('citation', {})
            if 'mock' in citation.get('source', '').lower():
                print("❌ Still getting mock data!")
                return False
            else:
                print("✅ Real SEC data confirmed!")
                return True
        else:
            print("❌ No SEC data returned")
            return False
            
    except Exception as e:
        print(f"❌ Production SEC test failed: {e}")
        return False

async def test_production_archive():
    """Test production Archive data"""
    print("\n📚 Testing Production Archive Data...")
    
    try:
        from src.services.paper_search import PaperSearcher
        
        searcher = PaperSearcher()
        print(f"✅ Archive searcher created in production mode")
        
        # Create request
        class SimpleRequest:
            def __init__(self, query, limit=2):
                self.query = query
                self.limit = limit
        
        request = SimpleRequest("machine learning", 2)
        print("🔍 Testing academic paper search...")
        
        result = await searcher.search_papers(request)
        
        if result and "papers" in result:
            papers = result["papers"]
            print(f"✅ Production archive data retrieved! Found {len(papers)} papers")
            
            for i, paper in enumerate(papers[:2], 1):
                print(f"📄 Paper {i}: {paper.get('title', 'No title')}")
                print(f"   DOI: {paper.get('doi', 'N/A')}")
                print(f"   Year: {paper.get('year', 'Unknown')}")
            
            # Verify it's real data
            if any(paper.get('doi', '').startswith('10.') for paper in papers):
                print("✅ Real academic data confirmed!")
                return True
            else:
                print("❌ Still getting mock data!")
                return False
        else:
            print("❌ No archive data returned")
            return False
            
    except Exception as e:
        print(f"❌ Production archive test failed: {e}")
        return False

async def test_production_endpoints():
    """Test production endpoints"""
    print("\n🌐 Testing Production Endpoints...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test health
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print("✅ Health endpoint working")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
                    return False
            
            # Test FinSight
            async with session.get("http://localhost:8000/finsight/kpis/AAPL/revenue?limit=1") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ FinSight endpoint working")
                    print(f"   Real data: {data.get('real_data', 'N/A')}")
                    print(f"   Source: {data.get('source', 'N/A')}")
                else:
                    print(f"❌ FinSight endpoint failed: {response.status}")
                    return False
            
            # Test Archive
            async with session.get("http://localhost:8000/archive/search?query=machine+learning&limit=1") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Archive endpoint working")
                    if 'papers' in data:
                        print(f"   Found {len(data['papers'])} papers")
                else:
                    print(f"❌ Archive endpoint failed: {response.status}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Production endpoints test failed: {e}")
        return False

async def main():
    """Run production tests"""
    print("🚀 PRODUCTION MODE TEST")
    print("=" * 50)
    
    sec_ok = await test_production_sec()
    archive_ok = await test_production_archive()
    endpoints_ok = await test_production_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 PRODUCTION TEST RESULTS:")
    print(f"SEC Data: {'✅ REAL' if sec_ok else '❌ MOCK'}")
    print(f"Archive Data: {'✅ REAL' if archive_ok else '❌ MOCK'}")
    print(f"Endpoints: {'✅ WORKING' if endpoints_ok else '❌ FAILED'}")
    
    working_count = sum([sec_ok, archive_ok, endpoints_ok])
    total_count = 3
    
    print(f"\n🎯 PRODUCTION READINESS: {working_count}/{total_count}")
    
    if working_count == total_count:
        print("🎉 PRODUCTION READY! All systems using real data.")
    elif working_count >= 2:
        print("⚠️ MOSTLY READY: Some components need attention.")
    else:
        print("❌ NOT READY: Major issues need resolution.")

if __name__ == "__main__":
    asyncio.run(main())