#!/usr/bin/env python3
"""
Test API Calls - Actually test if the APIs return real data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

async def test_sec_api():
    """Test actual SEC API call"""
    print("💰 Testing SEC API Call...")
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        
        adapter = SECFactsAdapter()
        print(f"✅ SEC adapter created: {type(adapter)}")
        
        # Test with Apple revenue
        print("📊 Testing Apple (AAPL) revenue...")
        result = await adapter.get_fact("AAPL", "revenue")
        
        if result:
            print("✅ SEC API call successful!")
            print(f"   Value: ${result.get('value', 'N/A'):,}")
            print(f"   Period: {result.get('period', 'N/A')}")
            print(f"   Unit: {result.get('unit', 'N/A')}")
            
            citation = result.get('citation', {})
            print(f"   Source: {citation.get('source', 'N/A')}")
            print(f"   URL: {citation.get('url', 'N/A')}")
            print(f"   Accession: {citation.get('accession', 'N/A')}")
            
            # Check if it's real data
            if 'mock' in citation.get('source', '').lower():
                print("⚠️ This is mock data")
                return False
            else:
                print("✅ This appears to be real SEC data")
                return True
        else:
            print("❌ SEC API call returned no data")
            return False
            
    except Exception as e:
        print(f"❌ SEC API test failed: {e}")
        return False

async def test_archive_api():
    """Test actual Archive API call"""
    print("\n📚 Testing Archive API Call...")
    
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
            print(f"✅ Archive API call successful! Found {len(papers)} papers")
            
            for i, paper in enumerate(papers[:2], 1):
                print(f"📄 Paper {i}: {paper.get('title', 'No title')}")
                print(f"   Authors: {len(paper.get('authors', []))} authors")
                print(f"   Year: {paper.get('year', 'Unknown')}")
                print(f"   Citations: {paper.get('citations_count', 'Unknown')}")
                print(f"   DOI: {paper.get('doi', 'N/A')}")
                print(f"   URL: {paper.get('pdf_url', 'N/A')}")
            
            # Check if it's real data
            if any(paper.get('doi', '').startswith('10.') for paper in papers):
                print("✅ This appears to be real academic data")
                return True
            else:
                print("⚠️ This appears to be mock data")
                return False
        else:
            print("❌ Archive API call returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Archive API test failed: {e}")
        return False

async def test_unified_platform():
    """Test unified platform integration"""
    print("\n🌙 Testing Unified Platform Integration...")
    
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
                print(f"✅ Unified platform SEC adapter works: ${result.get('value', 'N/A'):,}")
            else:
                print("❌ Unified platform SEC adapter returned no data")
        else:
            print("❌ SEC adapter not loaded in unified platform")
            
        if paper_searcher:
            print(f"✅ Paper searcher loaded: {type(paper_searcher)}")
        else:
            print("❌ Paper searcher not loaded in unified platform")
            
        return True
        
    except Exception as e:
        print(f"❌ Unified platform test failed: {e}")
        return False

async def main():
    """Run all API tests"""
    print("🔍 API CALLS TEST")
    print("=" * 50)
    
    sec_ok = await test_sec_api()
    archive_ok = await test_archive_api()
    platform_ok = await test_unified_platform()
    
    print("\n" + "=" * 50)
    print("📊 API TEST RESULTS:")
    print(f"SEC API: {'✅ WORKS' if sec_ok else '❌ FAILED'}")
    print(f"Archive API: {'✅ WORKS' if archive_ok else '❌ FAILED'}")
    print(f"Unified Platform: {'✅ WORKS' if platform_ok else '❌ FAILED'}")
    
    working_count = sum([sec_ok, archive_ok, platform_ok])
    total_count = 3
    
    print(f"\n🎯 OVERALL: {working_count}/{total_count} APIs working")
    
    if working_count == total_count:
        print("🎉 ALL APIs WORKING! Real data is accessible.")
    elif working_count >= 2:
        print("⚠️ MOSTLY WORKING: Some APIs need attention.")
    else:
        print("❌ MAJOR ISSUES: Most APIs not working.")

if __name__ == "__main__":
    asyncio.run(main())