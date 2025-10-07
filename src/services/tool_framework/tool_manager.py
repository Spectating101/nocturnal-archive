"""
Dynamic Tool Manager - Core tool selection and execution framework
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
import uuid

from .code_execution_tool import CodeExecutionTool
from .file_operations_tool import FileOperationsTool
from .web_search_tool import WebSearchTool
from .data_analysis_tool import DataAnalysisTool
from .api_calls_tool import APICallsTool

logger = logging.getLogger(__name__)

class ToolManager:
    """
    Dynamic tool manager with intelligent tool selection and execution capabilities.
    
    Features:
    - Dynamic tool selection based on task requirements
    - Tool execution with monitoring and error handling
    - Tool capability matching and optimization
    - Execution history and performance tracking
    - Tool composition and chaining
    """
    
    def __init__(self):
        # Initialize available tools
        self.tools = {
            "code_execution": CodeExecutionTool(),
            "file_operations": FileOperationsTool(),
            "web_search": WebSearchTool(),
            "data_analysis": DataAnalysisTool(),
            "api_calls": APICallsTool(),
            "llm_reasoning": self._create_llm_tool(),
            "llm_analysis": self._create_llm_tool(),
            "llm_validation": self._create_llm_tool(),
            "llm_synthesis": self._create_llm_tool()
        }
        
        # Tool capabilities mapping
        self.tool_capabilities = {
            "code_execution": ["python", "javascript", "bash", "sql", "data_processing"],
            "file_operations": ["read", "write", "list", "search", "analyze"],
            "web_search": ["search", "scrape", "extract", "research"],
            "data_analysis": ["analyze", "visualize", "statistics", "ml"],
            "api_calls": ["http", "rest", "graphql", "integration"],
            "llm_reasoning": ["reasoning", "analysis", "synthesis", "planning"],
            "llm_analysis": ["analysis", "evaluation", "assessment"],
            "llm_validation": ["validation", "verification", "checking"],
            "llm_synthesis": ["synthesis", "summarization", "integration"]
        }
        
        # Execution history
        self.execution_history: List[Dict] = []
        
        logger.info("Tool Manager initialized with {} tools".format(len(self.tools)))
    
    def _create_llm_tool(self):
        """Create a generic LLM tool for reasoning tasks."""
        class LLMTool:
            async def execute(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
                # This would integrate with the existing LLM service
                return {
                    "status": "completed",
                    "result": f"LLM processed: {task_description}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        return LLMTool()
    
    async def execute_tool(self, tool_name: str, task_description: str, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a specific tool with the given task.
        
        Args:
            tool_name: Name of the tool to execute
            task_description: Description of the task
            context: Additional context for execution
            
        Returns:
            Execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available")
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Executing tool '{tool_name}' with task: {task_description}")
            
            # Execute the tool
            tool = self.tools[tool_name]
            result = await tool.execute(task_description, context or {})
            
            # Record execution
            execution_record = {
                "execution_id": execution_id,
                "tool_name": tool_name,
                "task_description": task_description,
                "context": context,
                "start_time": start_time,
                "end_time": datetime.now(timezone.utc),
                "status": "success",
                "result": result,
                "error": None
            }
            
            self.execution_history.append(execution_record)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
            
            # Record failed execution
            execution_record = {
                "execution_id": execution_id,
                "tool_name": tool_name,
                "task_description": task_description,
                "context": context,
                "start_time": start_time,
                "end_time": datetime.now(timezone.utc),
                "status": "failed",
                "result": None,
                "error": str(e)
            }
            
            self.execution_history.append(execution_record)
            raise
    
    async def select_best_tool(self, task_description: str, 
                              context: Dict[str, Any] = None) -> str:
        """
        Select the best tool for a given task based on capabilities and context.
        
        Args:
            task_description: Description of the task
            context: Additional context
            
        Returns:
            Name of the best tool
        """
        # Simple tool selection based on keywords
        task_lower = task_description.lower()
        
        # File-related tasks (check first for directory operations)
        if any(keyword in task_lower for keyword in ["list", "directory", "folder", "ls", "dir"]):
            return "file_operations"
        
        # Code-related tasks
        if any(keyword in task_lower for keyword in ["code", "program", "script", "python", "javascript", "execute", "run"]):
            return "code_execution"
        
        # File operations (read, write, search files)
        if any(keyword in task_lower for keyword in ["file", "read", "write", "create", "delete"]):
            return "file_operations"
        
        # Search-related tasks
        if any(keyword in task_lower for keyword in ["search", "find", "lookup", "research", "web"]):
            return "web_search"
        
        # Data analysis tasks
        if any(keyword in task_lower for keyword in ["analyze", "data", "statistics", "visualize", "chart"]):
            return "data_analysis"
        
        # API-related tasks
        if any(keyword in task_lower for keyword in ["api", "request", "http", "call", "fetch"]):
            return "api_calls"
        
        # Default to LLM reasoning
        return "llm_reasoning"
    
    async def execute_with_auto_selection(self, task_description: str, 
                                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Automatically select and execute the best tool for a task.
        
        Args:
            task_description: Description of the task
            context: Additional context
            
        Returns:
            Execution result
        """
        tool_name = await self.select_best_tool(task_description, context)
        return await self.execute_tool(tool_name, task_description, context)
    
    def get_tool_capabilities(self, tool_name: str) -> List[str]:
        """Get capabilities of a specific tool."""
        return self.tool_capabilities.get(tool_name, [])
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tools.keys())
    
    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get recent execution history."""
        return self.execution_history[-limit:]
    
    def get_tool_performance_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get performance statistics for a specific tool."""
        tool_executions = [e for e in self.execution_history if e["tool_name"] == tool_name]
        
        if not tool_executions:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        successful = len([e for e in tool_executions if e["status"] == "success"])
        failed = len([e for e in tool_executions if e["status"] == "failed"])
        
        total_time = sum(
            (e["end_time"] - e["start_time"]).total_seconds() 
            for e in tool_executions
        )
        
        return {
            "total_executions": len(tool_executions),
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / len(tool_executions) if tool_executions else 0,
            "average_execution_time": total_time / len(tool_executions) if tool_executions else 0
        }
