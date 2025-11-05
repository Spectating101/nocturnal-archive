#!/usr/bin/env python3
"""
Test agent with proper initialization
"""
import asyncio
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT))

# Use existing API keys from environment
if not os.getenv('CEREBRAS_API_KEY') and not os.getenv('GROQ_API_KEY'):
    print("⚠️  No API keys found - tests will use backend mode or fail")
    print("Set CEREBRAS_API_KEY or GROQ_API_KEY for full testing")

from cite_agent.enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest

async def test_with_proper_init():
    """Test with full initialization"""
    print("="*80)
    print("AGENT TEST WITH PROPER INITIALIZATION")
    print("="*80)

    agent = EnhancedNocturnalAgent()

    # Initialize properly
    print("\nInitializing agent...")
    success = await agent.initialize()
    print(f"Initialization: {'✓ Success' if success else '✗ Failed'}")

    if not success:
        print("❌ Cannot test - initialization failed")
        return False

    # Test queries
    test_cases = [
        ("where are we?", "Should show directory"),
        ("what python files are here?", "Should list files"),
        ("test", "Should respond naturally"),
        ("show me setup.py", "Should read file"),
        ("what's the version?", "Should find version"),
    ]

    scores = []

    for query, expectation in test_cases:
        print(f"\n{'─'*80}")
        print(f"Query: {query}")
        print(f"Expected: {expectation}")

        try:
            response = await agent.process_request(ChatRequest(question=query))

            # Evaluate quality
            has_error = "❌" in response.response
            is_asking_user = any(p in response.response.lower() for p in
                               ["you can run", "try running", "please run", "you should"])
            is_verbose = len(response.response) > 600
            used_tools = bool(response.tools_used and response.tools_used != ['quick_reply'])

            # Score
            score = 0
            if not has_error:
                score += 50
            if not is_asking_user:
                score += 30
            if not is_verbose:
                score += 20

            print(f"\nResponse ({len(response.response)} chars):")
            print(f"  {response.response[:250]}")
            if len(response.response) > 250:
                print("  ...")
            print(f"Tools: {response.tools_used}")
            print(f"Score: {score}/100")

            if score >= 80:
                print("✅ EXCELLENT")
            elif score >= 60:
                print("⚠️ ACCEPTABLE")
            else:
                print("❌ POOR")

            scores.append(score)

        except Exception as e:
            print(f"❌ Error: {e}")
            scores.append(0)

        await asyncio.sleep(0.3)

    # Overall
    avg = sum(scores) / len(scores) if scores else 0
    print(f"\n{'='*80}")
    print(f"OVERALL SCORE: {avg:.1f}/100")

    if avg >= 85:
        print("✅ EXCELLENT - Claude-level intelligence")
        verdict = True
    elif avg >= 70:
        print("⚠️ GOOD - Capable but not quite Claude-level")
        verdict = False
    elif avg >= 50:
        print("⚠️ MEDIOCRE - Needs improvement")
        verdict = False
    else:
        print("❌ POOR - Major issues")
        verdict = False
    print("="*80)

    return verdict

if __name__ == "__main__":
    try:
        success = asyncio.run(test_with_proper_init())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
