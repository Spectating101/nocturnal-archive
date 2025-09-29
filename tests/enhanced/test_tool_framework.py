"""
Tests for the Dynamic Tool Framework
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.services.tool_framework.tool_manager import ToolManager
from src.services.tool_framework.code_execution_tool import CodeExecutionTool
from src.services.tool_framework.file_operations_tool import FileOperationsTool

class TestToolManager:
    """Test cases for the Tool Manager."""
    
    @pytest.fixture
    def tool_manager(self):
        """Create a tool manager instance for testing."""
        return ToolManager()
    
    @pytest.mark.asyncio
    async def test_tool_selection(self, tool_manager):
        """Test automatic tool selection."""
        # Test code-related task
        tool = await tool_manager.select_best_tool("Write a Python function to calculate fibonacci")
        assert tool == "code_execution"
        
        # Test file-related task
        tool = await tool_manager.select_best_tool("Read the contents of config.json")
        assert tool == "file_operations"
        
        # Test search-related task
        tool = await tool_manager.select_best_tool("Search for information about machine learning")
        assert tool == "web_search"
    
    @pytest.mark.asyncio
    async def test_tool_execution(self, tool_manager):
        """Test tool execution."""
        result = await tool_manager.execute_tool(
            "llm_reasoning",
            "Analyze this problem and provide a solution",
            {"context": "test"}
        )
        
        assert "status" in result
        assert "result" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_auto_execution(self, tool_manager):
        """Test automatic tool selection and execution."""
        result = await tool_manager.execute_with_auto_selection(
            "Calculate the sum of numbers 1 to 10",
            {"numbers": list(range(1, 11))}
        )
        
        assert "status" in result
        assert "result" in result
    
    def test_tool_capabilities(self, tool_manager):
        """Test tool capabilities retrieval."""
        capabilities = tool_manager.get_tool_capabilities("code_execution")
        assert "python" in capabilities
        assert "javascript" in capabilities
        
        capabilities = tool_manager.get_tool_capabilities("file_operations")
        assert "read" in capabilities
        assert "write" in capabilities
    
    def test_available_tools(self, tool_manager):
        """Test available tools listing."""
        tools = tool_manager.get_available_tools()
        assert "code_execution" in tools
        assert "file_operations" in tools
        assert "web_search" in tools
        assert "data_analysis" in tools
        assert "api_calls" in tools
    
    def test_performance_stats(self, tool_manager):
        """Test performance statistics."""
        stats = tool_manager.get_tool_performance_stats("code_execution")
        assert "total_executions" in stats
        assert "successful_executions" in stats
        assert "failed_executions" in stats
        assert "success_rate" in stats

class TestCodeExecutionTool:
    """Test cases for the Code Execution Tool."""
    
    @pytest.fixture
    def code_tool(self):
        """Create a code execution tool instance for testing."""
        return CodeExecutionTool()
    
    @pytest.mark.asyncio
    async def test_python_execution(self, code_tool):
        """Test Python code execution."""
        result = await code_tool.execute_python("print('Hello, World!')")
        
        assert result["status"] == "success"
        assert "result" in result
        assert result["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_javascript_execution(self, code_tool):
        """Test JavaScript code execution."""
        result = await code_tool.execute_javascript("console.log('Hello, World!');")
        
        assert result["status"] == "success"
        assert "result" in result
        assert result["language"] == "javascript"
    
    @pytest.mark.asyncio
    async def test_security_validation(self, code_tool):
        """Test security validation."""
        # Test forbidden import
        result = await code_tool.execute_python("import os")
        assert result["status"] == "error"
        assert "Security violation" in result["error"]
        
        # Test forbidden function
        result = await code_tool.execute_python("eval('1+1')")
        assert result["status"] == "error"
        assert "Security violation" in result["error"]
    
    @pytest.mark.asyncio
    async def test_code_generation(self, code_tool):
        """Test code generation from task description."""
        result = await code_tool.execute("Calculate 2 + 2", {"language": "python"})
        
        assert result["status"] == "success"
        assert "code_executed" in result

class TestFileOperationsTool:
    """Test cases for the File Operations Tool."""
    
    @pytest.fixture
    def file_tool(self):
        """Create a file operations tool instance for testing."""
        return FileOperationsTool()
    
    @pytest.mark.asyncio
    async def test_file_read(self, file_tool):
        """Test file reading."""
        # Create a test file
        test_content = "This is a test file"
        write_result = await file_tool.write_file("test_file.txt", test_content)
        assert write_result["status"] == "success"
        
        # Read the file
        read_result = await file_tool.read_file("test_file.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == test_content
    
    @pytest.mark.asyncio
    async def test_directory_listing(self, file_tool):
        """Test directory listing."""
        result = await file_tool.list_directory(".")
        
        assert result["status"] == "success"
        assert "files" in result
        assert "directories" in result
        assert "total_files" in result
        assert "total_directories" in result
    
    @pytest.mark.asyncio
    async def test_file_search(self, file_tool):
        """Test file search."""
        result = await file_tool.search_files("*.py", ".")
        
        assert result["status"] == "success"
        assert "matches" in result
        assert "total_matches" in result
    
    @pytest.mark.asyncio
    async def test_security_restrictions(self, file_tool):
        """Test security restrictions."""
        # Test forbidden path
        result = await file_tool.read_file("/etc/passwd")
        assert result["status"] == "error"
        assert "Path not allowed" in result["error"]
        
        # Test path traversal
        result = await file_tool.read_file("../../../etc/passwd")
        assert result["status"] == "error"
        assert "Path not allowed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_file_analysis(self, file_tool):
        """Test file analysis."""
        # Create a test file
        test_content = "This is a test file\nwith multiple lines\nof content"
        await file_tool.write_file("test_analysis.txt", test_content)
        
        # Analyze the file
        result = await file_tool.execute("", {"operation": "analyze", "file_path": "test_analysis.txt"})
        
        assert result["status"] == "success"
        assert "analysis" in result
        analysis = result["analysis"]
        assert analysis["line_count"] == 3
        assert analysis["word_count"] == 10
        assert analysis["character_count"] == len(test_content)
