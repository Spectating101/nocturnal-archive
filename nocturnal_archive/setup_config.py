#!/usr/bin/env python3
"""
Automatic setup and configuration for Nocturnal Archive
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class NocturnalConfig:
    """Handles automatic configuration and setup"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".nocturnal_archive"
        self.config_file = self.config_dir / "config.env"
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
    
    def interactive_setup(self) -> bool:
        """Interactive setup for API keys and configuration"""
        print("🚀 Nocturnal Archive Setup")
        print("=" * 40)
        print()
        
        # Check if already configured
        if self.config_file.exists():
            print("✅ Configuration already exists!")
            response = input("Do you want to reconfigure? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                return True
        
        print("Let's set up your API keys for the best experience:")
        print()
        
        # Get Groq API key
        groq_key = self._get_groq_api_key()
        if not groq_key:
            print("❌ Groq API key is required for the AI agent functionality")
            return False
        
        # Optional API keys
        print("\n📚 Optional: Academic Research APIs (for enhanced paper search)")
        openalex_key = input("OpenAlex API key (optional, press Enter to skip): ").strip()
        pubmed_key = input("PubMed API key (optional, press Enter to skip): ").strip()
        
        print("\n💰 Optional: Additional Financial Data APIs")
        alpha_vantage_key = input("Alpha Vantage API key (optional, press Enter to skip): ").strip()
        
        # Save configuration
        config = {
            "GROQ_API_KEY": groq_key,
            "OPENALEX_API_KEY": openalex_key,
            "PUBMED_API_KEY": pubmed_key,
            "ALPHA_VANTAGE_API_KEY": alpha_vantage_key,
            "NOCTURNAL_CONFIG_VERSION": "1.0.0"
        }
        
        self.save_config(config)
        
        print("\n✅ Configuration saved successfully!")
        print(f"📁 Config location: {self.config_file}")
        print("\n🎉 You're ready to use Nocturnal Archive!")
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
    
    def _get_groq_api_key(self) -> Optional[str]:
        """Get Groq API key from user"""
        print("🔑 Groq API Key Setup")
        print("You need a Groq API key for the AI agent functionality.")
        print("Get yours at: https://console.groq.com/keys")
        print()
        
        # Check if already set in environment
        existing_key = os.getenv('GROQ_API_KEY')
        if existing_key:
            print(f"✅ Found existing GROQ_API_KEY in environment")
            use_existing = input("Use existing key? (Y/n): ").strip().lower()
            if use_existing in ['', 'y', 'yes']:
                return existing_key
        
        # Get new key
        while True:
            api_key = input("Enter your Groq API key: ").strip()
            if not api_key:
                print("❌ API key cannot be empty")
                continue
            
            if not api_key.startswith('gsk_'):
                print("⚠️  Groq API keys typically start with 'gsk_'")
                confirm = input("Continue anyway? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            
            return api_key
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            f.write("# Nocturnal Archive Configuration\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            for key, value in config.items():
                if value:  # Only save non-empty values
                    f.write(f"{key}={value}\n")
    
    def load_config(self) -> Dict[str, str]:
        """Load configuration from file"""
        config = {}
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
        return config
    
    def setup_environment(self):
        """Set up environment variables from config"""
        config = self.load_config()
        for key, value in config.items():
            if not os.getenv(key):  # Don't override existing env vars
                os.environ[key] = value
        return len(config) > 0
    
    def check_setup(self) -> bool:
        """Check if setup is complete"""
        return self.config_file.exists() and self.load_config().get('GROQ_API_KEY')
    
    def get_setup_status(self) -> Dict[str, Any]:
        """Get detailed setup status"""
        config = self.load_config()
        return {
            "configured": self.check_setup(),
            "config_file": str(self.config_file),
            "groq_configured": bool(config.get('GROQ_API_KEY')),
            "openalex_configured": bool(config.get('OPENALEX_API_KEY')),
            "pubmed_configured": bool(config.get('PUBMED_API_KEY')),
            "alpha_vantage_configured": bool(config.get('ALPHA_VANTAGE_API_KEY')),
            "config_keys": list(config.keys())
        }

def auto_setup():
    """Automatic setup function"""
    config = NocturnalConfig()
    
    # Try to setup environment from existing config
    if config.setup_environment():
        return True
    
    # If no config exists, run interactive setup
    print("🔧 Nocturnal Archive needs initial setup")
    return config.interactive_setup()

def get_config():
    """Get configuration instance"""
    return NocturnalConfig()

if __name__ == "__main__":
    auto_setup()
