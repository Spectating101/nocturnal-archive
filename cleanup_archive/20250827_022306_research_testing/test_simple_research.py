#!/usr/bin/env python3
"""
Simple test for core research functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_core_research():
    """Test the core research functionality."""
    
    print("🔬 Testing Core Research Functionality...")
    print("=" * 50)
    
    try:
        # Import the search engine directly
        from src.services.search_service.search_engine import SearchEngine
        from src.storage.db.operations import DatabaseOperations
        
        # Initialize database operations
        db_ops = DatabaseOperations(
            os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/nocturnal_archive'),
            os.environ.get('REDIS_URL', 'redis://localhost:6379')
        )
        
        # Initialize search engine
        search_engine = SearchEngine(db_ops, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        
        # Test web search
        query = "renewable energy technology 2024"
        print(f"📝 Search Query: {query}")
        print("⏳ Performing web search...")
        
        web_results = await search_engine.web_search(query, num_results=5)
        
        print(f"✅ Web Search Results: {len(web_results)} sources found")
        
        for i, result in enumerate(web_results[:3], 1):
            print(f"  {i}. {result.get('title', 'No title')}")
            print(f"     URL: {result.get('url', 'No URL')}")
            print(f"     Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            print()
        
        # Test academic search if available
        try:
            from src.services.paper_service.openalex import OpenAlexClient
            
            print("⏳ Performing academic search...")
            async with OpenAlexClient() as openalex:
                academic_results = await openalex.search_works(query, per_page=5)
                
                if academic_results and "results" in academic_results:
                    print(f"✅ Academic Search Results: {len(academic_results['results'])} papers found")
                    
                    for i, paper in enumerate(academic_results['results'][:3], 1):
                        title = paper.get('title', 'No title')
                        authors = paper.get('authorships', [])
                        author_names = [author.get('author', {}).get('display_name', 'Unknown') for author in authors[:3]]
                        
                        print(f"  {i}. {title}")
                        print(f"     Authors: {', '.join(author_names)}")
                        print(f"     DOI: {paper.get('doi', 'No DOI')}")
                        print()
                else:
                    print("⚠️  No academic results found")
                    
        except Exception as e:
            print(f"⚠️  Academic search not available: {e}")
        
        print("✅ Core Research Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during research: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_citation_system():
    """Test the citation system."""
    
    print("\n📚 Testing Citation System...")
    print("=" * 30)
    
    try:
        from src.services.research_service.citation_manager import citation_manager
        
        # Add a test citation
        citation_id = citation_manager.add_citation(
            url="https://www.nature.com/articles/renewable-energy-2024",
            title="Advances in Renewable Energy Technology",
            content="This paper discusses the latest developments in renewable energy...",
            metadata={
                "author": ["Smith, J.", "Johnson, A.", "Brown, M."],
                "publication_date": "2024-01-15",
                "journal": "Nature Energy",
                "doi": "10.1038/s41560-024-00001-x",
                "volume": "9",
                "issue": "2",
                "pages": "45-67"
            }
        )
        
        print(f"✅ Added citation: {citation_id}")
        
        # Test different citation formats
        formats = ["apa", "mla", "chicago", "ieee"]
        
        for fmt in formats:
            citation_text = citation_manager.generate_citation_text(citation_id, fmt)
            print(f"📖 {fmt.upper()}: {citation_text}")
        
        # Test reference list
        reference_list = citation_manager.generate_reference_list("apa")
        print(f"\n📋 APA Reference List:\n{reference_list}")
        
        print("✅ Citation System Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in citation system: {str(e)}")
        return False

async def main():
    """Run the tests."""
    
    print("🚀 Starting Core Research System Tests...")
    print("=" * 60)
    
    # Test citation system
    citation_success = await test_citation_system()
    
    # Test core research
    research_success = await test_core_research()
    
    if citation_success and research_success:
        print("\n🎯 All core tests completed successfully!")
        print("The research system is working properly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
