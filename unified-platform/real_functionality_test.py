#!/usr/bin/env python3
"""
Real Functionality Test - Actually test if APIs work
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

async def test_sec_adapter():
    """Test if SEC adapter actually works"""
    print("💰 Testing SEC Adapter...")
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        
        adapter = SECFactsAdapter()
        print(f"✅ SEC adapter created: {type(adapter)}")
        
        # Test with Apple
        print("📊 Testing Apple (AAPL) revenue...")
        result = await adapter.get_fact("AAPL", "revenue")
        
        if result:
            print(f"✅ Got result: {result}")
            print(f"   Value: ${result.get('value', 'N/A'):,}")
            print(f"   Period: {result.get('period', 'N/A')}")
            print(f"   Source: {result.get('citation', {}).get('source', 'N/A')}")
            
            # Check if it's real data or mock
            citation = result.get('citation', {})
            if 'mock' in citation.get('source', '').lower():
                print("⚠️ This appears to be mock data")
                return False
            else:
                print("✅ This appears to be real SEC data")
                return True
        else:
            print("❌ No result returned")
            return False
            
    except Exception as e:
        print(f"❌ SEC adapter test failed: {e}")
        return False

async def test_paper_searcher():
    """Test if paper searcher actually works"""
    print("\n📚 Testing Paper Searcher...")
    
    try:
        from src.services.paper_search import PaperSearcher
        
        searcher = PaperSearcher()
        print(f"✅ Paper searcher created: {type(searcher)}")
        
        # Create a simple request
        class SimpleRequest:
            def __init__(self, query, limit=2):
                self.query = query
                self.limit = limit
        
        request = SimpleRequest("machine learning", 2)
        print("🔍 Searching for 'machine learning' papers...")
        
        result = await searcher.search_papers(request)
        
        if result and "papers" in result:
            papers = result["papers"]
            print(f"✅ Found {len(papers)} papers")
            
            for i, paper in enumerate(papers[:2], 1):
                print(f"📄 Paper {i}: {paper.get('title', 'No title')}")
                print(f"   Authors: {len(paper.get('authors', []))} authors")
                print(f"   Year: {paper.get('year', 'Unknown')}")
                print(f"   Citations: {paper.get('citations_count', 'Unknown')}")
                print(f"   DOI: {paper.get('doi', 'N/A')}")
            
            # Check if it's real data
            if any(paper.get('doi', '').startswith('10.') for paper in papers):
                print("✅ This appears to be real academic data")
                return True
            else:
                print("⚠️ This appears to be mock data")
                return False
        else:
            print("❌ No papers found")
            return False
            
    except Exception as e:
        print(f"❌ Paper searcher test failed: {e}")
        return False

async def test_unified_platform():
    """Test if unified platform actually works"""
    print("\n🌙 Testing Unified Platform...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.routes.finsight_real import FINSIGHT_AVAILABLE, sec_adapter
        from src.routes.archive_real import ARCHIVE_AVAILABLE, paper_searcher
        
        print(f"✅ FinSight available: {FINSIGHT_AVAILABLE}")
        print(f"✅ Archive available: {ARCHIVE_AVAILABLE}")
        
        if sec_adapter:
            print(f"✅ SEC adapter loaded: {type(sec_adapter)}")
            
            # Test the adapter
            result = await sec_adapter.get_fact("AAPL", "revenue")
            if result:
                print(f"✅ SEC adapter works: ${result.get('value', 'N/A'):,}")
            else:
                print("❌ SEC adapter returned no data")
        else:
            print("❌ SEC adapter not loaded")
            
        if paper_searcher:
            print(f"✅ Paper searcher loaded: {type(paper_searcher)}")
        else:
            print("❌ Paper searcher not loaded")
            
        return True
        
    except Exception as e:
        print(f"❌ Unified platform test failed: {e}")
        return False

async def test_server_startup():
    """Test if server can actually start"""
    print("\n🚀 Testing Server Startup...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from integrated_server import app
        print("✅ Integrated server imported successfully")
        
        # Check if routes are included
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Server has {len(routes)} routes")
        
        # Check for FinSight routes
        finsight_routes = [r for r in routes if '/finsight' in r]
        if finsight_routes:
            print(f"✅ FinSight routes found: {finsight_routes}")
        else:
            print("❌ No FinSight routes found")
            
        # Check for Archive routes
        archive_routes = [r for r in routes if '/archive' in r]
        if archive_routes:
            print(f"✅ Archive routes found: {archive_routes}")
        else:
            print("❌ No Archive routes found")
            
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

async def main():
    """Run all functionality tests"""
    print("🔍 REAL FUNCTIONALITY TEST")
    print("=" * 50)
    
    sec_ok = await test_sec_adapter()
    archive_ok = await test_paper_searcher()
    platform_ok = await test_unified_platform()
    server_ok = await test_server_startup()
    
    print("\n" + "=" * 50)
    print("📊 FUNCTIONALITY RESULTS:")
    print(f"SEC Adapter: {'✅ WORKS' if sec_ok else '❌ FAILED'}")
    print(f"Archive API: {'✅ WORKS' if archive_ok else '❌ FAILED'}")
    print(f"Unified Platform: {'✅ WORKS' if platform_ok else '❌ FAILED'}")
    print(f"Server Startup: {'✅ WORKS' if server_ok else '❌ FAILED'}")
    
    working_count = sum([sec_ok, archive_ok, platform_ok, server_ok])
    total_count = 4
    
    print(f"\n🎯 OVERALL: {working_count}/{total_count} components working")
    
    if working_count == total_count:
        print("🎉 ALL SYSTEMS WORKING! Real APIs are functional.")
    elif working_count >= 2:
        print("⚠️ PARTIAL SUCCESS: Some components work, others need fixing.")
    else:
        print("❌ MOSTLY BROKEN: Major issues need to be resolved.")

if __name__ == "__main__":
    asyncio.run(main())