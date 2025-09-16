#!/usr/bin/env python3
"""
Test API keys functionality
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

async def test_mistral_api():
    """Test Mistral API key"""
    import aiohttp
    
    api_key = os.environ.get('MISTRAL_API_KEY')
    if not api_key:
        print("❌ MISTRAL_API_KEY not found")
        return False
    
    url = "https://api.mistral.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print("✅ Mistral API key is valid")
                    return True
                else:
                    print(f"❌ Mistral API error: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Mistral API test failed: {e}")
        return False

async def test_cohere_api():
    """Test Cohere API key"""
    import aiohttp
    
    api_key = os.environ.get('COHERE_API_KEY')
    if not api_key:
        print("❌ COHERE_API_KEY not found")
        return False
    
    url = "https://api.cohere.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print("✅ Cohere API key is valid")
                    return True
                else:
                    print(f"❌ Cohere API error: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Cohere API test failed: {e}")
        return False

async def test_cerebras_api():
    """Test Cerebras API key"""
    import aiohttp
    
    api_key = os.environ.get('CEREBRAS_API_KEY')
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found")
        return False
    
    url = "https://api.cerebras.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print("✅ Cerebras API key is valid")
                    return True
                else:
                    print(f"❌ Cerebras API error: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Cerebras API test failed: {e}")
        return False

async def main():
    """Test all API keys"""
    print("🔑 Testing API Keys...")
    print("=" * 50)
    
    results = await asyncio.gather(
        test_mistral_api(),
        test_cohere_api(),
        test_cerebras_api(),
        return_exceptions=True
    )
    
    print("\n📊 Results Summary:")
    print("-" * 30)
    
    services = ["Mistral", "Cohere", "Cerebras"]
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ {services[i]}: Exception - {result}")
        elif result:
            print(f"✅ {services[i]}: Working")
        else:
            print(f"❌ {services[i]}: Failed")

if __name__ == "__main__":
    asyncio.run(main())
