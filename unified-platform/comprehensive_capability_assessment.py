#!/usr/bin/env python3
"""
Comprehensive Capability Assessment
Compare Nocturnal-Archive capabilities against Claude's actual capabilities
"""

import asyncio
import sys
import os
import json
from typing import Dict, List, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_interactive_agent import EnhancedInteractiveAgent, ChatRequest

class CapabilityAssessment:
    """Comprehensive assessment of system capabilities"""
    
    def __init__(self):
        self.agent = None
        self.results = {
            "core_capabilities": {},
            "tool_execution": {},
            "reasoning_quality": {},
            "api_integrations": {},
            "overall_score": 0
        }
    
    async def initialize(self):
        """Initialize the agent for testing"""
        try:
            self.agent = EnhancedInteractiveAgent()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False
    
    async def test_core_capabilities(self):
        """Test core AI capabilities"""
        print("\n🧠 TESTING CORE CAPABILITIES")
        print("=" * 50)
        
        tests = [
            {
                "name": "Simple Question Answering",
                "request": "What is the capital of France?",
                "expected": "Should provide factual answer"
            },
            {
                "name": "Code Explanation", 
                "request": "Explain this Python code: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "expected": "Should explain recursion and fibonacci sequence"
            },
            {
                "name": "Problem Solving",
                "request": "How would you debug a Python script that's running slowly?",
                "expected": "Should provide systematic debugging approach"
            }
        ]
        
        for test in tests:
            print(f"\n🔍 {test['name']}")
            try:
                request = ChatRequest(
                    question=test["request"],
                    use_planning=False,
                    context={}
                )
                
                response = await self.agent.process_request(request)
                
                # Assess response quality
                quality_score = self._assess_response_quality(response.response, test["expected"])
                
                self.results["core_capabilities"][test["name"]] = {
                    "success": True,
                    "response_length": len(response.response),
                    "quality_score": quality_score,
                    "tools_used": response.tools_used
                }
                
                print(f"✅ Response length: {len(response.response)} chars")
                print(f"✅ Quality score: {quality_score}/10")
                print(f"✅ Tools used: {response.tools_used}")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                self.results["core_capabilities"][test["name"]] = {
                    "success": False,
                    "error": str(e)
                }
    
    async def test_tool_execution(self):
        """Test tool execution capabilities"""
        print("\n🔧 TESTING TOOL EXECUTION")
        print("=" * 50)
        
        tests = [
            {
                "name": "File Reading",
                "request": "read the requirements.txt file",
                "expected_tool": "read_file"
            },
            {
                "name": "Terminal Command",
                "request": "run ls -la to list directory contents",
                "expected_tool": "execute_terminal_command"
            },
            {
                "name": "File Writing",
                "request": "create a test file called test.txt with content 'Hello World'",
                "expected_tool": "write_file"
            },
            {
                "name": "Python Code Execution",
                "request": "execute this Python code: print('Hello from Python')",
                "expected_tool": "execute_python_code"
            }
        ]
        
        for test in tests:
            print(f"\n🔍 {test['name']}")
            try:
                request = ChatRequest(
                    question=test["request"],
                    use_planning=True,
                    context={}
                )
                
                response = await self.agent.process_request(request)
                
                # Check if expected tool was used
                tool_used = test["expected_tool"] in response.tools_used
                
                self.results["tool_execution"][test["name"]] = {
                    "success": tool_used,
                    "expected_tool": test["expected_tool"],
                    "tools_used": response.tools_used,
                    "response_length": len(response.response)
                }
                
                if tool_used:
                    print(f"✅ Tool executed: {test['expected_tool']}")
                else:
                    print(f"❌ Tool NOT executed. Expected: {test['expected_tool']}, Got: {response.tools_used}")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                self.results["tool_execution"][test["name"]] = {
                    "success": False,
                    "error": str(e)
                }
    
    async def test_reasoning_quality(self):
        """Test reasoning and planning quality"""
        print("\n🧩 TESTING REASONING QUALITY")
        print("=" * 50)
        
        tests = [
            {
                "name": "Multi-step Planning",
                "request": "create a Python script that reads a CSV file, processes the data, and creates a plot",
                "expected": "Should break down into multiple steps"
            },
            {
                "name": "Complex Problem Solving",
                "request": "I have a web scraping script that's getting blocked. How can I make it more robust?",
                "expected": "Should provide systematic solution approach"
            },
            {
                "name": "Code Review",
                "request": "Review this code for potential issues: import os; os.system('rm -rf /')",
                "expected": "Should identify security issues"
            }
        ]
        
        for test in tests:
            print(f"\n🔍 {test['name']}")
            try:
                request = ChatRequest(
                    question=test["request"],
                    use_planning=True,
                    context={}
                )
                
                response = await self.agent.process_request(request)
                
                # Assess reasoning quality
                reasoning_score = self._assess_reasoning_quality(response.response, test["expected"])
                
                self.results["reasoning_quality"][test["name"]] = {
                    "success": True,
                    "reasoning_score": reasoning_score,
                    "response_length": len(response.response),
                    "tools_used": response.tools_used
                }
                
                print(f"✅ Reasoning score: {reasoning_score}/10")
                print(f"✅ Response length: {len(response.response)} chars")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                self.results["reasoning_quality"][test["name"]] = {
                    "success": False,
                    "error": str(e)
                }
    
    async def test_api_integrations(self):
        """Test API integrations"""
        print("\n🔌 TESTING API INTEGRATIONS")
        print("=" * 50)
        
        # Check what APIs are available
        finsight_available = hasattr(self.agent, 'finsight_components') and self.agent.finsight_components
        archive_available = hasattr(self.agent, 'archive_components') and self.agent.archive_components
        
        print(f"Finsight API available: {finsight_available}")
        print(f"Archive API available: {archive_available}")
        
        self.results["api_integrations"] = {
            "finsight_available": finsight_available,
            "archive_available": archive_available,
            "overall_status": "partial" if (finsight_available or archive_available) else "none"
        }
    
    def _assess_response_quality(self, response: str, expected: str) -> int:
        """Assess response quality on a scale of 1-10"""
        if not response or len(response) < 50:
            return 2
        
        # Basic quality checks
        score = 5  # Base score
        
        # Length check
        if len(response) > 200:
            score += 1
        
        # Structure check
        if "**" in response or "##" in response:  # Markdown formatting
            score += 1
        
        # Completeness check
        if len(response.split()) > 50:  # Substantial content
            score += 1
        
        # Relevance check (basic keyword matching)
        if any(word in response.lower() for word in expected.lower().split()):
            score += 1
        
        return min(score, 10)
    
    def _assess_reasoning_quality(self, response: str, expected: str) -> int:
        """Assess reasoning quality on a scale of 1-10"""
        if not response:
            return 1
        
        score = 3  # Base score
        
        # Multi-step indication
        if "step" in response.lower() or "first" in response.lower() or "then" in response.lower():
            score += 2
        
        # Structured approach
        if "**" in response or "##" in response:
            score += 1
        
        # Substantial content
        if len(response) > 300:
            score += 2
        
        # Problem-solving indicators
        if any(word in response.lower() for word in ["analyze", "consider", "approach", "solution"]):
            score += 2
        
        return min(score, 10)
    
    def calculate_overall_score(self):
        """Calculate overall capability score"""
        scores = []
        
        # Core capabilities score
        core_scores = [test.get("quality_score", 0) for test in self.results["core_capabilities"].values() if test.get("success")]
        if core_scores:
            scores.append(sum(core_scores) / len(core_scores))
        
        # Tool execution score
        tool_success_rate = sum(1 for test in self.results["tool_execution"].values() if test.get("success")) / len(self.results["tool_execution"])
        scores.append(tool_success_rate * 10)
        
        # Reasoning quality score
        reasoning_scores = [test.get("reasoning_score", 0) for test in self.results["reasoning_quality"].values() if test.get("success")]
        if reasoning_scores:
            scores.append(sum(reasoning_scores) / len(reasoning_scores))
        
        # API integration score
        api_score = 5 if self.results["api_integrations"]["overall_status"] == "partial" else 0
        scores.append(api_score)
        
        self.results["overall_score"] = sum(scores) / len(scores) if scores else 0
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE CAPABILITY ASSESSMENT SUMMARY")
        print("="*80)
        
        print(f"\n📊 OVERALL SCORE: {self.results['overall_score']:.1f}/10")
        
        print(f"\n🧠 CORE CAPABILITIES:")
        for name, result in self.results["core_capabilities"].items():
            status = "✅" if result.get("success") else "❌"
            score = result.get("quality_score", 0)
            print(f"  {status} {name}: {score}/10")
        
        print(f"\n🔧 TOOL EXECUTION:")
        for name, result in self.results["tool_execution"].items():
            status = "✅" if result.get("success") else "❌"
            tools = result.get("tools_used", [])
            print(f"  {status} {name}: {tools}")
        
        print(f"\n🧩 REASONING QUALITY:")
        for name, result in self.results["reasoning_quality"].items():
            status = "✅" if result.get("success") else "❌"
            score = result.get("reasoning_score", 0)
            print(f"  {status} {name}: {score}/10")
        
        print(f"\n🔌 API INTEGRATIONS:")
        print(f"  Finsight: {'✅' if self.results['api_integrations']['finsight_available'] else '❌'}")
        print(f"  Archive: {'✅' if self.results['api_integrations']['archive_available'] else '❌'}")
        
        # Final assessment
        if self.results["overall_score"] >= 8:
            print(f"\n🎉 ASSESSMENT: EXCELLENT - Ready for production!")
        elif self.results["overall_score"] >= 6:
            print(f"\n✅ ASSESSMENT: GOOD - Minor improvements needed")
        elif self.results["overall_score"] >= 4:
            print(f"\n⚠️ ASSESSMENT: FAIR - Significant improvements needed")
        else:
            print(f"\n❌ ASSESSMENT: POOR - Major overhaul required")

async def main():
    """Run comprehensive assessment"""
    assessment = CapabilityAssessment()
    
    print("🚀 Starting Comprehensive Capability Assessment")
    print("Comparing Nocturnal-Archive against Claude's capabilities")
    
    if not await assessment.initialize():
        print("❌ Cannot proceed without agent initialization")
        return
    
    await assessment.test_core_capabilities()
    await assessment.test_tool_execution()
    await assessment.test_reasoning_quality()
    await assessment.test_api_integrations()
    
    assessment.calculate_overall_score()
    assessment.print_summary()
    
    # Save results
    with open("capability_assessment_results.json", "w") as f:
        json.dump(assessment.results, f, indent=2)
    
    print(f"\n💾 Results saved to: capability_assessment_results.json")

if __name__ == "__main__":
    asyncio.run(main())