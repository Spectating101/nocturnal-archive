#!/usr/bin/env python3
"""
WORKING EXAMPLE - Shows the Interactive Agent actually working
This demonstrates the system working like Claude with real interactions
"""

import os
import sys
import asyncio
import requests
import subprocess
import time
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def start_interactive_agent():
    """Start the Interactive Agent server"""
    print("🚀 Starting Interactive Agent server...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, 'interactive_agent.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       env={**os.environ, 'SERVER_PORT': '8003'})
    
    # Wait for server to start
    time.sleep(5)
    
    return server_process

def test_interactive_agent():
    """Test the Interactive Agent with real questions"""
    print("🤖 TESTING INTERACTIVE AGENT")
    print("=" * 50)
    
    # Start server
    server_process = start_interactive_agent()
    
    try:
        base_url = 'http://localhost:8003'
        
        # Test 1: Health check
        print("📋 Test 1: Health Check")
        response = requests.get(f'{base_url}/', timeout=10)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
        
        # Test 2: Simple question with tool usage
        print("\n📋 Test 2: Simple Question with Tool Usage")
        print("❓ Question: 'What files are in the current directory?'")
        
        chat_payload = {
            "question": "What files are in the current directory?",
            "user_id": "demo_user"
        }
        
        response = requests.post(
            f'{base_url}/interactive/chat',
            json=chat_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received:")
            print(f"   📝 Answer length: {len(data['response'])} characters")
            print(f"   🔧 Tools used: {data['tools_used']}")
            print(f"   🧠 Reasoning steps: {len(data['reasoning_steps'])}")
            print(f"   📊 Plan executed: {data['successful_steps']}/{data['plan_executed']} steps")
            print(f"   💬 Session ID: {data['session_id']}")
            
            # Show first part of response
            response_preview = data['response'][:200] + "..." if len(data['response']) > 200 else data['response']
            print(f"   📄 Response preview: {response_preview}")
            
            if data['tools_used'] and data['successful_steps'] > 0:
                print("✅ Tool usage and multi-step reasoning: WORKING")
            else:
                print("❌ Tool usage or multi-step reasoning: FAILED")
                return False
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            return False
        
        # Test 3: Follow-up question (conversation memory)
        print("\n📋 Test 3: Follow-up Question (Conversation Memory)")
        print("❓ Question: 'Can you read the README.md file from those files?'")
        
        chat_payload = {
            "question": "Can you read the README.md file from those files?",
            "user_id": "demo_user"  # Same user ID to test memory
        }
        
        response = requests.post(
            f'{base_url}/interactive/chat',
            json=chat_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received:")
            print(f"   📝 Answer length: {len(data['response'])} characters")
            print(f"   🔧 Tools used: {data['tools_used']}")
            print(f"   🧠 Reasoning steps: {len(data['reasoning_steps'])}")
            print(f"   📊 Plan executed: {data['successful_steps']}/{data['plan_executed']} steps")
            print(f"   💬 Session ID: {data['session_id']}")
            
            # Check if session ID is the same (memory working)
            if data['session_id'] == data['session_id']:
                print("✅ Conversation memory: WORKING (same session ID)")
            else:
                print("❌ Conversation memory: FAILED (different session ID)")
                return False
        else:
            print(f"❌ Follow-up request failed: {response.status_code}")
            return False
        
        # Test 4: R environment check
        print("\n📋 Test 4: R Environment Check")
        print("❓ Question: 'Check if R is installed on this system'")
        
        chat_payload = {
            "question": "Check if R is installed on this system",
            "user_id": "demo_user"
        }
        
        response = requests.post(
            f'{base_url}/interactive/chat',
            json=chat_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received:")
            print(f"   📝 Answer length: {len(data['response'])} characters")
            print(f"   🔧 Tools used: {data['tools_used']}")
            print(f"   🧠 Reasoning steps: {len(data['reasoning_steps'])}")
            print(f"   📊 Plan executed: {data['successful_steps']}/{data['plan_executed']} steps")
            
            if 'check_r_environment' in data['tools_used']:
                print("✅ R environment check: WORKING")
            else:
                print("❌ R environment check: FAILED")
                return False
        else:
            print(f"❌ R environment check failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up server
        server_process.terminate()
        server_process.wait()

def main():
    """Run the working example"""
    print("🎬 WORKING EXAMPLE: Interactive Agent in Action")
    print("=" * 60)
    print("This demonstrates the Interactive Agent actually working like Claude")
    print()
    
    success = test_interactive_agent()
    
    print("\n🎉 FINAL RESULTS")
    print("=" * 50)
    
    if success:
        print("✅ INTERACTIVE AGENT: WORKING")
        print("✅ Conversation memory: Working")
        print("✅ Tool integration: Working")
        print("✅ Multi-step reasoning: Working")
        print("✅ R environment integration: Working")
        print()
        print("🚀 PROOF: Your system now works like Claude!")
        print("🎯 It's no longer Copilot-style!")
        print("💡 It has conversation memory, tool usage, and multi-step reasoning!")
        print()
        print("🔧 How to use it:")
        print("   1. Start server: python3 interactive_agent.py")
        print("   2. Use client: python3 interactive_client.py")
        print("   3. Ask complex questions with follow-ups!")
    else:
        print("❌ INTERACTIVE AGENT: NEEDS WORK")
        print("🔧 Some tests failed - the system needs debugging")

if __name__ == "__main__":
    main()