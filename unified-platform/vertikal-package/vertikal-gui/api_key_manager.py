#!/usr/bin/env python3
"""
API Key Manager - Handles API key input, storage, and rotation
"""

import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import getpass

class APIKeyManager:
    def __init__(self, config_dir=None):
        if config_dir is None:
            # Use user's home directory for config
            self.config_dir = Path.home() / ".vertikal"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        
        # Initialize encryption key
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.encryption_key)
            # Make key file readable only by owner
            os.chmod(self.key_file, 0o600)
    
    def _encrypt_data(self, data):
        """Encrypt data"""
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt data"""
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    
    def get_api_key(self):
        """Get stored API key"""
        # First check environment variable
        env_key = os.getenv("GROQ_API_KEY")
        if env_key:
            return env_key
        
        # Then check config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                if 'api_key' in config:
                    return self._decrypt_data(config['api_key'])
            except Exception as e:
                print(f"Error reading config: {e}")
        
        return None
    
    def set_api_key(self, api_key):
        """Set and store API key"""
        if not api_key or not api_key.strip():
            return False
        
        try:
            # Load existing config or create new
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Encrypt and store API key
            config['api_key'] = self._encrypt_data(api_key.strip())
            config['last_updated'] = str(Path().cwd())  # Simple timestamp
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set environment variable
            os.environ['GROQ_API_KEY'] = api_key.strip()
            
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False
    
    def update_api_key(self, new_api_key):
        """Update existing API key"""
        return self.set_api_key(new_api_key)
    
    def clear_api_key(self):
        """Clear stored API key"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                if 'api_key' in config:
                    del config['api_key']
                
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            # Clear environment variable
            if 'GROQ_API_KEY' in os.environ:
                del os.environ['GROQ_API_KEY']
            
            return True
        except Exception as e:
            print(f"Error clearing API key: {e}")
            return False
    
    def has_api_key(self):
        """Check if API key is set"""
        return self.get_api_key() is not None
    
    def get_api_key_info(self):
        """Get API key information (without revealing the key)"""
        if not self.has_api_key():
            return {
                'has_key': False,
                'source': None,
                'last_updated': None
            }
        
        source = 'environment' if os.getenv("GROQ_API_KEY") else 'config_file'
        
        last_updated = None
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                last_updated = config.get('last_updated', 'Unknown')
            except:
                pass
        
        return {
            'has_key': True,
            'source': source,
            'last_updated': last_updated
        }

class APIKeySetup:
    """Interactive API key setup"""
    
    def __init__(self):
        self.manager = APIKeyManager()
    
    def show_setup_dialog(self):
        """Show API key setup dialog"""
        print("🔑 Vertikal API Key Setup")
        print("=" * 30)
        
        # Check if key already exists
        if self.manager.has_api_key():
            info = self.manager.get_api_key_info()
            print(f"✅ API key already configured")
            print(f"📁 Source: {info['source']}")
            print(f"🕒 Last updated: {info['last_updated']}")
            
            update = input("\nUpdate API key? (y/n): ").strip().lower()
            if update != 'y':
                return True
        
        print("\n💡 Get your free Groq API key at: https://console.groq.com/")
        print("1. Sign up for free account")
        print("2. Create API key")
        print("3. Copy the key")
        
        while True:
            api_key = getpass.getpass("\nEnter your Groq API key: ").strip()
            
            if not api_key:
                print("❌ API key cannot be empty")
                continue
            
            if not api_key.startswith('gsk_'):
                print("⚠️ Warning: Groq API keys usually start with 'gsk_'")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            # Test the API key
            print("🧪 Testing API key...")
            if self._test_api_key(api_key):
                if self.manager.set_api_key(api_key):
                    print("✅ API key saved successfully!")
                    return True
                else:
                    print("❌ Failed to save API key")
                    return False
            else:
                print("❌ API key test failed")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
    
    def _test_api_key(self, api_key):
        """Test API key by making a simple request"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple test request
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json={
                    'model': 'llama-3.1-8b-instant',
                    'messages': [{'role': 'user', 'content': 'Hello'}],
                    'max_tokens': 10
                },
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Test error: {e}")
            return False
    
    def show_management_menu(self):
        """Show API key management menu"""
        while True:
            print("\n🔑 API Key Management")
            print("=" * 25)
            print("1. View API key status")
            print("2. Update API key")
            print("3. Clear API key")
            print("4. Test API key")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self._show_status()
            elif choice == '2':
                self._update_key()
            elif choice == '3':
                self._clear_key()
            elif choice == '4':
                self._test_current_key()
            elif choice == '5':
                break
            else:
                print("❌ Invalid option")
    
    def _show_status(self):
        """Show API key status"""
        info = self.manager.get_api_key_info()
        
        print(f"\n📊 API Key Status:")
        print(f"Has key: {'✅ Yes' if info['has_key'] else '❌ No'}")
        if info['has_key']:
            print(f"Source: {info['source']}")
            print(f"Last updated: {info['last_updated']}")
    
    def _update_key(self):
        """Update API key"""
        print("\n🔄 Update API Key")
        api_key = getpass.getpass("Enter new API key: ").strip()
        
        if api_key:
            if self.manager.update_api_key(api_key):
                print("✅ API key updated successfully!")
            else:
                print("❌ Failed to update API key")
        else:
            print("❌ API key cannot be empty")
    
    def _clear_key(self):
        """Clear API key"""
        confirm = input("\n⚠️ Are you sure you want to clear the API key? (y/n): ").strip().lower()
        if confirm == 'y':
            if self.manager.clear_api_key():
                print("✅ API key cleared successfully!")
            else:
                print("❌ Failed to clear API key")
    
    def _test_current_key(self):
        """Test current API key"""
        api_key = self.manager.get_api_key()
        if not api_key:
            print("❌ No API key configured")
            return
        
        print("🧪 Testing current API key...")
        if self._test_api_key(api_key):
            print("✅ API key is working!")
        else:
            print("❌ API key test failed")

def main():
    """Main entry point for API key management"""
    setup = APIKeySetup()
    setup.show_management_menu()

if __name__ == "__main__":
    main()
