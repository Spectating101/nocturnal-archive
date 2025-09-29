#!/usr/bin/env python3
"""
User Signup Manager for R/SQL Assistant
Handles user registration and API key management
"""

import os
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests

@dataclass
class UserAccount:
    """User account information"""
    user_id: str
    email: str
    api_key: Optional[str] = None
    status: str = "pending"  # pending, active, suspended
    created_at: datetime = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class SignupManager:
    """Manages user signups and API key collection"""
    
    def __init__(self, data_file: str = "user_accounts.json"):
        self.data_file = data_file
        self.accounts: Dict[str, UserAccount] = {}
        self._load_accounts()
    
    def _load_accounts(self):
        """Load user accounts from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for user_id, account_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if account_data.get('created_at'):
                            account_data['created_at'] = datetime.fromisoformat(account_data['created_at'])
                        if account_data.get('last_used'):
                            account_data['last_used'] = datetime.fromisoformat(account_data['last_used'])
                        self.accounts[user_id] = UserAccount(**account_data)
            except Exception as e:
                print(f"Error loading accounts: {e}")
                self.accounts = {}
    
    def _save_accounts(self):
        """Save user accounts to file"""
        try:
            data = {}
            for user_id, account in self.accounts.items():
                account_dict = asdict(account)
                # Convert datetime objects to strings
                if account_dict.get('created_at'):
                    account_dict['created_at'] = account.created_at.isoformat()
                if account_dict.get('last_used'):
                    account_dict['last_used'] = account.last_used.isoformat()
                data[user_id] = account_dict
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving accounts: {e}")
    
    def register_user(self, email: str) -> str:
        """Register a new user and return user ID"""
        user_id = self._generate_user_id(email)
        
        if user_id in self.accounts:
            return user_id  # User already exists
        
        account = UserAccount(
            user_id=user_id,
            email=email,
            status="pending"
        )
        
        self.accounts[user_id] = account
        self._save_accounts()
        
        return user_id
    
    def _generate_user_id(self, email: str) -> str:
        """Generate a unique user ID from email"""
        # Create a hash of email + timestamp for uniqueness
        timestamp = str(int(time.time()))
        combined = f"{email}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def add_api_key(self, user_id: str, api_key: str) -> bool:
        """Add API key for a user"""
        if user_id not in self.accounts:
            return False
        
        # Validate API key format
        if not self._validate_api_key(api_key):
            return False
        
        self.accounts[user_id].api_key = api_key
        self.accounts[user_id].status = "active"
        self._save_accounts()
        
        return True
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate Groq API key format"""
        # Basic validation - Groq keys typically start with 'gsk_'
        return api_key.startswith('gsk_') and len(api_key) > 20
    
    def get_user_status(self, user_id: str) -> Optional[Dict]:
        """Get user account status"""
        if user_id not in self.accounts:
            return None
        
        account = self.accounts[user_id]
        return {
            "user_id": user_id,
            "email": account.email,
            "status": account.status,
            "has_api_key": account.api_key is not None,
            "created_at": account.created_at.isoformat(),
            "last_used": account.last_used.isoformat() if account.last_used else None,
            "usage_count": account.usage_count
        }
    
    def get_signup_stats(self) -> Dict:
        """Get signup statistics"""
        total = len(self.accounts)
        pending = sum(1 for acc in self.accounts.values() if acc.status == "pending")
        active = sum(1 for acc in self.accounts.values() if acc.status == "active")
        
        return {
            "total_users": total,
            "pending_signup": pending,
            "active_users": active,
            "completion_rate": (active / total * 100) if total > 0 else 0
        }
    
    def generate_signup_instructions(self, user_id: str) -> str:
        """Generate signup instructions for a user"""
        if user_id not in self.accounts:
            return "User not found"
        
        account = self.accounts[user_id]
        
        instructions = f"""
# R/SQL Assistant - Account Setup

## Your User ID: {user_id}
## Email: {account.email}

## Step 1: Create Groq Account
1. Go to: https://console.groq.com/keys
2. Click "Sign Up" 
3. Use your email: {account.email}
4. Complete email verification
5. Log in to your account

## Step 2: Generate API Key
1. In Groq console, go to "API Keys"
2. Click "Create API Key"
3. Copy the key (starts with 'gsk_')
4. Keep it secure - you'll need it for the assistant

## Step 3: Activate Your Account
Run this command with your API key:
```bash
python user_signup_manager.py activate {user_id} YOUR_API_KEY_HERE
```

## Step 4: Start Using the Assistant
```bash
./run_rstudio_assistant.sh
```

## Need Help?
- Check the setup guide: README_COMPLETE_SYSTEM.md
- Contact support if you have issues
"""
        return instructions

def main():
    """Command line interface for signup management"""
    import sys
    
    manager = SignupManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python user_signup_manager.py register <email>")
        print("  python user_signup_manager.py activate <user_id> <api_key>")
        print("  python user_signup_manager.py status <user_id>")
        print("  python user_signup_manager.py stats")
        print("  python user_signup_manager.py instructions <user_id>")
        return
    
    command = sys.argv[1]
    
    if command == "register":
        if len(sys.argv) < 3:
            print("Error: Email required")
            return
        
        email = sys.argv[2]
        user_id = manager.register_user(email)
        print(f"✅ User registered with ID: {user_id}")
        print(f"📧 Email: {email}")
        print(f"📋 Status: Pending API key")
        
        # Generate instructions
        instructions = manager.generate_signup_instructions(user_id)
        print("\n" + "="*50)
        print(instructions)
        
    elif command == "activate":
        if len(sys.argv) < 4:
            print("Error: User ID and API key required")
            return
        
        user_id = sys.argv[2]
        api_key = sys.argv[3]
        
        if manager.add_api_key(user_id, api_key):
            print(f"✅ Account activated for user: {user_id}")
            print("🎉 You can now use the R/SQL Assistant!")
        else:
            print("❌ Failed to activate account. Check user ID and API key.")
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("Error: User ID required")
            return
        
        user_id = sys.argv[2]
        status = manager.get_user_status(user_id)
        
        if status:
            print(f"📊 User Status:")
            print(f"  ID: {status['user_id']}")
            print(f"  Email: {status['email']}")
            print(f"  Status: {status['status']}")
            print(f"  Has API Key: {'✅' if status['has_api_key'] else '❌'}")
            print(f"  Created: {status['created_at']}")
            if status['last_used']:
                print(f"  Last Used: {status['last_used']}")
            print(f"  Usage Count: {status['usage_count']}")
        else:
            print("❌ User not found")
    
    elif command == "stats":
        stats = manager.get_signup_stats()
        print(f"📊 Signup Statistics:")
        print(f"  Total Users: {stats['total_users']}")
        print(f"  Pending: {stats['pending_signup']}")
        print(f"  Active: {stats['active_users']}")
        print(f"  Completion Rate: {stats['completion_rate']:.1f}%")
    
    elif command == "instructions":
        if len(sys.argv) < 3:
            print("Error: User ID required")
            return
        
        user_id = sys.argv[2]
        instructions = manager.generate_signup_instructions(user_id)
        print(instructions)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
