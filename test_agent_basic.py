#!/usr/bin/env python3
"""
Basic agent test - works without API keys
Tests fast-path queries that don't require LLM calls
"""
import asyncio
import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from cite_agent.enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest

async def test_basic():
    """Test features that work without API keys"""
    print("="*80)
    print("BASIC AGENT TEST (No API keys required)")
    print("="*80)

    agent = EnhancedNocturnalAgent()
    try:
        print("\nInitializing agent...")
        try:
            await agent.initialize()
            print("✓ Agent initialized")
        except Exception as e:
            print(f"⚠️  Initialization: {e}")
            print("Continuing with fast-path tests...\n")

        # Test fast-path queries (work without LLM)
        fast_path_tests = [
            ("where are we?", "Should show current directory"),
            ("test", "Should acknowledge probe"),
        ]

        results = []

        for query, expectation in fast_path_tests:
            print(f"\n{'─'*80}")
            print(f"Query: {query}")
            print(f"Expected: {expectation}")

            try:
                response = await agent.process_request(ChatRequest(question=query))

                # Check quality
                is_error = "❌" in response.response
                is_helpful = len(response.response) > 0 and len(response.response) < 200

                print(f"\nResponse ({len(response.response)} chars):")
                print(f"  {response.response}")
                print(f"Tools: {response.tools_used}")

                if not is_error and is_helpful:
                    print("✅ PASS")
                    results.append(True)
                else:
                    print("⚠️  ISSUE")
                    results.append(False)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                results.append(False)
    finally:
        await agent.close()

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n{'='*80}")
    print(f"RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All basic tests passed")
        print("\nFast-path queries work correctly without API keys.")
        print("For full testing, set CEREBRAS_API_KEY or GROQ_API_KEY")
    else:
        print("⚠️  Some tests failed")

    print("="*80)

    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(test_basic())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
