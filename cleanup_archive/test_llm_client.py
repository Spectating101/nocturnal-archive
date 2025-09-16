#!/usr/bin/env python3
"""
Test LLM client directly
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

async def test_mistral_client():
    """Test Mistral client directly"""
    from src.services.llm_service.api_clients.mistral_client import MistralClient
    
    api_key = os.environ.get('MISTRAL_API_KEY')
    print(f"Testing Mistral client with API key: {api_key[:10]}...")
    
    client = MistralClient(api_key)
    
    # Test with a simple paper
    test_papers = [{
        "doc_id": "test_paper",
        "title": "Test Research Paper",
        "main_findings": [
            "Machine learning shows promise in drug discovery",
            "Multiple approaches are being explored",
            "Future research directions are promising"
        ],
        "raw_text": "This is a test paper about machine learning in drug discovery.",
        "authors": ["Test Author"],
        "year": 2024,
        "journal": "Test Journal"
    }]
    
    try:
        result = await client.generate_synthesis(test_papers, "Test research topic")
        print("✅ Mistral client synthesis successful!")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Mistral client synthesis failed: {e}")
        return False

async def test_cohere_client():
    """Test Cohere client directly"""
    from src.services.llm_service.api_clients.cohere_client import CohereClient
    
    api_key = os.environ.get('COHERE_API_KEY')
    print(f"Testing Cohere client with API key: {api_key[:10]}...")
    
    client = CohereClient(api_key)
    
    # Test with a simple paper
    test_papers = [{
        "doc_id": "test_paper",
        "title": "Test Research Paper",
        "main_findings": [
            "Machine learning shows promise in drug discovery",
            "Multiple approaches are being explored",
            "Future research directions are promising"
        ],
        "raw_text": "This is a test paper about machine learning in drug discovery.",
        "authors": ["Test Author"],
        "year": 2024,
        "journal": "Test Journal"
    }]
    
    try:
        result = await client.generate_synthesis(test_papers, "Test research topic")
        print("✅ Cohere client synthesis successful!")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Cohere client synthesis failed: {e}")
        return False

async def test_cerebras_client():
    """Test Cerebras client directly"""
    from src.services.llm_service.api_clients.cerebras_client import CerebrasClient
    
    api_key = os.environ.get('CEREBRAS_API_KEY')
    print(f"Testing Cerebras client with API key: {api_key[:10]}...")
    
    client = CerebrasClient(api_key)
    
    # Test with a simple paper
    test_papers = [{
        "doc_id": "test_paper",
        "title": "Test Research Paper",
        "main_findings": [
            "Machine learning shows promise in drug discovery",
            "Multiple approaches are being explored",
            "Future research directions are promising"
        ],
        "raw_text": "This is a test paper about machine learning in drug discovery.",
        "authors": ["Test Author"],
        "year": 2024,
        "journal": "Test Journal"
    }]
    
    try:
        result = await client.generate_synthesis(test_papers, "Test research topic")
        print("✅ Cerebras client synthesis successful!")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Cerebras client synthesis failed: {e}")
        return False

async def main():
    """Test all LLM clients directly"""
    print("🔑 Testing LLM Clients Directly...")
    print("=" * 50)
    
    results = await asyncio.gather(
        test_mistral_client(),
        test_cohere_client(),
        test_cerebras_client(),
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
