#!/usr/bin/env python3
"""
Final comprehensive autonomy test - Like talking to Claude
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

async def test_like_claude():
    """Test if agent behaves like Claude"""
    print("="*80)
    print("FINAL AUTONOMY TEST: Is this agent as good as Claude?")
    print("="*80)

    agent = EnhancedNocturnalAgent()
    await agent.initialize()

    # Real user scenarios
    scenarios = [
        {
            "query": "hmm, where are we right now?",
            "expectation": "Natural location response, no robot speak",
            "bad_patterns": ["i'm cite agent", "my capabilities", "persistent shell"],
            "max_length": 150
        },
        {
            "query": "just testing",
            "expectation": "Quick natural acknowledgment",
            "bad_patterns": ["demonstrate", "example", "i can help with"],
            "max_length": 100
        },
        {
            "query": "what files are here",
            "expectation": "Lists files, doesn't ask me to run ls",
            "bad_patterns": ["you can run", "try running", "please check"],
            "max_length": 500
        },
        {
            "query": "show me the README",
            "expectation": "Reads and shows README content",
            "bad_patterns": ["cannot read", "you should", "try opening"],
            "max_length": 2000
        },
        {
            "query": "find the version number",
            "expectation": "Finds and tells me the version",
            "bad_patterns": ["you can check", "try looking", "please search"],
            "max_length": 300
        },
        {
            "query": "tell me about this project quickly",
            "expectation": "Reads files and summarizes, doesn't lecture",
            "bad_patterns": ["i'm cite agent", "i have access", "let me explain"],
            "max_length": 800
        },
        {
            "query": "are there any test files?",
            "expectation": "Searches and answers yes/no with examples",
            "bad_patterns": ["you can check", "try looking"],
            "max_length": 400
        },
    ]

    scores = []
    passed = 0
    total = len(scenarios)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}/{total}: {scenario['query']}")
        print(f"Expected: {scenario['expectation']}")

        try:
            response = await agent.process_request(ChatRequest(question=scenario['query']))

            # Evaluate
            issues = []
            score = 100

            # Length check
            if len(response.response) > scenario['max_length']:
                excess = len(response.response) - scenario['max_length']
                penalty = min(30, (excess // 100) * 10)
                score -= penalty
                issues.append(f"Too verbose ({len(response.response)} > {scenario['max_length']})")

            # Bad patterns check
            text_lower = response.response.lower()
            for pattern in scenario['bad_patterns']:
                if pattern in text_lower:
                    score -= 20
                    issues.append(f"Contains: '{pattern}'")

            # Error check
            if response.response.startswith("❌"):
                score -= 40
                issues.append("Error response")

            # Tool intelligence check
            asking_patterns = ["you can run", "try running", "you should", "please run"]
            for pattern in asking_patterns:
                if pattern in text_lower:
                    score -= 25
                    issues.append(f"Asking user: '{pattern}'")

            score = max(0, score)

            # Display
            print(f"\nResponse ({len(response.response)} chars):")
            preview = response.response[:200]
            if len(response.response) > 200:
                preview += "..."
            print(f"  {preview}")
            print(f"Tools: {response.tools_used}")
            print(f"Score: {score}/100")

            if score >= 90:
                print("✅ CLAUDE-LEVEL")
                passed += 1
            elif score >= 75:
                print("⚠️ GOOD")
            elif score >= 60:
                print("⚠️ MEDIOCRE")
            else:
                print("❌ POOR")

            if issues:
                print("Issues:")
                for issue in issues:
                    print(f"  • {issue}")

            scores.append(score)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            scores.append(0)

        await asyncio.sleep(0.3)

    # Final verdict
    avg = sum(scores) / len(scores) if scores else 0

    print(f"\n{'='*80}")
    print("FINAL VERDICT")
    print(f"{'='*80}")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Average Score: {avg:.1f}/100")

    if avg >= 90 and passed >= total * 0.8:
        print("\n✅✅✅ YES - Agent is as smart and conversational as Claude")
        print("The agent:")
        print("  • Understands intent naturally")
        print("  • Takes action without asking permission")
        print("  • Responds concisely and helpfully")
        print("  • Uses tools intelligently")
        print("  • Doesn't over-explain or lecture")
        verdict = True
    elif avg >= 80:
        print("\n⚠️ ALMOST - Agent is very good but not quite Claude-level")
        print("Minor issues need addressing")
        verdict = False
    elif avg >= 65:
        print("\n⚠️ DECENT - Agent works but needs improvement")
        verdict = False
    else:
        print("\n❌ NO - Agent is not sophisticated enough")
        verdict = False

    print(f"{'='*80}\n")

    return verdict

if __name__ == "__main__":
    try:
        success = asyncio.run(test_like_claude())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(1)
