"""
Tests for the Advanced Reasoning Engine
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.services.reasoning_engine.reasoning_engine import ReasoningEngine, ReasoningState

class TestReasoningEngine:
    """Test cases for the Reasoning Engine."""
    
    @pytest.fixture
    def reasoning_engine(self):
        """Create a reasoning engine instance for testing."""
        return ReasoningEngine()
    
    @pytest.mark.asyncio
    async def test_solve_simple_problem(self, reasoning_engine):
        """Test solving a simple problem."""
        problem = "What is 2 + 2?"
        context = {"domain": "mathematics"}
        
        result = await reasoning_engine.solve_problem(problem, context)
        
        assert result["status"] == "success"
        assert "session_id" in result
        assert "solution" in result
        assert "reasoning_trace" in result
        assert "execution_summary" in result
    
    @pytest.mark.asyncio
    async def test_problem_decomposition(self, reasoning_engine):
        """Test problem decomposition functionality."""
        problem = "Analyze the performance of our web application"
        context = {"application_type": "web"}
        
        result = await reasoning_engine.solve_problem(problem, context)
        
        # Check that the problem was decomposed into steps
        reasoning_trace = result["reasoning_trace"]
        assert len(reasoning_trace) > 0
        
        # Check that each step has required fields
        for step in reasoning_trace:
            assert "step_id" in step
            assert "description" in step
            assert "status" in step
    
    @pytest.mark.asyncio
    async def test_session_management(self, reasoning_engine):
        """Test session management functionality."""
        problem = "Test session management"
        
        result = await reasoning_engine.solve_problem(problem)
        session_id = result["session_id"]
        
        # Check session status
        status = await reasoning_engine.get_session_status(session_id)
        assert status["status"] != "not_found"
        assert "state" in status
        assert "progress" in status
    
    @pytest.mark.asyncio
    async def test_error_handling(self, reasoning_engine):
        """Test error handling in reasoning engine."""
        # Test with invalid input
        with patch.object(reasoning_engine, '_analyze_problem', side_effect=Exception("Test error")):
            result = await reasoning_engine.solve_problem("Test problem")
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "partial_results" in result
    
    @pytest.mark.asyncio
    async def test_execution_monitoring(self, reasoning_engine):
        """Test execution monitoring functionality."""
        problem = "Test execution monitoring"
        
        result = await reasoning_engine.solve_problem(problem)
        
        # Check execution summary
        execution_summary = result["execution_summary"]
        assert "total_steps" in execution_summary
        assert "successful_steps" in execution_summary
        assert "failed_steps" in execution_summary
        assert "total_execution_time" in execution_summary
    
    @pytest.mark.asyncio
    async def test_context_integration(self, reasoning_engine):
        """Test integration with context information."""
        problem = "Test context integration"
        context = {
            "user_preferences": {"language": "python"},
            "project_info": {"type": "web_application"},
            "previous_solutions": ["solution1", "solution2"]
        }
        
        result = await reasoning_engine.solve_problem(problem, context)
        
        assert result["status"] == "success"
        # Context should influence the solution approach
        assert "metadata" in result
