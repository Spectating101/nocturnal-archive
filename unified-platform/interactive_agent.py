#!/usr/bin/env python3
"""
Interactive Agent - Makes the system work like me (Claude)
Adds conversation memory, multi-step reasoning, and tool integration
"""

import os
import json
import time
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from groq import Groq, RateLimitError, APIError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('interactive_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONVERSATION MEMORY SYSTEM
# =============================================================================

@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    user_input: str
    assistant_response: str
    timestamp: datetime
    tools_used: List[str] = None
    reasoning_steps: List[str] = None
    
    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.reasoning_steps is None:
            self.reasoning_steps = []

@dataclass
class ConversationSession:
    """Manages conversation history and context"""
    session_id: str
    user_id: str
    turns: List[ConversationTurn]
    current_task: Optional[str] = None
    task_context: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.turns is None:
            self.turns = []
        if self.task_context is None:
            self.task_context = {}
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_turn(self, user_input: str, assistant_response: str, 
                 tools_used: List[str] = None, reasoning_steps: List[str] = None):
        """Add a new turn to the conversation"""
        turn = ConversationTurn(
            user_input=user_input,
            assistant_response=assistant_response,
            timestamp=datetime.now(),
            tools_used=tools_used or [],
            reasoning_steps=reasoning_steps or []
        )
        self.turns.append(turn)
    
    def get_context(self, max_turns: int = 3) -> str:
        """Get conversation context for LLM - LIMITED to prevent token overflow"""
        if not self.turns:
            return ""
        
        recent_turns = self.turns[-max_turns:]
        context_parts = []
        
        for turn in recent_turns:
            # Truncate long responses to prevent context bloat
            user_input = turn.user_input[:200] if len(turn.user_input) > 200 else turn.user_input
            assistant_response = turn.assistant_response[:300] if len(turn.assistant_response) > 300 else turn.assistant_response
            
            context_parts.append(f"User: {user_input}")
            context_parts.append(f"Assistant: {assistant_response}")
            if turn.tools_used:
                context_parts.append(f"Tools used: {', '.join(turn.tools_used)}")
        
        return "\n".join(context_parts)
    
    def get_task_context(self) -> str:
        """Get current task context"""
        if not self.current_task:
            return ""
        
        context = f"Current task: {self.current_task}\n"
        if self.task_context:
            context += f"Task context: {json.dumps(self.task_context, indent=2)}\n"
        
        return context

class ConversationManager:
    """Manages all conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(hours=24)  # Sessions expire after 24 hours
    
    def get_or_create_session(self, user_id: str) -> ConversationSession:
        """Get existing session or create new one"""
        session_id = f"{user_id}_{int(time.time() // 3600)}"  # New session every hour
        
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                turns=[]
            )
        
        return self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.created_at > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

# =============================================================================
# TOOL INTEGRATION SYSTEM
# =============================================================================

@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0

class ToolManager:
    """Manages tool execution capabilities"""
    
    def __init__(self):
        self.tools = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_directory": self._list_directory,
            "run_command": self._run_command,
            "search_files": self._search_files,
            "get_file_info": self._get_file_info,
            "check_r_environment": self._check_r_environment,
            "execute_r_code": self._execute_r_code,
            "get_system_info": self._get_system_info
        }
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unknown tool: {tool_name}"
            )
        
        start_time = time.time()
        
        try:
            result = await self.tools[tool_name](params)
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {tool_name} failed: {e}")
            
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _read_file(self, params: Dict[str, Any]) -> str:
        """Read file contents with security guardrails"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("File path required")
        
        # SECURITY: Prevent path traversal and absolute paths
        import os
        from pathlib import Path
        
        # Resolve to absolute path and check it's within allowed directory
        abs_path = Path(file_path).resolve()
        allowed_dir = Path.cwd().resolve()  # Current working directory
        
        try:
            abs_path.relative_to(allowed_dir)
        except ValueError:
            raise ValueError(f"Access denied: Path outside allowed directory")
        
        # Additional security checks
        if ".." in file_path or file_path.startswith("/"):
            raise ValueError(f"Access denied: Invalid path format")
        
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _write_file(self, params: Dict[str, Any]) -> str:
        """Write content to file"""
        file_path = params.get("path")
        content = params.get("content", "")
        
        if not file_path:
            raise ValueError("File path required")
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"File written: {file_path}"
    
    async def _list_directory(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List directory contents"""
        dir_path = params.get("path", ".")
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        items = []
        for item in dir_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
        
        return items
    
    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run shell command"""
        command = params.get("command")
        if not command:
            raise ValueError("Command required")
        
        # Security check - prevent dangerous commands
        dangerous_commands = ["rm -rf", "sudo", "chmod 777", "dd if=", "mkfs"]
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            raise ValueError(f"Dangerous command blocked: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "command": command
            }
    
    async def _search_files(self, params: Dict[str, Any]) -> List[str]:
        """Search for files matching pattern"""
        pattern = params.get("pattern", "*")
        directory = params.get("directory", ".")
        
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        matching_files = []
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                matching_files.append(str(file_path))
        
        return matching_files
    
    async def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed file information"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("File path required")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "extension": file_path.suffix
        }
    
    async def _check_r_environment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check R environment and packages"""
        try:
            # Check if R is available
            result = subprocess.run(['R', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            r_available = result.returncode == 0
            
            info = {
                "r_available": r_available,
                "r_version": result.stdout.split('\n')[0] if r_available else None,
                "rstudio_available": 'RSTUDIO' in os.environ or 'RSTUDIO_PANDOC' in os.environ,
                "working_directory": str(Path.cwd())
            }
            
            if r_available:
                # Get installed packages
                try:
                    packages_result = subprocess.run([
                        'R', '--slave', '-e', 
                        'cat(paste(installed.packages()[,1], collapse=", "))'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if packages_result.returncode == 0:
                        info["installed_packages"] = packages_result.stdout.strip().split(", ")
                except:
                    info["installed_packages"] = []
            
            return info
            
        except Exception as e:
            return {
                "r_available": False,
                "error": str(e),
                "working_directory": str(Path.cwd())
            }
    
    async def _execute_r_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute R code and return results"""
        r_code = params.get("code")
        if not r_code:
            raise ValueError("R code required")
        
        try:
            # Create temporary R script
            temp_file = Path("/tmp/temp_r_script.R")
            with open(temp_file, 'w') as f:
                f.write(r_code)
            
            # Execute R script
            result = subprocess.run([
                'R', '--slave', '-f', str(temp_file)
            ], capture_output=True, text=True, timeout=30)
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            return {
                "returncode": result.returncode,
                "output": result.stdout,
                "errors": result.stderr,
                "code": r_code
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "output": "",
                "errors": "R code execution timed out after 30 seconds",
                "code": r_code
            }
    
    async def _get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": os.name,
            "current_directory": str(Path.cwd()),
            "environment_variables": {
                "USER": os.getenv("USER"),
                "HOME": os.getenv("HOME"),
                "PATH": os.getenv("PATH", "")[:200] + "..." if len(os.getenv("PATH", "")) > 200 else os.getenv("PATH", "")
            },
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# MULTI-STEP REASONING SYSTEM
# =============================================================================

@dataclass
class ReasoningStep:
    """Single step in multi-step reasoning"""
    step_number: int
    description: str
    action_type: str  # "think", "tool", "llm", "plan"
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None

class TaskPlanner:
    """Plans multi-step tasks and reasoning"""
    
    def __init__(self, groq_client: Groq, api_key_status):
        self.groq_client = groq_client
        self.api_key_status = api_key_status
    
    async def create_plan(self, question: str, context: str = "") -> List[ReasoningStep]:
        """Create a multi-step plan for solving the question"""
        
        # DETERMINISTIC FAST-PATH: Handle common filesystem commands without LLM
        question_lower = question.lower().strip()
        
        # File listing patterns
        if any(pattern in question_lower for pattern in ["list files", "show files", "what files", "ls", "directory contents"]):
            return [
                ReasoningStep(
                    step_number=1,
                    description="Get system information",
                    action_type="tool",
                    parameters={"tool_name": "get_system_info"}
                ),
                ReasoningStep(
                    step_number=2,
                    description="List directory contents",
                    action_type="tool",
                    parameters={"tool_name": "list_directory"}
                )
            ]
        
        # File reading patterns
        import re
        # Improved regex to handle "read the filename" patterns (preserve case)
        file_read_match = re.match(r'(open|read)\s+(?:the\s+)?([^\s]+(?:\.\w+)?)', question_lower)
        if file_read_match:
            # Extract the filename from the original question to preserve case
            original_match = re.match(r'(open|read)\s+(?:the\s+)?([^\s]+(?:\.\w+)?)', question, re.IGNORECASE)
            filename = original_match.group(2) if original_match else file_read_match.group(2)
            return [
                ReasoningStep(
                    step_number=1,
                    description=f"Read file: {filename}",
                    action_type="tool",
                    parameters={"tool_name": "read_file", "params": {"path": filename}}
                )
            ]
        
        # R/SQL programming questions - use direct LLM response (check before search)
        if any(pattern in question_lower for pattern in ["how do i", "create", "histogram", "plot", "ggplot", "r code", "sql query", "data frame", "vector", "matrix", "write a sql", "sql query"]):
            return [
                ReasoningStep(
                    step_number=1,
                    description="Provide programming assistance",
                    action_type="llm",
                    parameters={"question": question, "context": context}
                )
            ]
        
        # Search patterns
        if any(pattern in question_lower for pattern in ["search", "find", "locate"]):
            return [
                ReasoningStep(
                    step_number=1,
                    description="Search for files",
                    action_type="tool",
                    parameters={"tool_name": "search_files", "pattern": question}
                )
            ]
        
        planning_prompt = f"""Create a step-by-step plan for this question: {question}

Available tools: read_file, write_file, list_directory, run_command, search_files, get_file_info, check_r_environment, execute_r_code, get_system_info

Respond ONLY with valid JSON array. No explanations, no markdown, just JSON:

[{{"step_number": 1, "description": "Analyze question", "action_type": "think", "parameters": {{"analysis": "What user needs"}}}}, {{"step_number": 2, "description": "Provide answer", "action_type": "llm", "parameters": {{"question": "{question}"}}}}]"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates step-by-step plans. Respond with valid JSON only."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # HARDENED JSON EXTRACTION: Multiple strategies for robust parsing
            import re
            
            # Log raw output for debugging
            print(f"DEBUG: Raw LLM output (first 400 chars): {content[:400]}")
            
            # Strategy 1: Try strict JSON array extraction
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group()
                    steps_data = json.loads(json_str)
                    
                    # Validate schema and create steps
                    steps = []
                    for i, step_data in enumerate(steps_data):
                        if isinstance(step_data, dict) and "action_type" in step_data:
                            steps.append(ReasoningStep(
                                step_number=step_data.get("step_number", i+1),
                                description=step_data.get("description", f"Step {i+1}"),
                                action_type=step_data["action_type"],
                                parameters=step_data.get("parameters", {})
                            ))
                    
                    if steps:  # Only return if we got valid steps
                        return steps
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON parsing failed: {e}")
            
            # Strategy 2: Try first complete JSON object
            json_obj_match = re.search(r'\{.*?\}', content, re.DOTALL)
            if json_obj_match:
                try:
                    json_str = json_obj_match.group()
                    obj_data = json.loads(json_str)
                    if isinstance(obj_data, list):
                        # Convert single object to list
                        obj_data = [obj_data]
                    
                    steps = []
                    for i, step_data in enumerate(obj_data):
                        if isinstance(step_data, dict) and "action_type" in step_data:
                            steps.append(ReasoningStep(
                                step_number=step_data.get("step_number", i+1),
                                description=step_data.get("description", f"Step {i+1}"),
                                action_type=step_data["action_type"],
                                parameters=step_data.get("parameters", {})
                            ))
                    
                    if steps:
                        return steps
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Object JSON parsing failed: {e}")
            
            # Strategy 3: Fallback to simple plan
            print("DEBUG: All JSON parsing failed, using fallback plan")
            return [
                ReasoningStep(
                    step_number=1,
                    description="Analyze the question",
                    action_type="think",
                    parameters={"analysis": "Understanding what the user needs"}
                ),
                    ReasoningStep(
                        step_number=2,
                        description="Provide direct answer",
                        action_type="llm",
                        parameters={"question": question, "context": context}
                    )
                ]
                
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Fallback plan
            return [
                ReasoningStep(
                    step_number=1,
                    description="Provide direct answer",
                    action_type="llm",
                    parameters={"question": question, "context": context}
                )
            ]

# =============================================================================
# INTERACTIVE AGENT CORE
# =============================================================================

class InteractiveAgent:
    """Main interactive agent that works like me"""
    
    def __init__(self, groq_client: Groq, api_key_status):
        self.groq_client = groq_client
        self.api_key_status = api_key_status
        self.conversation_manager = ConversationManager()
        self.tool_manager = ToolManager()
        self.task_planner = TaskPlanner(groq_client, api_key_status)
    
    async def process_question(self, question: str, user_id: str = "default") -> Dict[str, Any]:
        """Process a question with full interactive capabilities"""
        
        # Get or create conversation session
        session = self.conversation_manager.get_or_create_session(user_id)
        
        # Get conversation context
        conversation_context = session.get_context()
        task_context = session.get_task_context()
        
        # Create multi-step plan
        logger.info(f"Creating plan for question: {question}")
        plan = await self.task_planner.create_plan(question, conversation_context)
        
        # Execute the plan
        results = []
        tools_used = []
        reasoning_steps = []
        
        for step in plan:
            logger.info(f"Executing step {step.step_number}: {step.description}")
            
            try:
                if step.action_type == "think":
                    # Thinking step - just record it
                    step.result = "Thinking: " + step.description
                    step.success = True
                    reasoning_steps.append(step.description)
                
                elif step.action_type == "tool":
                    # Tool execution step
                    tool_name = step.parameters.get("tool_name")
                    tool_params = step.parameters.get("params", {})
                    
                    if tool_name:
                        tool_result = await self.tool_manager.execute_tool(tool_name, tool_params)
                        step.result = tool_result.data if tool_result.success else tool_result.error
                        step.success = tool_result.success
                        step.error = tool_result.error
                        
                        if tool_result.success:
                            tools_used.append(tool_name)
                            reasoning_steps.append(f"Used {tool_name}: {step.description}")
                        else:
                            reasoning_steps.append(f"Failed to use {tool_name}: {step.error}")
                
                elif step.action_type == "llm":
                    # LLM reasoning step
                    llm_question = step.parameters.get("question", question)
                    llm_context = step.parameters.get("context", conversation_context)
                    
                    # Combine all context
                    full_context = f"{conversation_context}\n{task_context}\n{llm_context}"
                    
                    # TOKEN METERING: Track input tokens
                    input_tokens = len(full_context.split()) + len(llm_question.split())  # Rough estimate
                    
                    response = self.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {
                                "role": "system",
                                "content": """You are a helpful assistant for R and SQL programming. 
                                Provide clear, concise answers with code examples when appropriate.
                                Focus on practical solutions and best practices.
                                If asked about R, provide R code examples.
                                If asked about SQL, provide SQL examples.
                                Always explain what the code does.
                                
                                You have access to tools and can execute multi-step reasoning.
                                Use the conversation context to provide relevant answers."""
                            },
                            {
                                "role": "user",
                                "content": f"Context:\n{full_context}\n\nQuestion: {llm_question}"
                            }
                        ],
                        temperature=0.1,
                        max_tokens=1500
                    )
                    
                    result = response.choices[0].message.content
                    output_tokens = len(result.split())  # Rough estimate
                    
                    # Log token usage
                    logger.info(f"Token usage - Input: ~{input_tokens}, Output: ~{output_tokens}, Total: ~{input_tokens + output_tokens}")
                    
                    step.result = result
                    step.success = True
                    reasoning_steps.append(f"LLM reasoning: {step.description}")
                
                else:
                    # Unknown action type
                    step.result = f"Unknown action type: {step.action_type}"
                    step.success = False
                    step.error = f"Unknown action type: {step.action_type}"
                
                results.append(step)
                
            except Exception as e:
                logger.error(f"Step {step.step_number} failed: {e}")
                step.result = None
                step.success = False
                step.error = str(e)
                results.append(step)
        
        # Compile final response
        final_response = await self._compile_response(question, results, conversation_context)
        
        # Add to conversation history
        session.add_turn(question, final_response, tools_used, reasoning_steps)
        
        return {
            "response": final_response,
            "tools_used": tools_used,
            "reasoning_steps": reasoning_steps,
            "plan_executed": len(results),
            "successful_steps": sum(1 for r in results if r.success),
            "session_id": session.session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _compile_response(self, question: str, results: List[ReasoningStep], context: str) -> str:
        """Compile final response from all reasoning steps"""
        
        # Get the main LLM response
        llm_responses = [r.result for r in results if r.action_type == "llm" and r.success]
        tool_results = [r.result for r in results if r.action_type == "tool" and r.success]
        tool_errors = [{"error": r.error} for r in results if r.action_type == "tool" and not r.success]
        
        if llm_responses:
            main_response = llm_responses[-1]  # Use the last LLM response
        elif tool_results or tool_errors:
            # Create response from tool results (including errors)
            all_tool_data = tool_results + tool_errors
            main_response = self._format_tool_results(question, all_tool_data)
        else:
            main_response = "I apologize, but I wasn't able to process your question properly."
        
        # Add tool results if any
        if tool_results:
            tool_info = "\n\n📊 Additional Information:\n"
            for i, result in enumerate(tool_results, 1):
                if isinstance(result, dict):
                    tool_info += f"{i}. {json.dumps(result, indent=2)}\n"
                else:
                    tool_info += f"{i}. {result}\n"
            main_response += tool_info
        
        return main_response
    
    def _format_tool_results(self, question: str, tool_results: List[Any]) -> str:
        """Format tool results into a proper response"""
        
        # Check for security errors first
        for result in tool_results:
            if isinstance(result, dict) and "error" in result:
                error_msg = result["error"]
                if "Access denied" in error_msg:
                    return f"❌ Security Error: {error_msg}\n\nFor security reasons, I can only access files within the current working directory."
                elif "File not found" in error_msg:
                    return f"❌ File Error: {error_msg}\n\nPlease check the filename and try again."
        
        # Analyze the question to determine what kind of response to give
        question_lower = question.lower()
        
        if "files" in question_lower and "directory" in question_lower:
            # File listing question
            for result in tool_results:
                if isinstance(result, list) and len(result) > 0:
                    # Extract file names from the directory listing
                    files = []
                    for item in result:
                        if isinstance(item, dict) and 'name' in item:
                            files.append(item['name'])
                    
                    if files:
                        response = f"Here are the files in the current directory:\n\n"
                        for file in files[:20]:  # Limit to first 20 files
                            response += f"• {file}\n"
                        if len(files) > 20:
                            response += f"\n... and {len(files) - 20} more files"
                        return response
        
        elif "read" in question_lower and ("file" in question_lower or "readme" in question_lower):
            # File reading question
            for result in tool_results:
                if isinstance(result, str) and len(result) > 100:
                    return f"Here's the content of the file:\n\n{result[:1000]}..."
        
        elif "system" in question_lower or "environment" in question_lower:
            # System information question
            for result in tool_results:
                if isinstance(result, dict):
                    response = "Here's the system information:\n\n"
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) < 100:
                            response += f"• {key}: {value}\n"
                        else:
                            response += f"• {key}: {type(value).__name__}\n"
                    return response
        
        # Generic response for other tool results
        if tool_results:
            response = "I've gathered the following information:\n\n"
            for i, result in enumerate(tool_results, 1):
                if isinstance(result, (list, dict)):
                    response += f"Result {i}: {type(result).__name__} with {len(result) if hasattr(result, '__len__') else 'unknown'} items\n"
                else:
                    response += f"Result {i}: {str(result)[:200]}...\n"
            return response
        
        return "I've processed your request and gathered some information."

# =============================================================================
# FASTAPI INTEGRATION
# =============================================================================

# Import the existing API key manager from integrated_server.py
import sys
sys.path.append('/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive/unified-platform')

# Create a simple API key manager for this module
class SimpleAPIKeyManager:
    def __init__(self):
        self.api_keys = []
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment"""
        for i in range(1, 4):
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key and key.strip():
                self.api_keys.append({
                    "key_id": f"key_{i}",
                    "api_key": key.strip()
                })
    
    def get_available_key(self):
        """Get first available key"""
        return self.api_keys[0] if self.api_keys else None

# Global instances
api_manager = SimpleAPIKeyManager()
interactive_agent = None

def initialize_interactive_agent():
    """Initialize the interactive agent"""
    global interactive_agent
    
    key_status = api_manager.get_available_key()
    if not key_status:
        raise ValueError("No API keys available")
    
    groq_client = Groq(api_key=key_status["api_key"])
    interactive_agent = InteractiveAgent(groq_client, key_status)
    
    logger.info("Interactive agent initialized successfully")

# Request models
class InteractiveRequest(BaseModel):
    question: str
    user_id: Optional[str] = "default"

class InteractiveResponse(BaseModel):
    response: str
    tools_used: List[str]
    reasoning_steps: List[str]
    plan_executed: int
    successful_steps: int
    session_id: str
    timestamp: str

# FastAPI app
app = FastAPI(
    title="Interactive Agent",
    description="Interactive AI agent that works like Claude with conversation memory and tool integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the interactive agent on startup"""
    try:
        initialize_interactive_agent()
        logger.info("Interactive agent server started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize interactive agent: {e}")

@app.post("/interactive/chat", response_model=InteractiveResponse)
async def interactive_chat(request: InteractiveRequest):
    """Interactive chat endpoint that works like me"""
    
    if not interactive_agent:
        raise HTTPException(status_code=500, detail="Interactive agent not initialized")
    
    try:
        result = await interactive_agent.process_question(
            question=request.question,
            user_id=request.user_id
        )
        
        return InteractiveResponse(**result)
        
    except Exception as e:
        logger.error(f"Interactive chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/interactive/status")
async def interactive_status():
    """Get interactive agent status"""
    return {
        "status": "healthy" if interactive_agent else "unhealthy",
        "agent_initialized": interactive_agent is not None,
        "api_keys_loaded": len(api_manager.api_keys),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Interactive Agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8001"))  # Different port to avoid conflicts
    
    logger.info(f"Starting Interactive Agent on {host}:{port}")
    
    uvicorn.run(
        "interactive_agent:app",
        host=host,
        port=port,
        workers=1,
        log_level="info",
        reload=False
    )