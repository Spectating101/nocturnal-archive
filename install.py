#!/usr/bin/env python3
"""
Nocturnal Archive Installation Script
Installs the package and runs initial setup
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def install_package():
    """Install the package in development mode"""
    print("🚀 Installing Nocturnal Archive...")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Try direct installation first
    if run_command("pip install -e .", "Installing package in development mode"):
        # Install optional dependencies for better experience
        print("\n📦 Installing optional dependencies...")
        run_command("pip install python-dotenv", "Installing python-dotenv")
        run_command("pip install aiohttp", "Installing aiohttp")
    else:
        # If direct installation fails, try with virtual environment
        print("⚠️ Direct installation failed, creating virtual environment...")
        
        # Create virtual environment
        if not run_command("python3 -m venv nocturnal-venv", "Creating virtual environment"):
            return False
        
        # Install in virtual environment
        venv_pip = "./nocturnal-venv/bin/pip"
        if not run_command(f"{venv_pip} install -e .", "Installing package in virtual environment"):
            return False
        
        # Install optional dependencies
        run_command(f"{venv_pip} install python-dotenv", "Installing python-dotenv")
        run_command(f"{venv_pip} install aiohttp", "Installing aiohttp")
        
        print("🔧 Package installed in virtual environment: ./nocturnal-venv/")
        print("   To activate: source nocturnal-venv/bin/activate")
    
    print("\n✅ Installation completed!")
    return True

def run_setup():
    """Run initial setup"""
    print("\n🔧 Running initial setup...")
    print("=" * 30)
    
    try:
        from nocturnal_archive.setup_config import auto_setup
        return auto_setup()
    except ImportError as e:
        print(f"❌ Could not import setup module: {e}")
        print("Try running: python -m nocturnal_archive.setup_config")
        return False

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    print("=" * 30)
    
    try:
        from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest
        print("✅ Package imports successfully")
        
        # Test basic functionality
        agent = EnhancedNocturnalAgent()
        print("✅ Agent class instantiated")
        
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main installation process"""
    print("🌙 Nocturnal Archive - Installation & Setup")
    print("=" * 50)
    
    # Step 1: Install package
    if not install_package():
        print("\n❌ Installation failed. Please check the errors above.")
        return False
    
    # Step 2: Test installation
    if not test_installation():
        print("\n❌ Installation test failed. Please check the errors above.")
        return False
    
    # Step 3: Run setup
    if not run_setup():
        print("\n⚠️  Setup was skipped or failed. You can run it later with:")
        print("   python -m nocturnal_archive.setup_config")
        print("\n✅ Installation completed successfully!")
        print("\n🎉 Ready to use Nocturnal Archive!")
        print("\nQuick start:")
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
        return True
    
    print("\n🎉 Installation and setup completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
