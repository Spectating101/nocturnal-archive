#!/usr/bin/env python3
"""
Start Real Server - Uses actual FinSight and Archive APIs
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the nocturnal-archive-api to the path
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start the server with real APIs"""
    print("🚀 Starting Real API Server")
    print("=" * 50)
    
    # Check if we have the real components
    try:
        from src.adapters.sec_company_facts import SECCompanyFactsAdapter
        from src.services.paper_search import PaperSearcher
        print("✅ Real FinSight and Archive components available")
    except ImportError as e:
        print(f"❌ Real components not available: {e}")
        print("⚠️ Server will start with fallback components")
    
    # Start the integrated server
    print("🌙 Starting Integrated Nocturnal Platform Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("")
    print("🚀 REAL APIs ENABLED:")
    print("   • FinSight: SEC EDGAR integration")
    print("   • Archive: OpenAlex/PubMed integration")
    print("   • No mocks, no fallbacks - just real data!")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    # Import and run the integrated server
    from integrated_server import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()