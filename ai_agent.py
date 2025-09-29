#!/usr/bin/env python3
"""
Nocturnal Archive AI Agent - Consolidated and Production-Ready
Combines the best features from all implementations into one solid agent.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Suppress noise
logging.basicConfig(level=logging.ERROR)

try:
    from groq import Groq
except ImportError:
    print("❌ Install groq: pip install groq")
    exit(1)

@dataclass
class ChatRequest:
    question: str
    user_id: str = "default"
    conversation_id: str = "default"
    context: Dict[str, Any] = None

@dataclass
class ChatResponse:
    response: str
    tools_used: List[str] = None
    reasoning_steps: List[str] = None
    model: str = "nocturnal-ai-agent"
    timestamp: str = None
    tokens_used: int = 0
    confidence_score: float = 0.0
    execution_results: Dict[str, Any] = None

class NocturnalAIAgent:
    """
    Consolidated AI Agent with the best features from all implementations:
    - Persistent shell access (from groq_fixed.py)
    - Smart routing and memory (from hybrid_intelligent_agent.py)
    - Code execution capabilities (from enhanced_proper_agent.py)
    - Production-ready error handling
    """
    
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.shell_session = None
        self.memory = {}  # Simple memory system
        self.daily_token_usage = 0
        self.daily_limit = 100000
        
    async def initialize(self):
        """Initialize the agent with API keys and shell session"""
        # Try multiple API keys for better rate limits
        api_keys = [
            os.getenv('GROQ_API_KEY'),
            os.getenv('GROQ_API_KEY_2'),
            os.getenv('GROQ_API_KEY_3')
        ]
        
        for i, api_key in enumerate(api_keys):
            if api_key:
                try:
                    self.client = Groq(api_key=api_key)
                    print(f"✅ Nocturnal AI Agent Ready! (Using API key {i+1})")
                    
                    # Initialize persistent shell session
                    self.shell_session = subprocess.Popen(['bash'], 
                                                        stdin=subprocess.PIPE, 
                                                        stdout=subprocess.PIPE, 
                                                        stderr=subprocess.STDOUT,
                                                        text=True,
                                                        cwd=os.getcwd())
                    return True
                except Exception as e:
                    print(f"❌ API key {i+1} failed: {e}")
                    continue
        
        print("❌ No valid API keys found!")
        return False
    
    def execute_command(self, command: str) -> str:
        """Execute command in persistent shell session and return output"""
        try:
            if self.shell_session is None:
                return "ERROR: Shell session not initialized"
            
            # Send command to persistent shell
            self.shell_session.stdin.write(command + '\n')
            self.shell_session.stdin.flush()
            
            # Read output with timeout
            import select
            
            output_lines = []
            start_time = time.time()
            timeout = 10  # seconds
            
            while time.time() - start_time < timeout:
                if select.select([self.shell_session.stdout], [], [], 0.1)[0]:
                    line = self.shell_session.stdout.readline()
                    if line:
                        output_lines.append(line.rstrip())
                    else:
                        break
                else:
                    # No more output available
                    break
            
            output = '\n'.join(output_lines)
            return output if output else "Command executed successfully"
            
        except Exception as e:
            return f"ERROR: {e}"
    
    def _check_token_budget(self, estimated_tokens: int) -> bool:
        """Check if we have enough token budget"""
        return (self.daily_token_usage + estimated_tokens) < self.daily_limit
    
    def _charge_tokens(self, tokens: int):
        """Charge tokens to daily usage"""
        self.daily_token_usage += tokens
    
    def _get_memory_context(self, user_id: str, conversation_id: str) -> str:
        """Get relevant memory context for the conversation"""
        if user_id not in self.memory:
            self.memory[user_id] = {}
        
        if conversation_id not in self.memory[user_id]:
            self.memory[user_id][conversation_id] = []
        
        # Get last 3 interactions for context
        recent_memory = self.memory[user_id][conversation_id][-3:]
        if not recent_memory:
            return ""
        
        context = "Recent conversation context:\n"
        for mem in recent_memory:
            context += f"- {mem}\n"
        return context
    
    def _update_memory(self, user_id: str, conversation_id: str, interaction: str):
        """Update memory with new interaction"""
        if user_id not in self.memory:
            self.memory[user_id] = {}
        
        if conversation_id not in self.memory[user_id]:
            self.memory[user_id][conversation_id] = []
        
        self.memory[user_id][conversation_id].append(interaction)
        
        # Keep only last 10 interactions
        if len(self.memory[user_id][conversation_id]) > 10:
            self.memory[user_id][conversation_id] = self.memory[user_id][conversation_id][-10:]
    
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """Process request with full AI capabilities"""
        try:
            if not self.client:
                return ChatResponse(
                    response="❌ AI response not available (no Groq API key)",
                    timestamp=datetime.now().isoformat()
                )
            
            # Get memory context
            memory_context = self._get_memory_context(request.user_id, request.conversation_id)
            
            # Build messages with enhanced system prompt
            messages = [
                {
                    "role": "system", 
                    "content": f"""You are the Nocturnal AI Agent, a sophisticated AI assistant with persistent shell access and memory.

