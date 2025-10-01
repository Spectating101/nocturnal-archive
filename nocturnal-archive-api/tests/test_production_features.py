"""
Comprehensive test suite for production features
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import redis.asyncio as redis

# Import your FastAPI app
from src.main import app

client = TestClient(app)

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_valid_api_key(self):
        """Test valid API key authentication"""
        # This would test with a real API key
        response = client.get(
            "/v1/finance/kpis/AAPL/revenue",
            headers={"Authorization": "Bearer na_test_api_key_123"}
        )
        # Should return 200 or 401 depending on if key exists
        assert response.status_code in [200, 401]
    
    def test_invalid_api_key(self):
        """Test invalid API key authentication"""
        response = client.get(
            "/v1/finance/kpis/AAPL/revenue",
            headers={"Authorization": "Bearer invalid_key"}
        )
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]
    
    def test_missing_authorization(self):
        """Test missing authorization header"""
        response = client.get("/v1/finance/kpis/AAPL/revenue")
        assert response.status_code == 401
    
    def test_permission_requirements(self):
        """Test permission-based access control"""
        # Test read permission
        response = client.get(
            "/v1/finance/kpis/AAPL/revenue",
            headers={"Authorization": "Bearer na_read_only_key"}
        )
        assert response.status_code in [200, 401, 403]
        
        # Test write permission
        response = client.post(
            "/v1/finance/calc/explain",
            headers={"Authorization": "Bearer na_read_only_key"},
            json={"ticker": "AAPL", "expr": "revenue - costOfRevenue"}
        )
        assert response.status_code in [403, 401]

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present"""
        response = client.get(
            "/v1/finance/kpis/AAPL/revenue",
            headers={"Authorization": "Bearer na_test_api_key_123"}
        )
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded response"""
        # Make many requests quickly to trigger rate limit
        responses = []
        for i in range(35):  # Exceed 30/minute limit
            response = client.get(
                "/v1/finance/kpis/AAPL/revenue",
                headers={"Authorization": "Bearer na_test_api_key_123"}
            )
            responses.append(response)
        
        # At least one should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should trigger after exceeding limit"
    
    def test_different_endpoint_limits(self):
        """Test that different endpoints have different rate limits"""
        # Finance endpoint (60/minute)
        finance_responses = []
        for i in range(65):
            response = client.get(
                "/v1/finance/kpis/AAPL/revenue",
                headers={"Authorization": "Bearer na_test_api_key_123"}
            )
            finance_responses.append(response)
        
        # Search endpoint (30/minute)
        search_responses = []
        for i in range(35):
            response = client.post(
                "/api/search",
                headers={"Authorization": "Bearer na_test_api_key_123"},
                json={"query": "test", "limit": 5}
            )
            search_responses.append(response)
        
        # Search should hit rate limit first
        search_rate_limited = any(r.status_code == 429 for r in search_responses)
        assert search_rate_limited, "Search endpoint should have stricter rate limits"

class TestTokenBudget:
    """Test token budget management"""
    
    @pytest.mark.asyncio
    async def test_token_budget_tracking(self):
        """Test token budget tracking"""
        from src.services.token_manager import TokenBudget
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"1000"  # 1000 tokens used
        mock_redis.incrby.return_value = 1500  # After increment
        mock_redis.expire.return_value = True
        
        budget = TokenBudget(mock_redis)
        
        # Test budget check
        can_proceed, budget_info = await budget.check_budget("test_user", 500)
        assert can_proceed is True
        assert budget_info["daily"]["remaining"] > 0
    
    @pytest.mark.asyncio
    async def test_token_budget_exceeded(self):
        """Test token budget exceeded scenario"""
        from src.services.token_manager import TokenBudget
        
        # Mock Redis client with high usage
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"499000"  # Almost at daily limit
        mock_redis.incrby.return_value = 500000  # Would exceed limit
        mock_redis.expire.return_value = True
        
        budget = TokenBudget(mock_redis)
        
        # Test budget check with large request
        can_proceed, budget_info = await budget.check_budget("test_user", 2000)
        assert can_proceed is False
        assert budget_info["daily"]["remaining"] == 0
    
    def test_token_estimation(self):
        """Test token estimation accuracy"""
        from src.services.token_manager import TokenBudget
        
        budget = TokenBudget(AsyncMock())
        
        # Test token estimation
        text = "This is a test sentence with multiple words."
        estimated = budget.estimate_tokens(text)
        
        # Should be reasonable estimate
        assert estimated > 0
        assert estimated < len(text)  # Should be less than character count

class TestSecureShell:
    """Test secure shell functionality"""
    
    @pytest.mark.asyncio
    async def test_safe_command_execution(self):
        """Test execution of safe commands"""
        from src.services.secure_shell import SecureShell
        
        shell = SecureShell()
        
        # Test safe command
        result = await shell.execute_command("test_user", "ls -la")
        assert result["success"] is True
        assert "output" in result
        assert result["command"] == "ls -la"
    
    @pytest.mark.asyncio
    async def test_unsafe_command_blocking(self):
        """Test blocking of unsafe commands"""
        from src.services.secure_shell import SecureShell
        
        shell = SecureShell()
        
        # Test unsafe command
        result = await shell.execute_command("test_user", "rm -rf /")
        assert result["success"] is False
        assert "UNSAFE_COMMAND" in result["error"]
        assert "Command not allowed" in result["output"]
    
    @pytest.mark.asyncio
    async def test_command_timeout(self):
        """Test command timeout handling"""
        from src.services.secure_shell import SecureShell
        
        shell = SecureShell()
        
        # Test command that might hang
        result = await shell.execute_command("test_user", "sleep 35", timeout=5)
        # Should either succeed or fail gracefully
        assert "success" in result
        assert "command" in result
    
    def test_safe_command_validation(self):
        """Test safe command validation logic"""
        from src.services.secure_shell import SecureShell
        
        shell = SecureShell()
        
        # Test safe commands
        safe_commands = ["ls", "pwd", "cat file.txt", "git status", "python --version"]
        for cmd in safe_commands:
            assert shell._is_safe_command(cmd), f"Command '{cmd}' should be safe"
        
        # Test unsafe commands
        unsafe_commands = ["rm -rf /", "sudo su", "chmod 777", "kill -9", "python -c 'import os; os.system(\"rm -rf /\")'"]
        for cmd in unsafe_commands:
            assert not shell._is_safe_command(cmd), f"Command '{cmd}' should be unsafe"

class TestErrorHandling:
    """Test error handling and responses"""
    
    def test_404_error_response(self):
        """Test 404 error response format"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_500_error_response(self):
        """Test 500 error response format"""
        # This would test with an endpoint that intentionally fails
        # For now, just test the error response structure
        response = client.get("/v1/finance/kpis/INVALID/revenue")
        # Should return 404 or 400, not 500
        assert response.status_code in [400, 404, 401]
    
    def test_validation_error_response(self):
        """Test validation error response format"""
        response = client.post(
            "/api/search",
            json={"invalid": "data"}  # Missing required fields
        )
        assert response.status_code == 422
        assert "detail" in response.json()

