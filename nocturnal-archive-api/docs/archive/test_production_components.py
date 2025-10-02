#!/usr/bin/env python3
"""
Test script to verify all production components work without external dependencies
"""

import sys
import os
sys.path.append('src')

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing Module Imports...")
    
    try:
        from src.auth.security import AuthManager
        print("✅ Authentication module imports successfully")
    except Exception as e:
        print(f"❌ Authentication import failed: {e}")
        return False
    
    try:
        from src.middleware.rate_limiting import RateLimiter
        print("✅ Rate limiting module imports successfully")
    except Exception as e:
        print(f"❌ Rate limiting import failed: {e}")
        return False
    
    try:
        from src.services.token_manager import TokenBudget
        print("✅ Token management module imports successfully")
    except Exception as e:
        print(f"❌ Token management import failed: {e}")
        return False
    
    try:
        from src.services.secure_shell import SecureShell
        print("✅ Secure shell module imports successfully")
    except Exception as e:
        print(f"❌ Secure shell import failed: {e}")
        return False
    
    return True

def test_authentication():
    """Test authentication functionality"""
    print("\n🔐 Testing Authentication System...")
    
    try:
        from src.auth.security import AuthManager
        import redis.asyncio as redis
        
        # Mock Redis client
        class MockRedis:
            async def get(self, key):
                return None
            async def setex(self, key, ttl, value):
                return True
            async def delete(self, key):
                return True
            async def scan_iter(self, match):
                return []
        
        auth_manager = AuthManager(MockRedis())
        
        # Test password hashing
        password = "test_password"[:72]  # bcrypt limit
        hashed = auth_manager.get_password_hash(password)
        verified = auth_manager.verify_password(password, hashed)
        
        if verified:
            print("✅ Password hashing works correctly")
        else:
            print("❌ Password hashing failed")
            return False
        
        # Test JWT token creation
        token = auth_manager.create_access_token({"user_id": "test_user"})
        if token:
            print("✅ JWT token creation works")
        else:
            print("❌ JWT token creation failed")
            return False
        
        # Test token verification
        payload = auth_manager.verify_token(token)
        if payload and payload.get("user_id") == "test_user":
            print("✅ JWT token verification works")
        else:
            print("❌ JWT token verification failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⏱️ Testing Rate Limiting System...")
    
    try:
        from src.middleware.rate_limiting import RateLimiter
        from fastapi import Request
        from unittest.mock import Mock
        
        # Mock Redis client
        class MockRedis:
            async def get(self, key):
                return b"5"  # 5 requests already made
            async def incrby(self, key, value):
                return 6  # Increment to 6
            async def expire(self, key, ttl):
                return True
        
        rate_limiter = RateLimiter(MockRedis())
        
        # Test client ID extraction
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.url.path = "/api/search"
        mock_request.state = Mock()
        mock_request.state.user = None
        
        client_id = rate_limiter._get_client_id(mock_request)
        if client_id == "ip:127.0.0.1":
            print("✅ Client ID extraction works")
        else:
            print(f"❌ Client ID extraction failed: got '{client_id}', expected 'ip:127.0.0.1'")
            return False
        
        # Test endpoint type detection
        endpoint_type = rate_limiter._get_endpoint_type(mock_request)
        if endpoint_type == "search":
            print("✅ Endpoint type detection works")
        else:
            print("❌ Endpoint type detection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

async def test_token_management():
    """Test token budget management"""
    print("\n💰 Testing Token Budget Management...")
    
    try:
        from src.services.token_manager import TokenBudget
        
        # Mock Redis client
        class MockRedis:
            async def get(self, key):
                return b"1000"  # 1000 tokens used
            async def incrby(self, key, value):
                return 1500  # After increment
            async def expire(self, key, ttl):
                return True
        
        budget = TokenBudget(MockRedis())
        
        # Test token estimation
        text = "This is a test sentence with multiple words."
        estimated = budget.estimate_tokens(text)
        
        if estimated > 0 and estimated < len(text):
            print(f"✅ Token estimation works: {estimated} tokens for '{text[:20]}...'")
        else:
            print("❌ Token estimation failed")
            return False
        
        # Test budget check
        can_proceed, budget_info = await budget.check_budget("test_user", 500)
        if isinstance(can_proceed, bool) and isinstance(budget_info, dict):
            print("✅ Budget check works")
        else:
            print("❌ Budget check failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Token management test failed: {e}")
        return False

def test_secure_shell():
    """Test secure shell functionality"""
    print("\n🔒 Testing Secure Shell System...")
    
    try:
        from src.services.secure_shell import SecureShell
        
        shell = SecureShell()
        
        # Test safe command validation
        safe_commands = [
            "ls", "pwd", "cat file.txt", "git status", 
            "python --version", "python -m pip list"
        ]
        
        unsafe_commands = [
            "rm -rf /", "sudo su", "chmod 777", "rm -r /", 
            "chmod +x", "python -c \"import os; os.system('rm -rf /')\""
        ]
        
        print("  Testing safe commands:")
        for cmd in safe_commands:
            if shell._is_safe_command(cmd):
                print(f"    ✅ {cmd}")
            else:
                print(f"    ❌ {cmd} (should be safe)")
                return False
        
        print("  Testing unsafe commands:")
        for cmd in unsafe_commands:
            if not shell._is_safe_command(cmd):
                print(f"    ✅ {cmd} (correctly blocked)")
            else:
                print(f"    ❌ {cmd} (should be blocked)")
                return False
        
        print("✅ Secure shell validation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Secure shell test failed: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI integration without external dependencies"""
    print("\n🚀 Testing FastAPI Integration...")
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a minimal FastAPI app
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok", "message": "Test endpoint working"}
        
        # Test the app
        client = TestClient(app)
        response = client.get("/test")
        
        if response.status_code == 200:
            print("✅ FastAPI app creation and testing works")
            return True
        else:
            print(f"❌ FastAPI test failed: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Production Components Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Authentication", test_authentication),
        ("Rate Limiting", test_rate_limiting),
        ("Token Management", test_token_management),
        ("Secure Shell", test_secure_shell),
        ("FastAPI Integration", test_fastapi_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Production components are ready.")
        return True
    else:
        print("⚠️ Some tests failed. Review the issues above.")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
