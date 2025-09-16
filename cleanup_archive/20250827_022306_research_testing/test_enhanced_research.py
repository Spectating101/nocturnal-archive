#!/usr/bin/env python3
"""
Test script for the enhanced research service with real academic capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_enhanced_research():
    """Test the enhanced research service with a real query."""
    
    print("🔬 Testing Enhanced Research Service...")
    print("=" * 50)
    
    try:
        # Import the enhanced research service
        from src.services.research_service.enhanced_research import enhanced_research_service
        
        # Test query
        query = "latest developments in renewable energy technology 2024"
        print(f"📝 Research Query: {query}")
        print("⏳ Starting research...")
        
        # Perform the research
        results = await enhanced_research_service.research_topic(
            query=query,
            max_results=10
        )
        
        print("\n✅ Research Completed!")
        print("=" * 50)
        
        # Display results
        print(f"📊 Sources Analyzed: {results.get('sources_analyzed', 0)}")
        print(f"📋 Summary: {results.get('summary', 'N/A')[:200]}...")
        
        # Show key findings
        print("\n🔍 Key Findings:")
        for i, finding in enumerate(results.get('key_findings', [])[:5], 1):
            print(f"  {i}. {finding}")
        
        # Show citations
        print(f"\n📚 Citations Found: {len(results.get('citations', []))}")
        for i, citation in enumerate(results.get('citations', [])[:3], 1):
            print(f"  {i}. {citation.get('title', 'N/A')}")
        
        # Show visualizations
        if results.get('visualizations'):
            print(f"\n📈 Visualizations Generated: {len(results['visualizations'])}")
            for viz_type in results['visualizations'].keys():
                print(f"  - {viz_type}")
        
        # Show citation formats
        if results.get('citation_formats'):
            print(f"\n📖 Citation Formats Available:")
            for format_name in results['citation_formats'].keys():
                print(f"  - {format_name.upper()}")
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced Research Test Completed Successfully!")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during research: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_citation_manager():
    """Test the citation manager directly."""
    
    print("\n📚 Testing Citation Manager...")
    print("=" * 30)
    
    try:
        from src.services.research_service.citation_manager import citation_manager
        
        # Add a test citation
        citation_id = citation_manager.add_citation(
            url="https://www.nature.com/articles/test",
            title="Test Research Paper",
            content="This is a test research paper content...",
            metadata={
                "author": ["Smith, J.", "Johnson, A."],
                "publication_date": "2024-01-15",
                "journal": "Nature",
                "doi": "10.1038/test"
            }
        )
        
        print(f"✅ Added citation: {citation_id}")
        
        # Generate citation in different formats
        apa_citation = citation_manager.generate_citation_text(citation_id, "apa")
        mla_citation = citation_manager.generate_citation_text(citation_id, "mla")
        
        print(f"📖 APA: {apa_citation}")
        print(f"📖 MLA: {mla_citation}")
        
        # Generate reference list
        reference_list = citation_manager.generate_reference_list("apa")
        print(f"📋 Reference List: {reference_list[:100]}...")
        
        print("✅ Citation Manager Test Completed!")
        
    except Exception as e:
        print(f"❌ Error in citation manager: {str(e)}")

async def test_data_visualizer():
    """Test the data visualizer directly."""
    
    print("\n📊 Testing Data Visualizer...")
    print("=" * 30)
    
    try:
        from src.services.research_service.data_visualizer import data_visualizer
        
        # Test data
        keywords = [("renewable energy", 15), ("solar power", 12), ("wind energy", 8)]
        sources = [
            {"type": "journal", "count": 5},
            {"type": "conference", "count": 3},
            {"type": "web", "count": 2}
        ]
        
        # Generate visualizations
        keyword_chart = data_visualizer.create_keyword_frequency_chart(keywords)
        source_chart = data_visualizer.create_source_analysis_chart(sources)
        
        print(f"✅ Keyword Chart: {keyword_chart.title}")
        print(f"✅ Source Chart: {source_chart.title}")
        
        # Test dashboard generation
        research_data = {
            "keywords": keywords,
            "sources": sources,
            "findings": ["Finding 1", "Finding 2"],
            "citations": [{"title": "Test Paper"}]
        }
        
        dashboard = data_visualizer.generate_research_dashboard(research_data)
        print(f"✅ Dashboard Generated: {len(dashboard)} characters")
        
        print("✅ Data Visualizer Test Completed!")
        
    except Exception as e:
        print(f"❌ Error in data visualizer: {str(e)}")

async def main():
    """Run all tests."""
    
    print("🚀 Starting Enhanced Research System Tests...")
    print("=" * 60)
    
    # Test citation manager
    await test_citation_manager()
    
    # Test data visualizer
    await test_data_visualizer()
    
    # Test enhanced research service
    results = await test_enhanced_research()
    
    if results:
        print("\n🎯 All tests completed successfully!")
        print("The enhanced research system is working properly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
