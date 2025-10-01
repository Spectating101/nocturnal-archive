#!/usr/bin/env python3
"""
Quick Check - See what's actually working right now
"""

import requests
import json
import sys
import os
from pathlib import Path

def check_server():
    """Check if server is running"""
    print("🔍 Checking if server is running...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            data = response.json()
            print(f"   Service: {data.get('service', 'Unknown')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return False

def test_finsight():
    """Test FinSight endpoint"""
    print("\n💰 Testing FinSight...")
    
    try:
        # Test Apple revenue
        response = requests.get("http://localhost:8000/finsight/kpis/AAPL/revenue?limit=2", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ FinSight endpoint working!")
            print(f"   Ticker: {data.get('ticker', 'N/A')}")
            print(f"   KPI: {data.get('kpi', 'N/A')}")
            print(f"   Real data: {data.get('real_data', 'N/A')}")
            print(f"   Source: {data.get('source', 'N/A')}")
            
            if 'data' in data and data['data']:
                first_point = data['data'][0]
                print(f"   First data point: {first_point.get('period', 'N/A')} = ${first_point.get('value', 'N/A'):,}")
            
            return True
        else:
            print(f"❌ FinSight failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ FinSight error: {e}")
        return False

def test_archive():
    """Test Archive endpoint"""
    print("\n📚 Testing Archive...")
    
    try:
        # Test search
        response = requests.get("http://localhost:8000/archive/search?query=machine+learning&limit=2", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Archive endpoint working!")
            
            if 'papers' in data:
                papers = data['papers']
                print(f"   Found {len(papers)} papers")
                
                for i, paper in enumerate(papers[:2], 1):
                    print(f"   Paper {i}: {paper.get('title', 'No title')}")
                    print(f"      Authors: {len(paper.get('authors', []))} authors")
                    print(f"      Year: {paper.get('year', 'Unknown')}")
                    print(f"      DOI: {paper.get('doi', 'N/A')}")
            
            return True
        else:
            print(f"❌ Archive failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Archive error: {e}")
        return False

def check_imports():
    """Check if we can import the components"""
    print("\n🔍 Checking imports...")
    
    try:
        # Add the nocturnal-archive-api to the path
        sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')
        
        from src.adapters.sec_facts import SECFactsAdapter
        print("✅ SECFactsAdapter imported")
        
        from src.services.paper_search import PaperSearcher
        print("✅ PaperSearcher imported")
        
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.routes.finsight_real import FINSIGHT_AVAILABLE
        print(f"✅ FinSight available: {FINSIGHT_AVAILABLE}")
        
        from src.routes.archive_real import ARCHIVE_AVAILABLE
        print(f"✅ Archive available: {ARCHIVE_AVAILABLE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Run quick check"""
    print("🚀 QUICK CHECK - What's Actually Working")
    print("=" * 50)
    
    imports_ok = check_imports()
    server_ok = check_server()
    
    if server_ok:
        finsight_ok = test_finsight()
        archive_ok = test_archive()
    else:
        print("\n⚠️ Server not running - skipping endpoint tests")
        print("   To start server: python3 start_real_server.py")
        finsight_ok = False
        archive_ok = False
    
    print("\n" + "=" * 50)
    print("📊 QUICK CHECK RESULTS:")
    print(f"Imports: {'✅ OK' if imports_ok else '❌ FAILED'}")
    print(f"Server: {'✅ OK' if server_ok else '❌ FAILED'}")
    print(f"FinSight: {'✅ OK' if finsight_ok else '❌ FAILED'}")
    print(f"Archive: {'✅ OK' if archive_ok else '❌ FAILED'}")
    
    working_count = sum([imports_ok, server_ok, finsight_ok, archive_ok])
    total_count = 4
    
    print(f"\n🎯 OVERALL: {working_count}/{total_count} components working")
    
    if working_count == total_count:
        print("🎉 EVERYTHING WORKING! Real APIs are functional.")
    elif working_count >= 2:
        print("⚠️ PARTIAL SUCCESS: Some components work.")
    else:
        print("❌ MAJOR ISSUES: Most components not working.")

if __name__ == "__main__":
    main()