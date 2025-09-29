#!/usr/bin/env python3
"""
R/SQL Assistant Client - Updated to use server with API key rotation
No longer needs individual API keys - connects to server instead
"""

import os
import sys
import json
import time
import requests
from typing import Optional

class AssistantClient:
    """Client for R/SQL Assistant Server"""
    
    def __init__(self, server_url: str = None, user_id: str = None):
        self.server_url = server_url or os.getenv('ASSISTANT_SERVER_URL', 'http://localhost:8000')
        self.user_id = user_id or os.getenv('USER_ID', 'anonymous')
        self.session = requests.Session()
        self.session.timeout = 30  # 30 second timeout
        
        # Test server connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to the server"""
        try:
            response = self.session.get(f"{self.server_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connected to server: {data.get('service', 'Unknown')}")
                print(f"📊 API keys loaded: {data.get('api_keys_loaded', 0)}")
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server at {self.server_url}")
            print(f"🔧 Make sure the server is running and accessible")
            print(f"💡 You can set ASSISTANT_SERVER_URL environment variable")
            raise ConnectionError(f"Failed to connect to server: {e}")
    
    def ask_question(self, question: str, model: str = "llama-3.1-70b-versatile", 
                    temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Send a question to the server and get response"""
        try:
            payload = {
                "question": question,
                "user_id": self.user_id,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = self.session.post(
                f"{self.server_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["response"]
            elif response.status_code == 429:
                error_data = response.json()
                return f"⏳ Rate limit exceeded: {error_data.get('detail', 'Please try again later')}"
            elif response.status_code == 503:
                error_data = response.json()
                return f"🚫 Service unavailable: {error_data.get('detail', 'All API keys are busy')}"
            else:
                error_data = response.json()
                return f"❌ Error {response.status_code}: {error_data.get('detail', 'Unknown error')}"
                
        except requests.exceptions.Timeout:
            return "⏰ Request timed out. The server might be busy."
        except requests.exceptions.RequestException as e:
            return f"❌ Network error: {e}"
        except Exception as e:
            return f"❌ Unexpected error: {e}"
    
    def get_server_status(self) -> dict:
        """Get server status and statistics"""
        try:
            response = self.session.get(f"{self.server_url}/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to get status: {e}"}
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics"""
        try:
            response = self.session.get(f"{self.server_url}/stats")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Stats request failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}

def main():
    """Main interactive loop"""
    print("🤖 R/SQL Assistant Client")
    print("=" * 40)
    print("💡 Ask me anything about R or SQL commands!")
    print("📝 Type 'quit' or 'exit' to stop")
    print("📊 Type 'status' to see server status")
    print("📈 Type 'stats' to see usage statistics")
    print()
    
    # Initialize client
    try:
        client = AssistantClient()
    except ConnectionError as e:
        print(f"❌ {e}")
        return
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'status':
                print("📊 Getting server status...")
                status = client.get_server_status()
                if "error" in status:
                    print(f"❌ {status['error']}")
                else:
                    print(f"✅ Server: {status.get('server_status', 'unknown')}")
                    print(f"🔑 API Keys: {len(status.get('api_keys', []))}")
                    for key in status.get('api_keys', []):
                        health = "✅" if key.get('is_healthy') else "❌"
                        print(f"  {health} {key.get('key_id')}: {key.get('requests_today', 0)}/{key.get('daily_limit', 0)} requests today")
                print()
                continue
            
            if question.lower() == 'stats':
                print("📈 Getting usage statistics...")
                stats = client.get_usage_stats()
                if "error" in stats:
                    print(f"❌ {stats['error']}")
                else:
                    print(f"📊 Total requests: {sum(stats.get('request_stats', {}).values())}")
                    print(f"👥 Active users: {len(stats.get('user_stats', {}))}")
                print()
                continue
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            response = client.ask_question(question)
            print(f"\n🤖 Assistant:\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
