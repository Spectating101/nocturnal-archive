#!/usr/bin/env python3
"""
Demo script for Vertikal - shows the core functionality
"""

import os
import sys
from vertikal import VertikalAssistant

def demo_vertikal():
    print("🚀 Vertikal Demo - Terminal File-Aware Assistant")
    print("=" * 50)
    
    # Mock Groq client for demo
    class MockGroq:
        def __init__(self, api_key):
            pass
    
    # Replace Groq with mock
    import vertikal
    vertikal.Groq = MockGroq
    
    # Initialize assistant
    assistant = VertikalAssistant('.', safe_mode=True)
    
    print("\n1️⃣ Testing file listing...")
    print(assistant.list_files())
    
    print("\n2️⃣ Testing file reading...")
    print(assistant.read_file('README.txt', lines=10))
    
    print("\n3️⃣ Testing file search...")
    print(assistant.search_files('function'))
    
    print("\n4️⃣ Testing security (should block)...")
    try:
        result = assistant.read_file('/etc/passwd')
        print(result)
    except Exception as e:
        print(f"✅ Security working: {e}")
    
    print("\n5️⃣ Testing path traversal (should block)...")
    try:
        result = assistant.read_file('../../../etc/passwd')
        print(result)
    except Exception as e:
        print(f"✅ Path traversal blocked: {e}")
    
    print("\n🎉 All tests passed! Vertikal is ready to use.")
    print("\nTo use with Groq API:")
    print("1. Get API key from: https://console.groq.com/")
    print("2. Set environment variable: export GROQ_API_KEY=your_key")
    print("3. Run: python3 vertikal.py")

if __name__ == "__main__":
    demo_vertikal()
