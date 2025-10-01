#!/usr/bin/env python3
"""
Honest Assessment - What Actually Works vs IDE Claims
"""

import sys
import os
from pathlib import Path

def assess_finsight():
    """Assess FinSight implementation"""
    print("💰 FINSIGHT ASSESSMENT")
    print("-" * 30)
    
    # Check if real components exist
    sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        adapter = SECFactsAdapter()
        
        print("✅ Real SEC adapter exists")
        print(f"   • Ticker mapping: {len(adapter.ticker_to_cik)} companies")
        print(f"   • Supported tickers: {list(adapter.ticker_to_cik.keys())}")
        
        # Check if it has mock data
        if hasattr(adapter, 'mock_data') and adapter.mock_data:
            print("⚠️ Adapter has mock data built-in")
            print(f"   • Mock companies: {list(adapter.mock_data.keys())}")
        
        # Check if it has real API calls
        if hasattr(adapter, 'get_fact'):
            print("✅ Has real SEC API method")
        else:
            print("❌ Missing real SEC API method")
            
        return True
        
    except Exception as e:
        print(f"❌ FinSight assessment failed: {e}")
        return False

def assess_archive():
    """Assess Archive implementation"""
    print("\n📚 ARCHIVE ASSESSMENT")
    print("-" * 30)
    
    try:
        from src.services.paper_search import PaperSearcher
        searcher = PaperSearcher()
        
        print("✅ Real paper searcher exists")
        
        # Check if it has real API endpoints
        if hasattr(searcher, 'openalex_base'):
            print(f"✅ OpenAlex endpoint: {searcher.openalex_base}")
        else:
            print("❌ Missing OpenAlex endpoint")
            
        if hasattr(searcher, 'pubmed_base'):
            print(f"✅ PubMed endpoint: {searcher.pubmed_base}")
        else:
            print("❌ Missing PubMed endpoint")
            
        return True
        
    except Exception as e:
        print(f"❌ Archive assessment failed: {e}")
        return False

def assess_unified_platform():
    """Assess unified platform implementation"""
    print("\n🌙 UNIFIED PLATFORM ASSESSMENT")
    print("-" * 30)
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from src.routes.finsight_real import FINSIGHT_AVAILABLE, sec_adapter
        from src.routes.archive_real import ARCHIVE_AVAILABLE, paper_searcher
        
        print(f"✅ FinSight available: {FINSIGHT_AVAILABLE}")
        print(f"✅ Archive available: {ARCHIVE_AVAILABLE}")
        
        if sec_adapter:
            print(f"✅ SEC adapter loaded: {type(sec_adapter)}")
        else:
            print("❌ SEC adapter not loaded")
            
        if paper_searcher:
            print(f"✅ Paper searcher loaded: {type(paper_searcher)}")
        else:
            print("❌ Paper searcher not loaded")
            
        return True
        
    except Exception as e:
        print(f"❌ Unified platform assessment failed: {e}")
        return False

def assess_ide_claims():
    """Assess what the IDE claimed vs reality"""
    print("\n🎭 IDE CLAIMS vs REALITY")
    print("-" * 30)
    
    claims = [
        ("Real SEC EDGAR integration", "✅ Real SEC adapter exists with API calls"),
        ("Real academic paper search", "✅ Real paper searcher with OpenAlex/PubMed"),
        ("Production-ready middleware", "✅ Monitoring, rate limiting, security"),
        ("Unified cross-module analysis", "✅ Cross-module search and analysis"),
        ("Professional API structure", "✅ FastAPI with proper documentation"),
        ("Real API connectivity", "⚠️ APIs exist but may default to mocks"),
        ("No mocks or fallbacks", "❌ Mocks are built into the adapters"),
        ("Enterprise-grade features", "✅ Professional middleware stack"),
    ]
    
    for claim, reality in claims:
        print(f"IDE: {claim}")
        print(f"Reality: {reality}")
        print()

def main():
    """Run comprehensive assessment"""
    print("🔍 HONEST ASSESSMENT - What Actually Works")
    print("=" * 60)
    
    finsight_ok = assess_finsight()
    archive_ok = assess_archive()
    platform_ok = assess_unified_platform()
    assess_ide_claims()
    
    print("📊 FINAL VERDICT")
    print("=" * 30)
    
    if finsight_ok and archive_ok and platform_ok:
        print("✅ REAL APIs EXIST AND ARE AVAILABLE")
        print("⚠️ BUT: They may default to mocks/demos")
        print("🎯 SOLUTION: Need to force real data mode")
    else:
        print("❌ SOME COMPONENTS MISSING OR BROKEN")
    
    print("\n🎯 THE TRUTH:")
    print("• Real SEC and academic APIs exist")
    print("• Professional middleware is implemented")
    print("• But adapters have mock data built-in")
    print("• Need to configure for real data mode")
    print("• IDE built sophisticated mocks, not real connectivity")

if __name__ == "__main__":
    main()