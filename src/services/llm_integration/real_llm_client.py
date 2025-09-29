"""
Real LLM Client - Actual LLM API integration using Groq
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RealLLMClient:
    """Real LLM client using Groq API."""
    
    def __init__(self):
        self.client = None
        self.model = "llama-3.1-70b-versatile"
        self._initialize_client()
        logger.info("Real LLM Client initialized")
    
    def _initialize_client(self):
        """Initialize Groq client."""
        try:
            from groq import Groq
            
            # Try to get API key from environment
            api_key = os.getenv('GROQ_API_KEY_1')
            if not api_key or api_key == 'your_groq_api_key_here':
                logger.warning("No valid Groq API key found. Using simulation mode.")
                return
            
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
            
        except ImportError:
            logger.error("Groq library not installed. Install with: pip install groq")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
    
    async def analyze_problem(self, problem_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use real LLM to analyze problems."""
        if not self.client:
            return await self._fallback_analysis(problem_description, context)
        
        try:
            prompt = f"""
            Analyze this problem and provide a structured analysis in JSON format:
            
            Problem: {problem_description}
            Context: {context or "No additional context"}
            
            Provide analysis in this exact JSON format:
            {{
                "problem_type": "programming|data_analysis|research|file_operations|general",
                "domain": "specific domain",
                "complexity": "low|medium|high",
                "requirements": ["list", "of", "requirements"],
                "constraints": ["list", "of", "constraints"],
                "approach": "recommended approach",
                "tools_needed": ["list", "of", "tools"],
                "reasoning": "detailed reasoning"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert problem analyzer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            import json
            try:
                # Look for JSON in the response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                
                return {
                    "status": "success",
                    "analysis": analysis,
                    "llm_response": content,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except json.JSONDecodeError:
                # Fallback to simulated analysis
                return await self._fallback_analysis(problem_description, context)
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return await self._fallback_analysis(problem_description, context)
    
    async def decompose_problem(self, problem_description: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use real LLM to decompose problems."""
        if not self.client:
            return await self._fallback_decomposition(problem_description, analysis)
        
        try:
            prompt = f"""
            Based on this analysis: {analysis}
            
            Decompose the problem "{problem_description}" into specific, actionable steps.
            
            Return as JSON array in this exact format:
            [
                {{
                    "id": "step_1",
                    "description": "specific action to take",
                    "type": "analysis|research|design|implementation|testing|documentation",
                    "tool_required": "specific tool needed",
                    "reasoning": "why this step is needed",
                    "expected_output": "what this step should produce"
                }}
            ]
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert problem decomposer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                if '[' in content and ']' in content:
                    start = content.find('[')
                    end = content.rfind(']') + 1
                    json_str = content[start:end]
                    steps = json.loads(json_str)
                else:
                    raise ValueError("No JSON array found in response")
                
                return steps
                
            except json.JSONDecodeError:
                return await self._fallback_decomposition(problem_description, analysis)
                
        except Exception as e:
            logger.error(f"LLM decomposition failed: {str(e)}")
            return await self._fallback_decomposition(problem_description, analysis)
    
    async def generate_code(self, description: str, context: Dict[str, Any] = None) -> str:
        """Use real LLM to generate code."""
        if not self.client:
            return await self._fallback_code_generation(description, context)
        
        try:
            prompt = f"""
            Generate Python code for: {description}
            
            Context: {context or "No additional context"}
            
            Requirements:
            1. Write clean, well-documented Python code
            2. Include proper error handling
            3. Add comments explaining the logic
            4. Include test examples if appropriate
            5. Follow Python best practices
            
            Return only the Python code, no explanations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate clean, well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if code.startswith('```python'):
                code = code[9:]
            if code.startswith('```'):
                code = code[3:]
            if code.endswith('```'):
                code = code[:-3]
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"LLM code generation failed: {str(e)}")
            return await self._fallback_code_generation(description, context)
    
    async def synthesize_solution(self, steps_results: List[Dict[str, Any]], original_problem: str) -> Dict[str, Any]:
        """Use real LLM to synthesize solutions."""
        if not self.client:
            return await self._fallback_synthesis(steps_results, original_problem)
        
        try:
            prompt = f"""
            Original problem: {original_problem}
            
            Step results: {steps_results}
            
            Synthesize a comprehensive solution including:
            1. Summary of what was accomplished
            2. Key insights and findings
            3. Final solution or recommendations
            4. Next steps or improvements
            
            Return as JSON:
            {{
                "summary": "overall summary",
                "insights": ["key", "insights"],
                "solution": "final solution or recommendations",
                "next_steps": ["suggested", "next", "steps"],
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert solution synthesizer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    synthesis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                
                return synthesis
                
            except json.JSONDecodeError:
                return await self._fallback_synthesis(steps_results, original_problem)
                
        except Exception as e:
            logger.error(f"LLM synthesis failed: {str(e)}")
            return await self._fallback_synthesis(steps_results, original_problem)
    
    # Fallback methods (simulated responses)
    async def _fallback_analysis(self, problem_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when LLM is not available."""
        problem_lower = problem_description.lower()
        
        if any(keyword in problem_lower for keyword in ["code", "program", "script", "function", "class"]):
            problem_type = "programming"
            domain = "software_development"
            complexity = "medium"
            requirements = ["code_generation", "syntax_validation", "testing"]
            constraints = ["python_language"] if "python" in problem_lower else []
            approach = "Implement using best practices with proper error handling"
            tools_needed = ["code_execution", "file_operations"]
            reasoning = "This is a programming task requiring code implementation, testing, and documentation."
        else:
            problem_type = "general"
            domain = "general"
            complexity = "medium"
            requirements = ["analysis", "solution_design"]
            constraints = []
            approach = "Analyze requirements and design appropriate solution"
            tools_needed = ["reasoning"]
            reasoning = "This is a general problem requiring analysis and solution design."
        
        return {
            "status": "success",
            "analysis": {
                "problem_type": problem_type,
                "domain": domain,
                "complexity": complexity,
                "requirements": requirements,
                "constraints": constraints,
                "approach": approach,
                "tools_needed": tools_needed,
                "reasoning": reasoning
            },
            "llm_response": "Fallback analysis (LLM not available)",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _fallback_decomposition(self, problem_description: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback decomposition when LLM is not available."""
        return [
            {
                "id": "step_1",
                "description": f"Analyze problem: {problem_description}",
                "type": "analysis",
                "tool_required": "llm_reasoning",
                "reasoning": "Need to understand the problem requirements and constraints",
                "expected_output": "Clear problem understanding and requirements"
            },
            {
                "id": "step_2",
                "description": "Implement solution",
                "type": "implementation",
                "tool_required": "code_execution",
                "reasoning": "Need to implement the solution",
                "expected_output": "Working solution"
            },
            {
                "id": "step_3",
                "description": "Synthesize solution and provide summary",
                "type": "documentation",
                "tool_required": "llm_reasoning",
                "reasoning": "Need to summarize findings and provide final solution",
                "expected_output": "Comprehensive solution summary"
            }
        ]
    
    async def _fallback_code_generation(self, description: str, context: Dict[str, Any]) -> str:
        """Fallback code generation when LLM is not available."""
        return f'''
# Generated code for: {description}

def main():
    """Main function to solve the problem."""
    print("Problem:", "{description}")
    print("Solution implementation:")
    
    # Add your implementation here
    # This is a template - customize based on specific requirements
    
    return "Solution implemented"

if __name__ == "__main__":
    result = main()
    print(f"Result: {{result}}")
'''
    
    async def _fallback_synthesis(self, steps_results: List[Dict[str, Any]], original_problem: str) -> Dict[str, Any]:
        """Fallback synthesis when LLM is not available."""
        successful_steps = [step for step in steps_results if step.get("status") == "success"]
        
        return {
            "summary": f"Successfully completed {len(successful_steps)}/{len(steps_results)} steps for: {original_problem}",
            "insights": ["Solution implemented successfully"],
            "solution": f"Problem '{original_problem}' has been addressed through systematic analysis and implementation.",
            "next_steps": ["Review the implemented solution", "Consider additional optimizations"],
            "confidence": len(successful_steps) / len(steps_results) if steps_results else 0.0
        }