#!/usr/bin/env python3
"""
Simple installation script for Nocturnal Archive
No interactive prompts - just install and go!
"""

import sys
import subprocess

def install_package():
    """Install the package"""
    print("🚀 Installing Nocturnal Archive...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Installation completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest
        print("✅ Package imports successfully")
        
        agent = EnhancedNocturnalAgent()
        print("✅ Agent class instantiated")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main installation"""
    print("🌙 Nocturnal Archive - Simple Installation")
    print("=" * 45)
    
    if not install_package():
        return False
    
    if not test_installation():
        return False
    
    print("\n🎉 Installation successful!")
    print("\n📚 Quick Start:")
    print("```python")
    print("from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest")
    print("import asyncio")
    print()
    print("async def main():")
    print("    agent = EnhancedNocturnalAgent()")
    print("    await agent.initialize()")
    print("    # Your code here...")
    print("    await agent.close()")
    print()
    print("asyncio.run(main())")
    print("```")
    print("\n💡 Note: API keys can be set later when you first use the agent")
    print("   or via environment variables (GROQ_API_KEY, etc.)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
