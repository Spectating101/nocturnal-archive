#!/usr/bin/env python3
"""
Simple Test - Check what actually works
"""

import sys
import os
from pathlib import Path

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

def test_imports():
    """Test if we can import the real components"""
    print("🔍 Testing Imports...")
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        print("✅ SECFactsAdapter imported successfully")
        
        adapter = SECFactsAdapter()
        print(f"✅ SECFactsAdapter instantiated: {type(adapter)}")
        
        # Check if it has the right methods
        if hasattr(adapter, 'get_fact'):
            print("✅ SECFactsAdapter has get_fact method")
        else:
            print("❌ SECFactsAdapter missing get_fact method")
            
        if hasattr(adapter, 'ticker_to_cik'):
            print(f"✅ SECFactsAdapter has ticker mapping: {len(adapter.ticker_to_cik)} tickers")
        else:
            print("❌ SECFactsAdapter missing ticker mapping")
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    try:
        from src.services.paper_search import PaperSearcher
        print("✅ PaperSearcher imported successfully")
        
        searcher = PaperSearcher()
        print(f"✅ PaperSearcher instantiated: {type(searcher)}")
        
    except Exception as e:
        print(f"❌ PaperSearcher import failed: {e}")
        return False
    
    return True

def test_unified_platform():
    """Test if the unified platform can import"""
    print("\n🔍 Testing Unified Platform...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.routes.finsight_real import FINSIGHT_AVAILABLE, sec_adapter
        print(f"✅ FinSight available: {FINSIGHT_AVAILABLE}")
        
        if sec_adapter:
            print(f"✅ SEC adapter available: {type(sec_adapter)}")
        else:
            print("❌ SEC adapter not available")
            
    except Exception as e:
        print(f"❌ Unified platform import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Simple Test - What Actually Works")
    print("=" * 50)
    
    imports_ok = test_imports()
    platform_ok = test_unified_platform()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Imports: {'✅ OK' if imports_ok else '❌ FAILED'}")
    print(f"Platform: {'✅ OK' if platform_ok else '❌ FAILED'}")
    
    if imports_ok and platform_ok:
        print("\n🎉 Everything looks good! Real APIs should work.")
    else:
        print("\n⚠️ Some issues found. Check the errors above.")

if __name__ == "__main__":
    main()