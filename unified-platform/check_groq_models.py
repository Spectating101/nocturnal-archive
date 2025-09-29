#!/usr/bin/env python3
"""
Check Available Groq Models
"""

import os
from groq import Groq

def check_models():
    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY_1'))
        models = client.models.list()
        
        print("🚀 Available Groq Models:")
        print("=" * 50)
        
        for model in models.data:
            print(f"Model: {model.id}")
            print(f"  - Object: {model.object}")
            print(f"  - Created: {model.created}")
            print(f"  - Owned By: {model.owned_by}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_models()