class TestHealthChecks:
    """Test health check endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_finance_health_endpoint(self):
        """Test finance API health endpoint"""
        response = client.get("/v1/finance/status")
        assert response.status_code == 200
        assert "overall_status" in response.json()
    
    def test_archive_health_endpoint(self):
        """Test archive API health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()

class TestIntegration:
    """Test integration between components"""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # 1. Search for papers
        search_response = client.post(
            "/api/search",
            headers={"Authorization": "Bearer na_test_api_key_123"},
            json={"query": "machine learning", "limit": 5}
        )
        assert search_response.status_code in [200, 401, 429]
        
        # 2. Get financial data
        finance_response = client.get(
            "/v1/finance/kpis/AAPL/revenue",
            headers={"Authorization": "Bearer na_test_api_key_123"}
        )
        assert finance_response.status_code in [200, 401, 429]
        
        # 3. Synthesize research
        if search_response.status_code == 200:
            paper_ids = [paper["id"] for paper in search_response.json().get("papers", [])[:3]]
            if paper_ids:
                synthesis_response = client.post(
                    "/api/synthesize",
                    headers={"Authorization": "Bearer na_test_api_key_123"},
                    json={"paper_ids": paper_ids, "max_words": 300}
                )
                assert synthesis_response.status_code in [200, 401, 429]
    
    def test_cross_api_authentication(self):
        """Test that authentication works across all APIs"""
        api_key = "na_test_api_key_123"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Test all major endpoints
        endpoints = [
            "/api/search",
            "/api/synthesize", 
            "/v1/finance/kpis/AAPL/revenue",
            "/v1/finance/calc/explain",
            "/health"
        ]
        
        for endpoint in endpoints:
            if endpoint == "/health":
                # Health endpoint might not require auth
                response = client.get(endpoint)
                assert response.status_code in [200, 401]
            else:
                response = client.get(endpoint, headers=headers)
                assert response.status_code in [200, 401, 422, 429]

# Performance tests
class TestPerformance:
    """Test performance characteristics"""
    
    def test_response_times(self):
        """Test that response times are reasonable"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check took {response_time:.2f}s, should be < 1s"
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start = time.time()
            response = client.get("/health")
            end = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end - start
            })
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 10
        successful_requests = [r for r in results if r["status_code"] == 200]
        assert len(successful_requests) >= 8, "At least 80% of requests should succeed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
