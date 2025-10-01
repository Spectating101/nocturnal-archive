#!/usr/bin/env python3
"""
Production Startup Script - Real Data Mode Only
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_production_environment():
    """Set up production environment"""
    print("🚀 Setting up Production Environment")
    print("=" * 50)
    
    # Force production mode
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['FINSIGHT_STRICT'] = 'true'
    os.environ['ARCHIVE_STRICT'] = 'true'
    os.environ['NO_MOCK_DATA'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['DEBUG'] = 'false'
    
    # Load production environment file if it exists
    env_file = Path(__file__).parent / '.env.production'
    if env_file.exists():
        print("✅ Loading production environment variables...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("⚠️ Production environment file not found, using defaults")
    
    # Verify critical settings
    print(f"✅ Environment: {os.environ.get('ENVIRONMENT', 'unknown')}")
    print(f"✅ FinSight Strict: {os.environ.get('FINSIGHT_STRICT', 'false')}")
    print(f"✅ Archive Strict: {os.environ.get('ARCHIVE_STRICT', 'false')}")
    print(f"✅ No Mock Data: {os.environ.get('NO_MOCK_DATA', 'false')}")
    print(f"✅ Debug Mode: {os.environ.get('DEBUG', 'true')}")

def verify_production_components():
    """Verify production components are available"""
    print("\n🔍 Verifying Production Components")
    print("=" * 50)
    
    # Add the nocturnal-archive-api to the path
    api_path = '/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/nocturnal-archive-api'
    if api_path not in sys.path:
        sys.path.insert(0, api_path)
    
    try:
        from src.adapters.sec_facts import SECFactsAdapter
        from src.services.paper_search import PaperSearcher
        print("✅ Real API components available")
        
        # Test strict mode
        adapter = SECFactsAdapter()
        if hasattr(adapter, 'get_fact'):
            print("✅ SEC adapter ready for production")
        else:
            print("❌ SEC adapter not ready")
            return False
            
        searcher = PaperSearcher()
        if hasattr(searcher, 'search_papers'):
            print("✅ Archive searcher ready for production")
        else:
            print("❌ Archive searcher not ready")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Production components not available: {e}")
        print(f"   API path: {api_path}")
        print(f"   Python path: {sys.path[:3]}...")
        return False

def start_production_server():
    """Start the production server"""
    print("\n🌙 Starting Production Server")
    print("=" * 50)
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from integrated_server import app
        print("✅ Production server imported successfully")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Server has {len(routes)} routes")
        
        # Check for real API routes
        finsight_routes = [r for r in routes if '/finsight' in r]
        archive_routes = [r for r in routes if '/archive' in r]
        
        print(f"✅ FinSight routes: {len(finsight_routes)}")
        print(f"✅ Archive routes: {len(archive_routes)}")
        
        # Start server
        print("\n🚀 Starting Production Server...")
        print("📍 Server: http://0.0.0.0:8000")
        print("📚 API Docs: http://0.0.0.0:8000/docs")
        print("🔍 Health: http://0.0.0.0:8000/health")
        print("")
        print("🎯 PRODUCTION MODE ENABLED:")
        print("   • Real SEC EDGAR data only")
        print("   • Real academic papers only")
        print("   • No mock data allowed")
        print("   • Strict error handling")
        print("")
        print("Press Ctrl+C to stop the server")
        print("")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            workers=1
        )
        
    except Exception as e:
        print(f"❌ Failed to start production server: {e}")
        return False

def main():
    """Main production startup"""
    print("🌙 NOCTURNAL PLATFORM - PRODUCTION MODE")
    print("=" * 60)
    
    # Set up environment
    setup_production_environment()
    
    # Verify components
    if not verify_production_components():
        print("❌ Production components not ready. Exiting.")
        return
    
    # Start server
    start_production_server()

if __name__ == "__main__":
    main()