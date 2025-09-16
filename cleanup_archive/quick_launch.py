#!/usr/bin/env python3
"""
Quick Launch - Nocturnal Archive Demo
Demonstrates the full system capabilities in one comprehensive demo
"""

import asyncio
import subprocess
import sys
from pathlib import Path

async def quick_launch_demo():
    """Quick launch demo of the full Nocturnal Archive system"""
    print("🚀 NOCTURNAL ARCHIVE - QUICK LAUNCH DEMO")
    print("=" * 60)
    print()
    
    print("🎯 What You're About to Experience:")
    print("• 📚 Research paper analysis with citation tracking")
    print("• 🎯 Consensus building from multiple studies")
    print("• 📊 Data visualization and chart generation")
    print("• 📄 Academic export with proper citations")
    print("• 🤖 Interactive chatbot interface")
    print("• 🌐 Web-based UI (if available)")
    print()
    
    # Check if we can run the enhanced chatbot
    try:
        print("🤖 Starting Enhanced Chatbot Interface...")
        from enhanced_chatbot_interface import EnhancedChatbotInterface
        
        chatbot = EnhancedChatbotInterface()
        
        # Start research session
        session = await chatbot.start_research_session("Machine Learning in Drug Discovery")
        print(session["message"])
        print()
        
        # Run through the full workflow
        commands = [
            "analyze papers",
            "build consensus",
            "create chart", 
            "show citations",
            "export academic"
        ]
        
        print("🔄 Running Complete Research Workflow...")
        print("-" * 40)
        
        for command in commands:
            print(f"\n🤖 Command: {command}")
            response = await chatbot.process_user_input(command)
            
            # Show key results
            if "papers_analyzed" in response:
                print(f"   ✅ Papers analyzed: {response['papers_analyzed']}")
            if "consensus_findings" in response:
                print(f"   ✅ Consensus findings: {len(response['consensus_findings'])}")
            if "charts_created" in response:
                print(f"   ✅ Charts created: {len(response['charts_created'])}")
            if "export_file" in response:
                print(f"   ✅ Export file: {response['export_file']}")
            
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("🎉 COMPLETE WORKFLOW DEMONSTRATION FINISHED!")
        print()
        print("📊 What Was Accomplished:")
        print("• ✅ Paper analysis with citation extraction")
        print("• ✅ Consensus building from multiple studies")
        print("• ✅ Data visualization generation")
        print("• ✅ Citation analysis and formatting")
        print("• ✅ Academic export with proper citations")
        print()
        print("🚀 Ready for Production Launch!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    
    except Exception as e:
        print(f"❌ Error during demo: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS FOR LAUNCH:")
    print("1. Run: python launch_nocturnal.py (Full system launch)")
    print("2. Run: python enhanced_chatbot_interface.py (Chatbot demo)")
    print("3. Run: python consensus_citation_demo.py (Citation system)")
    print("4. Access web UI: http://localhost:3000 (if available)")
    print("5. Access API docs: http://localhost:8000/docs (if available)")

if __name__ == "__main__":
    asyncio.run(quick_launch_demo())