CAPABILITIES:
- Execute terminal commands with persistent state (cd commands stick between interactions)
- Access and analyze files in the current directory
- Remember conversation context and user preferences
- Provide intelligent analysis and recommendations

IMPORTANT RULES:
- Be direct and concise - NO <think> tags or internal reasoning
- Only suggest terminal commands in backticks when users ask about files/directories/system info
- You have a PERSISTENT shell session - directory changes persist between interactions
- When commands are executed, you receive real results - use them for accurate analysis
- Use memory context to provide personalized responses

{memory_context}

INTERACTION STYLE:
- Normal conversation first, tools only when needed
- Give helpful, direct responses without verbose explanations
- Focus on being useful, not showing your reasoning process
- Remember user preferences and build on previous conversations

You have real system access through command execution. Be smart and efficient."""
                }
            ]
            
            # Add conversation history (limit to last 6 messages to avoid token limits)
            recent_history = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
            messages.extend(recent_history)
            
            # Add current user message
            messages.append({"role": "user", "content": request.question})
            
            # Check token budget
            estimated_tokens = len(str(messages)) // 4  # Rough estimate
            if not self._check_token_budget(estimated_tokens):
                return ChatResponse(
                    response="⚠️ Daily token limit reached. Please try again tomorrow or upgrade your plan.",
                    timestamp=datetime.now().isoformat()
                )
            
            # Get Groq's response
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else estimated_tokens
            self._charge_tokens(tokens_used)
            
            # Check for commands in backticks
            commands = re.findall(r'`([^`]+)`', response_text)
            execution_results = {}
            
            if commands:
                command = commands[0].strip()
                print(f"\n🔧 Executing: {command}")
                
                # Execute the command
                output = self.execute_command(command)
                print(f"✅ Command completed")
                
                execution_results = {
                    "command": command,
                    "output": output,
                    "success": not output.startswith("ERROR:")
                }
                
                # Create analysis prompt with REAL results (truncated to avoid token limits)
                truncated_output = output[:1000] if len(output) > 1000 else output
                analysis_prompt = f"""User asked: "{request.question}"
Command: `{command}`
Results: {truncated_output}

Brief summary:"""
                
                # Get Groq's analysis of the real results
                analysis_response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    max_tokens=300,
                    temperature=0.3
                )
                
                analysis = analysis_response.choices[0].message.content
                final_response = f"{response_text}\n\n{analysis}"
                
                # Charge additional tokens
                additional_tokens = analysis_response.usage.total_tokens if analysis_response.usage else 100
                self._charge_tokens(additional_tokens)
                tokens_used += additional_tokens
            else:
                final_response = response_text
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": request.question})
            self.conversation_history.append({"role": "assistant", "content": final_response})
            
            # Update memory
            self._update_memory(
                request.user_id, 
                request.conversation_id, 
                f"Q: {request.question[:100]}... A: {final_response[:100]}..."
            )
            
            return ChatResponse(
                response=final_response,
                tools_used=["shell_execution"] if commands else [],
                reasoning_steps=["command_execution"] if commands else [],
                timestamp=datetime.now().isoformat(),
                tokens_used=tokens_used,
                confidence_score=0.9 if not commands else 0.8,
                execution_results=execution_results
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"❌ Error: {str(e)}",
                timestamp=datetime.now().isoformat(),
                confidence_score=0.0
            )
    
    async def run_interactive(self):
        """Run interactive chat session"""
        if not await self.initialize():
            return
            
        print("\n" + "="*60)
        print("🤖 NOCTURNAL AI AGENT")
        print("="*60)
        print("Consolidated AI Agent with persistent shell access and memory")
        print("Type 'quit' to exit")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    # Clean up shell session
                    if self.shell_session:
                        self.shell_session.terminate()
                    break
                
                # Process request
                request = ChatRequest(question=user_input)
                response = await self.process_request(request)
                
                print(f"\n🤖 Agent: {response.response}")
                
                if response.execution_results:
                    print(f"🔧 Command: {response.execution_results['command']}")
                    print(f"📊 Success: {response.execution_results['success']}")
                
                print(f"📈 Tokens used: {response.tokens_used}")
                print(f"🎯 Confidence: {response.confidence_score:.2f}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                # Clean up shell session
                if self.shell_session:
                    self.shell_session.terminate()
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

async def main():
    """Main entry point"""
    agent = NocturnalAIAgent()
    await agent.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())
