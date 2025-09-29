#!/usr/bin/env python3
"""
Simple R/SQL Assistant using Groq API
Provides interactive help with R and SQL commands
"""

import os
import sys
from groq import Groq

def get_groq_client():
    """Initialize Groq client with API key"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set!")
        print("📝 Get your free API key at: https://console.groq.com/keys")
        print("🔧 Set it with: export GROQ_API_KEY='your-key-here'")
        return None
    
    try:
        client = Groq(api_key=api_key)
        return client
    except Exception as e:
        print(f"❌ Error initializing Groq client: {e}")
        return None

def ask_groq(client, question):
    """Send question to Groq and get response"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant for R and SQL programming. 
                    Provide clear, concise answers with code examples when appropriate.
                    Focus on practical solutions and best practices.
                    If asked about R, provide R code examples.
                    If asked about SQL, provide SQL examples.
                    Always explain what the code does."""
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error getting response: {e}"

def main():
    """Main interactive loop"""
    print("🤖 R/SQL Assistant with Groq")
    print("=" * 40)
    print("💡 Ask me anything about R or SQL commands!")
    print("📝 Type 'quit' or 'exit' to stop")
    print("🔧 Make sure GROQ_API_KEY is set in your environment")
    print()
    
    client = get_groq_client()
    if not client:
        return
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            response = ask_groq(client, question)
            print(f"\n🤖 Assistant:\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()