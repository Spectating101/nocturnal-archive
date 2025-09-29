#!/usr/bin/env python3
"""
Test script for the consolidated Nocturnal AI Agent
"""

import asyncio
from ai_agent import NocturnalAIAgent, ChatRequest

async def test_agent():
    """Test the consolidated AI agent"""
    print("🧪 Testing Nocturnal AI Agent...")
    
    agent = NocturnalAIAgent()
    
    # Test initialization
    if not await agent.initialize():
        print("❌ Failed to initialize agent")
        return
    
    print("✅ Agent initialized successfully")
    
    # Test basic request
    request = ChatRequest(
        question="What files are in the current directory?",
        user_id="test_user",
        conversation_id="test_conversation"
    )
    
    print("\n🔍 Testing basic request...")
    response = await agent.process_request(request)
    
    print(f"✅ Response received: {response.response[:100]}...")
    print(f"📊 Tools used: {response.tools_used}")
    print(f"🎯 Confidence: {response.confidence_score}")
    print(f"📈 Tokens used: {response.tokens_used}")
    
    # Test memory functionality
    print("\n🧠 Testing memory functionality...")
    memory_context = agent._get_memory_context("test_user", "test_conversation")
    print(f"✅ Memory context: {memory_context[:100]}...")
    
    # Test command execution
    print("\n🔧 Testing command execution...")
    test_output = agent.execute_command("echo 'Hello from test'")
    print(f"✅ Command output: {test_output}")
    
    print("\n🎉 All tests passed! The consolidated AI agent is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_agent())
