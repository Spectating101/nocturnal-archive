#!/usr/bin/env python3
"""
Test Real APIs - Verify FinSight and Archive are actually working
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

async def test_finsight():
    """Test real FinSight API"""
    print("🔍 Testing Real FinSight API...")
    
    try:
        from src.adapters.sec_company_facts import SECCompanyFactsAdapter
        
        adapter = SECCompanyFactsAdapter()
        
        # Test with Apple
        print("📊 Fetching Apple (AAPL) financial data from SEC...")
        data = await adapter.get_company_facts("AAPL")
        
        if data and "facts" in data:
            print(f"✅ Success! Found {len(data['facts'])} fact categories")
            
            # Show some revenue data
            for concept, periods in data["facts"].items():
                if "revenue" in concept.lower():
                    print(f"📈 Found revenue data: {concept}")
                    for period, values in list(periods.items())[:3]:  # Show first 3 periods
                        if isinstance(values, list) and values:
                            print(f"   {period}: ${values[0]['val']:,} {values[0].get('unit', 'USD')}")
                    break
        else:
            print("❌ No data found")
            
    except Exception as e:
        print(f"❌ FinSight test failed: {e}")

async def test_archive():
    """Test real Archive API"""
    print("\n🔍 Testing Real Archive API...")
    
    try:
        from src.services.paper_search import PaperSearcher
        
        searcher = PaperSearcher()
        
        # Test with a simple query
        print("📚 Searching for papers on 'machine learning'...")
        
        # Create a simple request object
        class SimpleRequest:
            def __init__(self, query, limit=3):
                self.query = query
                self.limit = limit
        
        request = SimpleRequest("machine learning", 3)
        result = await searcher.search_papers(request)
        
        if result and "papers" in result:
            papers = result["papers"]
            print(f"✅ Success! Found {len(papers)} papers")
            
            for i, paper in enumerate(papers[:2], 1):  # Show first 2 papers
                print(f"📄 Paper {i}: {paper.get('title', 'No title')}")
                print(f"   Authors: {', '.join([author.get('name', 'Unknown') for author in paper.get('authors', [])])}")
                print(f"   Year: {paper.get('year', 'Unknown')}")
                print(f"   Citations: {paper.get('citations_count', 'Unknown')}")
        else:
            print("❌ No papers found")
            
    except Exception as e:
        print(f"❌ Archive test failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Testing Real APIs Integration")
    print("=" * 50)
    
    await test_finsight()
    await test_archive()
    
    print("\n" + "=" * 50)
    print("✅ Real API testing complete!")

if __name__ == "__main__":
    asyncio.run(main())