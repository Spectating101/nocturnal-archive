#!/usr/bin/env python3
"""
Quick test script to evaluate agent responses
Run: python3 test_agent_live.py
"""
import asyncio
import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use existing API keys from environment, or skip if not available
if not os.getenv('CEREBRAS_API_KEY') and not os.getenv('GROQ_API_KEY'):
    print("⚠️  No API keys found in environment")
    print("Set CEREBRAS_API_KEY or GROQ_API_KEY to run tests")
    print("Or the agent will try to use backend mode")
    print()

from cite_agent.enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest

async def test_queries():
    """Test specific queries and show results"""
    agent = EnhancedNocturnalAgent()

    # Initialize agent
    print("Initializing agent...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return
    print("✓ Agent initialized\n")

    test_queries = [
        "where are we?",
        "what python files are in this directory?",
        "test",
        "show me setup.py",
        "what's the version number?",
    ]

    print("="*80)
    print("AGENT LIVE TEST")
    print("="*80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}: {query}")
        print(f"{'─'*80}")

        try:
            # Send query
            response = await agent.process_request(ChatRequest(question=query))

            print(f"\n🤖 Response ({len(response.response)} chars):")
            print(response.response)
            print(f"\n🔧 Tools used: {response.tools_used}")

            # Evaluate
            is_helpful = (
                not any(bad in response.response.lower() for bad in
                       ["you can run", "try running", "please run"]) and
                len(response.response) < 500 and
                not response.response.startswith("❌")
            )

            if is_helpful:
                print("✅ GOOD - Helpful response")
            else:
                print("⚠️ ISSUE - Check response quality")

        except Exception as e:
            print(f"❌ ERROR: {e}")

        await asyncio.sleep(0.5)

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_queries())
