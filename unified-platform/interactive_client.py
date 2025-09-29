#!/usr/bin/env python3
"""
Interactive Client - Works with the Interactive Agent
Provides the same experience as talking to me (Claude)
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime

class InteractiveClient:
    """Client that provides interactive experience like Claude"""
    
    def __init__(self, server_url: str = None, user_id: str = None):
        self.server_url = server_url or os.getenv('INTERACTIVE_SERVER_URL', 'http://localhost:8001')
        self.user_id = user_id or os.getenv('USER_ID', f'user_{os.getenv("USER", "default")}')
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for complex operations
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to the interactive agent"""
        try:
            response = self.session.get(f"{self.server_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connected to Interactive Agent: {data.get('service', 'Unknown')}")
                print(f"🌐 Server: {self.server_url}")
                print(f"👤 User ID: {self.user_id}")
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Interactive Agent at {self.server_url}")
            print(f"🔧 Make sure the interactive agent is running")
            print(f"💡 You can set INTERACTIVE_SERVER_URL environment variable")
            raise ConnectionError(f"Failed to connect to interactive agent: {e}")
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question and get interactive response"""
        try:
            payload = {
                "question": question,
                "user_id": self.user_id
            }
            
            print("🤔 Thinking...")
            response = self.session.post(
                f"{self.server_url}/interactive/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                return {
                    "response": f"❌ Error {response.status_code}: {error_data.get('detail', 'Unknown error')}",
                    "tools_used": [],
                    "reasoning_steps": [],
                    "plan_executed": 0,
                    "successful_steps": 0,
                    "session_id": "error",
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                "response": "⏰ Request timed out. The agent might be processing a complex task.",
                "tools_used": [],
                "reasoning_steps": [],
                "plan_executed": 0,
                "successful_steps": 0,
                "session_id": "timeout",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                "response": f"❌ Network error: {e}",
                "tools_used": [],
                "reasoning_steps": [],
                "plan_executed": 0,
                "successful_steps": 0,
                "session_id": "network_error",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "response": f"❌ Unexpected error: {e}",
                "tools_used": [],
                "reasoning_steps": [],
                "plan_executed": 0,
                "successful_steps": 0,
                "session_id": "unexpected_error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get interactive agent status"""
        try:
            response = self.session.get(f"{self.server_url}/interactive/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to get status: {e}"}
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """Format the response for display"""
        response = result["response"]
        
        # Add metadata if available
        if result.get("tools_used"):
            response += f"\n\n🔧 Tools used: {', '.join(result['tools_used'])}"
        
        if result.get("reasoning_steps"):
            response += f"\n\n🧠 Reasoning steps: {len(result['reasoning_steps'])}"
            for i, step in enumerate(result["reasoning_steps"], 1):
                response += f"\n  {i}. {step}"
        
        if result.get("plan_executed", 0) > 0:
            response += f"\n\n📋 Plan executed: {result['successful_steps']}/{result['plan_executed']} steps successful"
        
        return response

def main():
    """Main interactive loop - works like talking to me"""
    print("🤖 Interactive AI Agent - Like Claude")
    print("=" * 50)
    print("💡 Ask me anything! I can:")
    print("  📁 Read and write files")
    print("  🔍 Search directories")
    print("  💻 Run commands (safely)")
    print("  📊 Check R environment")
    print("  🧠 Multi-step reasoning")
    print("  💬 Remember our conversation")
    print()
    print("📝 Type 'quit' to exit, 'status' for agent status, 'help' for examples")
    print()
    
    # Initialize client
    try:
        client = InteractiveClient()
    except ConnectionError as e:
        print(f"❌ {e}")
        return
    
    # Show status
    status = client.get_status()
    if "error" not in status:
        print(f"✅ Agent Status: {status.get('status', 'unknown')}")
        print(f"🔑 API Keys: {status.get('api_keys_loaded', 0)}")
    print()
    
    # Interactive loop
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'status':
                status = client.get_status()
                if "error" in status:
                    print(f"❌ {status['error']}")
                else:
                    print(f"✅ Agent Status: {status.get('status', 'unknown')}")
                    print(f"🔑 API Keys: {status.get('api_keys_loaded', 0)}")
                    print(f"🤖 Agent Initialized: {status.get('agent_initialized', False)}")
                print()
                continue
            
            if question.lower() == 'help':
                print("\n💡 Example questions:")
                print("  'What files are in the current directory?'")
                print("  'Read the file README.md and summarize it'")
                print("  'Check if R is installed and what packages are available'")
                print("  'Create a simple R script that calculates the mean of 1:10'")
                print("  'Search for all Python files in this directory'")
                print("  'What's the difference between R and Python for data analysis?'")
                print("  'Help me debug this R error: [paste your error]'")
                print()
                continue
            
            if not question:
                continue
            
            # Process the question
            result = client.ask_question(question)
            
            # Format and display response
            formatted_response = client.format_response(result)
            print(f"\n🤖 Assistant:\n{formatted_response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()