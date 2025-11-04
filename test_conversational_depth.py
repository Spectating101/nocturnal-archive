#!/usr/bin/env python3
"""
Deep Conversational Intelligence Test
Tests multi-turn conversations, clarifications, follow-ups, tone consistency
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT))

# Load .env.local if it exists
from dotenv import load_dotenv
env_file = ROOT / '.env.local'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded {env_file}")

# Force local keys mode
os.environ['USE_LOCAL_KEYS'] = 'true'

# Use real API keys from environment
if not os.getenv('CEREBRAS_API_KEY') and not os.getenv('GROQ_API_KEY'):
    print("⚠️  No API keys found - set CEREBRAS_API_KEY or GROQ_API_KEY")
    sys.exit(1)

print(f"✓ Using local API keys mode (USE_LOCAL_KEYS={os.getenv('USE_LOCAL_KEYS')})")

from cite_agent.enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest

class ConversationTester:
    def __init__(self):
        self.agent = None
        self.results = []

    async def setup(self):
        """Initialize agent"""
        self.agent = EnhancedNocturnalAgent()
        await self.agent.initialize()
        print("✓ Agent initialized\n")

    async def run_conversation(self, scenario_name: str, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a multi-turn conversation and evaluate quality"""
        print(f"{'='*80}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'='*80}\n")

        conversation_history = []
        issues = []
        scores = []

        for i, turn in enumerate(turns, 1):
            query = turn['query']
            expected = turn.get('expected', {})

            print(f"{'─'*80}")
            print(f"TURN {i}/{len(turns)}: {query}")
            print(f"{'─'*40}")

            try:
                response = await self.agent.process_request(
                    ChatRequest(question=query, conversation_id=f"test_{scenario_name}")
                )

                conversation_history.append({
                    'query': query,
                    'response': response.response,
                    'tools': response.tools_used
                })

                # Evaluate this turn
                turn_score = 100
                turn_issues = []

                # Check 1: Response exists and not error
                if not response.response or response.response.startswith("❌"):
                    turn_issues.append("Error or no response")
                    turn_score -= 40

                # Check 2: Length appropriate
                max_len = expected.get('max_length', 800)
                if len(response.response) > max_len:
                    turn_issues.append(f"Too verbose ({len(response.response)} > {max_len})")
                    turn_score -= 20

                # Check 3: Should use tools?
                should_use_tools = expected.get('should_use_tools', None)
                used_tools = bool(response.tools_used and response.tools_used != ['quick_reply'])

                if should_use_tools is True and not used_tools:
                    turn_issues.append("Should have used tools but didn't")
                    turn_score -= 20
                elif should_use_tools is False and used_tools:
                    turn_issues.append("Used tools unnecessarily")
                    turn_score -= 10

                # Check 4: Bad patterns
                bad_patterns = [
                    "you can run", "try running", "please run", "you should",
                    "i'm cite agent", "i'm an ai", "let me explain my capabilities"
                ]
                found_bad = [p for p in bad_patterns if p in response.response.lower()]
                if found_bad:
                    turn_issues.append(f"Bad patterns: {found_bad}")
                    turn_score -= 15 * len(found_bad)

                # Check 5: Must contain certain content?
                must_contain = expected.get('must_contain', [])
                missing = [item for item in must_contain if item.lower() not in response.response.lower()]
                if missing:
                    turn_issues.append(f"Missing expected content: {missing}")
                    turn_score -= 20

                # Check 6: Context awareness (for follow-ups)
                if i > 1 and expected.get('needs_context', False):
                    # Check if response references prior turn
                    prior_content = conversation_history[-2]['response']
                    # Simple heuristic: should have some continuity
                    if len(response.response) < 20:
                        turn_issues.append("Response too short for context-dependent query")
                        turn_score -= 15

                turn_score = max(0, turn_score)
                scores.append(turn_score)

                # Display
                preview = response.response[:300]
                if len(response.response) > 300:
                    preview += "..."

                print(f"Response ({len(response.response)} chars):")
                print(f"  {preview}")
                print(f"Tools: {response.tools_used}")
                print(f"Score: {turn_score}/100")

                if turn_issues:
                    print(f"Issues:")
                    for issue in turn_issues:
                        print(f"  • {issue}")
                    issues.extend(turn_issues)
                else:
                    print("✅ Turn passed all checks")

                print()

                # Small delay between turns
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                turn_issues.append(f"Exception: {str(e)[:100]}")
                scores.append(0)
                issues.extend(turn_issues)

        # Scenario summary
        avg_score = sum(scores) / len(scores) if scores else 0

        print(f"\n{'='*80}")
        print(f"SCENARIO RESULT: {scenario_name}")
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Total Issues: {len(issues)}")

        if avg_score >= 85:
            print("✅ EXCELLENT - Natural multi-turn conversation")
        elif avg_score >= 70:
            print("⚠️ GOOD - Minor issues")
        elif avg_score >= 50:
            print("⚠️ MEDIOCRE - Needs improvement")
        else:
            print("❌ POOR - Major conversational problems")

        print(f"{'='*80}\n")

        return {
            'scenario': scenario_name,
            'avg_score': avg_score,
            'turn_scores': scores,
            'issues': issues,
            'conversation': conversation_history
        }

    async def run_all_scenarios(self):
        """Run comprehensive conversational depth tests"""
        print("="*80)
        print("DEEP CONVERSATIONAL INTELLIGENCE TEST")
        print("Testing multi-turn, follow-ups, clarifications, tone consistency")
        print("="*80)
        print()

        await self.setup()

        # SCENARIO 1: Multi-turn file exploration
        result1 = await self.run_conversation(
            "Multi-turn File Exploration",
            [
                {
                    'query': "What Python files are in this directory?",
                    'expected': {
                        'should_use_tools': True,
                        'max_length': 600,
                        'must_contain': ['.py']
                    }
                },
                {
                    'query': "Show me the first one",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 2000
                    }
                },
                {
                    'query': "What does it do?",
                    'expected': {
                        'should_use_tools': False,
                        'needs_context': True,
                        'max_length': 500
                    }
                },
                {
                    'query': "Are there any tests for it?",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 400
                    }
                }
            ]
        )
        self.results.append(result1)

        # SCENARIO 2: Clarification flow
        result2 = await self.run_conversation(
            "Clarification and Refinement",
            [
                {
                    'query': "Analyze the data",
                    'expected': {
                        'should_use_tools': False,
                        'max_length': 300,
                        'must_contain': ['which', 'what']  # Should ask clarification
                    }
                },
                {
                    'query': "The test results from the autonomy harness",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 800
                    }
                },
                {
                    'query': "What's the pass rate?",
                    'expected': {
                        'should_use_tools': False,
                        'needs_context': True,
                        'max_length': 200
                    }
                }
            ]
        )
        self.results.append(result2)

        # SCENARIO 3: Natural follow-ups with pronouns
        result3 = await self.run_conversation(
            "Pronoun Resolution",
            [
                {
                    'query': "Find setup.py",
                    'expected': {
                        'should_use_tools': True,
                        'max_length': 300
                    }
                },
                {
                    'query': "Read it",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 2000
                    }
                },
                {
                    'query': "What version is it?",
                    'expected': {
                        'should_use_tools': False,
                        'needs_context': True,
                        'max_length': 150,
                        'must_contain': ['version']
                    }
                }
            ]
        )
        self.results.append(result3)

        # SCENARIO 4: Correction and pivot
        result4 = await self.run_conversation(
            "Correction Handling",
            [
                {
                    'query': "List the test files",
                    'expected': {
                        'should_use_tools': True,
                        'max_length': 600
                    }
                },
                {
                    'query': "No, I meant the installer test files",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 600
                    }
                },
                {
                    'query': "Show me the Windows one",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 2000
                    }
                }
            ]
        )
        self.results.append(result4)

        # SCENARIO 5: Complex reasoning chain
        result5 = await self.run_conversation(
            "Complex Reasoning Chain",
            [
                {
                    'query': "What's the current version of this project?",
                    'expected': {
                        'should_use_tools': True,
                        'max_length': 300,
                        'must_contain': ['1.']
                    }
                },
                {
                    'query': "Find all references to that version in the codebase",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 1000
                    }
                },
                {
                    'query': "Are they all consistent?",
                    'expected': {
                        'should_use_tools': False,
                        'needs_context': True,
                        'max_length': 300
                    }
                }
            ]
        )
        self.results.append(result5)

        # SCENARIO 6: Tone consistency test
        result6 = await self.run_conversation(
            "Tone Consistency",
            [
                {
                    'query': "where are we?",
                    'expected': {
                        'should_use_tools': True,
                        'max_length': 150
                    }
                },
                {
                    'query': "What repository is this?",
                    'expected': {
                        'should_use_tools': False,
                        'max_length': 200
                    }
                },
                {
                    'query': "Tell me about it",
                    'expected': {
                        'should_use_tools': True,
                        'needs_context': True,
                        'max_length': 800
                    }
                },
                {
                    'query': "thanks",
                    'expected': {
                        'should_use_tools': False,
                        'max_length': 100
                    }
                }
            ]
        )
        self.results.append(result6)

        await self.agent.close()

        # Final analysis
        self.print_final_analysis()

    def print_final_analysis(self):
        """Print comprehensive analysis of all scenarios"""
        print("\n\n" + "="*80)
        print("FINAL CONVERSATIONAL DEPTH ANALYSIS")
        print("="*80 + "\n")

        overall_scores = [r['avg_score'] for r in self.results]
        overall_avg = sum(overall_scores) / len(overall_scores)

        print(f"Scenarios Tested: {len(self.results)}")
        print(f"Overall Average: {overall_avg:.1f}/100\n")

        # Scenario breakdown
        print("Scenario Breakdown:")
        print("-" * 80)
        for r in self.results:
            status = "✅" if r['avg_score'] >= 85 else "⚠️" if r['avg_score'] >= 70 else "❌"
            print(f"{status} {r['scenario']:40s} {r['avg_score']:5.1f}/100  ({len(r['issues'])} issues)")

        print("\n" + "-" * 80)

        # Grade assignment
        if overall_avg >= 90:
            grade = "A+"
            verdict = "✅✅✅ EXCELLENT - Agent has deep conversational capability"
            desc = """
The agent demonstrates:
• Natural multi-turn conversations
• Excellent context tracking
• Smart pronoun resolution
• Graceful error correction
• Consistent helpful tone
• Minimal verbosity

This is production-ready conversational AI at Claude/Cursor level.
"""
        elif overall_avg >= 80:
            grade = "A"
            verdict = "✅✅ VERY GOOD - Strong conversational skills with minor gaps"
            desc = """
The agent demonstrates:
• Good multi-turn conversations
• Solid context tracking
• Decent pronoun resolution
• Some minor issues with edge cases

Nearly production-ready, may need minor refinements.
"""
        elif overall_avg >= 70:
            grade = "B"
            verdict = "⚠️ GOOD - Functional but needs conversational refinement"
            desc = """
The agent shows:
• Basic multi-turn capability
• Some context awareness
• Occasional confusion with pronouns
• Some verbosity or awkwardness

Functional but not quite conversational AI standard.
"""
        elif overall_avg >= 60:
            grade = "C"
            verdict = "⚠️ MEDIOCRE - Significant conversational limitations"
            desc = """
The agent struggles with:
• Multi-turn coherence
• Context tracking
• Natural follow-ups
• Tone consistency

Needs substantial prompt engineering.
"""
        else:
            grade = "F"
            verdict = "❌ POOR - Conversational capability insufficient"
            desc = """
The agent has major issues with:
• Basic conversation flow
• Context memory
• Natural interaction
• Appropriate responses

Not ready for conversational use.
"""

        print(f"\nGrade: {grade}")
        print(f"\n{verdict}")
        print(desc)

        # Common issues
        all_issues = []
        for r in self.results:
            all_issues.extend(r['issues'])

        if all_issues:
            issue_counts = {}
            for issue in all_issues:
                key = issue.split(':')[0]  # Get issue type
                issue_counts[key] = issue_counts.get(key, 0) + 1

            print("\nMost Common Issues:")
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {issue_type}: {count} occurrences")

        print("\n" + "="*80)

        return overall_avg >= 85

async def main():
    tester = ConversationTester()
    await tester.run_all_scenarios()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
