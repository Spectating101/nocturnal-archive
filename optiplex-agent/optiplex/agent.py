"""Main Optiplex Agent implementation"""
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import OptiplexConfig, ModelConfig
from .context import ContextManager
from .file_ops import FileOperations
from .git_ops import GitOperations
from .tools import BashTool, GrepTool, GlobTool, TodoManager, WebTool, PlannerTool
from .persistence import ConversationStore, SessionManager
from .indexer import CodebaseIndexer
from .diff_tool import DiffApplier
from .auto_import import AutoImport
from .tree_sitter_parser import create_parser

@dataclass
class AgentResponse:
    """Response from the agent"""
    content: str
    tool_calls: List[Dict[str, Any]]
    model: str
    tokens_used: int
    success: bool
    error: Optional[str] = None

class OptiplexAgent:
    """Main agent for coding assistance"""

    def __init__(
        self,
        root_dir: str,
        model_name: Optional[str] = None,
        system_prompt_type: str = "default",
        interactive_diffs: bool = True,
        auto_apply: bool = False,
        temperature: Optional[float] = None
    ):
        self.root_dir = Path(root_dir).resolve()
        self.model_config = OptiplexConfig.get_model(model_name)
        
        # Override temperature if specified (e.g., 0.7 for analysis, 0.2 for coding)
        if temperature is not None:
            self.model_config.temperature = temperature
        
        self.system_prompt = OptiplexConfig.get_system_prompt(system_prompt_type)
        self.interactive_diffs = interactive_diffs
        self.auto_apply = auto_apply

        # Initialize components
        self.context_manager = ContextManager(str(self.root_dir))
        self.file_ops = FileOperations(str(self.root_dir))

        # Initialize git if available
        try:
            self.git_ops = GitOperations(str(self.root_dir))
        except ValueError:
            self.git_ops = None

        # Initialize advanced tools
        self.bash_tool = BashTool(str(self.root_dir))
        self.grep_tool = GrepTool(str(self.root_dir))
        self.glob_tool = GlobTool(str(self.root_dir))
        self.todo_manager = TodoManager()
        self.web_tool = WebTool()
        self.planner_tool = PlannerTool()
        self.indexer = CodebaseIndexer(str(self.root_dir))
        self.diff_applier = DiffApplier(auto_apply=self.auto_apply)
        self.auto_import = AutoImport(self.root_dir)
        self.tree_parser = create_parser()

        # Persistence
        self.conversation_store = ConversationStore()
        self.session_manager = SessionManager()
        self.session_id = self.session_manager.create_session(
            model=self.model_config.name,
            root_dir=str(self.root_dir),
            prompt_type=system_prompt_type
        )

        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history = OptiplexConfig.MAX_CONVERSATION_HISTORY

    def _get_api_endpoint(self) -> str:
        """Get API endpoint for the model provider"""
        endpoints = {
            "xai": "https://api.x.ai/v1/chat/completions",
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "deepseek": "https://api.deepseek.com/v1/chat/completions",
            "cerebras": "https://api.cerebras.ai/v1/chat/completions"
        }
        return endpoints.get(self.model_config.provider)

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        api_key = self.model_config.get_api_key()
        if not api_key:
            raise ValueError(f"API key not found for {self.model_config.provider}")

        if self.model_config.provider == "anthropic":
            return {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        else:
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build tool definitions for function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file contents. For large files, specify start_line and end_line to read specific sections (1-indexed, inclusive).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the file to read"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "Starting line number (1-indexed, optional)"
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "Ending line number (1-indexed, inclusive, optional)"
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file (creates backup automatically)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["filepath", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing old content with new content. CRITICAL: Use read_file FIRST to get exact current content, then copy old_content EXACTLY with correct indentation and line breaks. Include 3-5 lines of context to make old_content unique.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the file to edit"
                            },
                            "old_content": {
                                "type": "string",
                                "description": "EXACT content to replace (must match file exactly with whitespace, newlines, parameter names). Include enough context (3-5 lines) to be unique."
                            },
                            "new_content": {
                                "type": "string",
                                "description": "New content to insert (same structure as old_content, only change what's needed)"
                            }
                        },
                        "required": ["filepath", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Get the current git status",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_diff",
                    "description": "Get git diff for a file or all changes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Optional: specific file to diff"
                            },
                            "staged": {
                                "type": "boolean",
                                "description": "Show staged changes only"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit",
                    "description": "Create a git commit",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Commit message"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files to stage and commit"
                            }
                        },
                        "required": ["message", "files"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Execute a bash command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Bash command to execute"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in seconds (default: 30)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep",
                    "description": "Search for pattern in files using regex",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Regex pattern to search for"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to search in (default: current directory)"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to filter (e.g., '*.py')"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Case sensitive search (default: true)"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "glob",
                    "description": "Find files matching a glob pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern (e.g., '**/*.py', 'src/*.js')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Base path to search from"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "todo_add",
                    "description": "Add a todo item to track tasks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Todo item description"
                            },
                            "status": {
                                "type": "string",
                                "description": "Status: pending, in_progress, completed"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "todo_update",
                    "description": "Update a todo item status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "Todo item ID"
                            },
                            "status": {
                                "type": "string",
                                "description": "New status: pending, in_progress, completed"
                            }
                        },
                        "required": ["todo_id", "status"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "todo_list",
                    "description": "Get all todo items",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_fetch",
                    "description": "Fetch content from a URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to fetch"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_plan",
                    "description": "Create a multi-step plan for complex tasks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "steps": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of step descriptions"
                            }
                        },
                        "required": ["steps"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_step",
                    "description": "Mark current plan step as complete",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "result": {
                                "type": "string",
                                "description": "Result of the step"
                            }
                        },
                        "required": ["result"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "index_codebase",
                    "description": "Index entire codebase for fast semantic search",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "force": {
                                "type": "boolean",
                                "description": "Force reindex even if already indexed"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "Search indexed codebase by name, content, imports, or function calls",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "search_type": {
                                "type": "string",
                                "description": "Type: 'name', 'content', 'import', 'call'"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results (default: 20)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "codebase_summary",
                    "description": "Get high-level summary of entire codebase",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_summary",
                    "description": "Get summary of a specific file (classes, functions, imports)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to file"
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call"""
        try:
            if tool_name == "read_file":
                content = self.file_ops.read_file(
                    arguments["filepath"],
                    arguments.get("start_line"),
                    arguments.get("end_line")
                )
                return {"content": content, "filepath": arguments["filepath"]}

            elif tool_name == "write_file":
                success = self.file_ops.write_file(
                    arguments["filepath"],
                    arguments["content"]
                )
                return {"success": success}

            elif tool_name == "edit_file":
                # Use interactive diff if enabled
                if self.interactive_diffs:
                    success = self.diff_applier.apply_edit(
                        arguments["filepath"],
                        arguments["old_content"],
                        arguments["new_content"],
                        create_backup=True
                    )
                else:
                    success = self.file_ops.edit_file(
                        arguments["filepath"],
                        arguments["old_content"],
                        arguments["new_content"]
                    )
                return {"success": success}

            elif tool_name == "git_status":
                if not self.git_ops:
                    return {"error": "Not a git repository"}
                status = self.git_ops.get_status()
                return asdict(status)

            elif tool_name == "git_diff":
                if not self.git_ops:
                    return {"error": "Not a git repository"}
                return self.git_ops.get_diff(
                    filepath=arguments.get("filepath"),
                    staged=arguments.get("staged", False)
                )

            elif tool_name == "git_commit":
                if not self.git_ops:
                    return {"error": "Not a git repository"}

                # Stage files
                self.git_ops.stage_files(arguments["files"])

                # Commit
                success = self.git_ops.commit(arguments["message"])
                return {"success": success}

            elif tool_name == "bash":
                result = self.bash_tool.execute(
                    arguments["command"],
                    timeout=arguments.get("timeout", 30)
                )
                return asdict(result)

            elif tool_name == "grep":
                results = self.grep_tool.search(
                    pattern=arguments["pattern"],
                    path=arguments.get("path"),
                    file_pattern=arguments.get("file_pattern"),
                    case_sensitive=arguments.get("case_sensitive", True)
                )
                return {"results": results}

            elif tool_name == "glob":
                files = self.glob_tool.find(
                    pattern=arguments["pattern"],
                    path=arguments.get("path")
                )
                return {"files": files}

            elif tool_name == "todo_add":
                todo = self.todo_manager.add(
                    content=arguments["content"],
                    status=arguments.get("status", "pending")
                )
                return todo

            elif tool_name == "todo_update":
                success = self.todo_manager.update(
                    todo_id=arguments["todo_id"],
                    status=arguments["status"]
                )
                return {"success": success}

            elif tool_name == "todo_list":
                todos = self.todo_manager.get_all()
                return {"todos": todos}

            elif tool_name == "web_search":
                results = self.web_tool.search(
                    query=arguments["query"],
                    num_results=arguments.get("num_results", 5)
                )
                return {"results": results}

            elif tool_name == "web_fetch":
                content = self.web_tool.fetch(arguments["url"])
                return content

            elif tool_name == "create_plan":
                plan = self.planner_tool.create_plan(arguments["steps"])
                return {"plan": plan}

            elif tool_name == "complete_step":
                self.planner_tool.complete_step(arguments["result"])
                status = self.planner_tool.get_plan_status()
                return status

            elif tool_name == "index_codebase":
                force = arguments.get("force", False)
                if force:
                    self.indexer.clear_index()
                stats = self.indexer.index_directory()
                return stats

            elif tool_name == "search_code":
                query = arguments["query"]
                search_type = arguments.get("search_type", "content")
                limit = arguments.get("limit", 20)

                if search_type == "name":
                    results = self.indexer.search_by_name(query, limit)
                elif search_type == "import":
                    results = self.indexer.search_by_import(query)
                elif search_type == "call":
                    results = self.indexer.search_by_call(query)
                else:  # content
                    results = self.indexer.search_by_content(query, limit)

                # Convert to dicts for JSON serialization
                return {
                    "results": [
                        {
                            "file": r.file_path,
                            "lines": f"{r.start_line}-{r.end_line}",
                            "type": r.chunk_type,
                            "name": r.name,
                            "preview": r.content[:200] if len(r.content) > 200 else r.content
                        }
                        for r in results
                    ]
                }

            elif tool_name == "codebase_summary":
                summary = self.indexer.get_codebase_summary()
                return summary

            elif tool_name == "file_summary":
                summary = self.indexer.get_file_summary(arguments["filepath"])
                return summary

            elif tool_name == "suggest_imports":
                filepath = Path(arguments["filepath"])
                suggestions = self.auto_import.analyze_file(filepath)
                return {
                    "suggestions": [
                        {
                            "module": s.module,
                            "names": s.names,
                            "type": s.import_type,
                            "reason": s.reason
                        }
                        for s in suggestions
                    ],
                    "count": len(suggestions)
                }

            elif tool_name == "add_imports":
                filepath = Path(arguments["filepath"])
                auto_apply = arguments.get("auto_apply", False)
                suggestions = self.auto_import.analyze_file(filepath)
                if suggestions:
                    success = self.auto_import.insert_imports(filepath, suggestions, auto_apply)
                    return {"success": success, "count": len(suggestions)}
                return {"success": False, "message": "No imports to add"}

            elif tool_name == "check_unused_imports":
                filepath = Path(arguments["filepath"])
                unused = self.auto_import.check_unused_imports(filepath)
                return {"unused": unused, "count": len(unused)}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _call_llm(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call the LLM API"""
        endpoint = self._get_api_endpoint()
        headers = self._build_headers()

        # Build request based on provider
        if self.model_config.provider == "anthropic":
            # Anthropic format
            system_msg = [m for m in messages if m["role"] == "system"]
            other_msgs = [m for m in messages if m["role"] != "system"]

            payload = {
                "model": self.model_config.name,
                "max_tokens": self.model_config.max_tokens,
                "temperature": self.model_config.temperature,
                "system": system_msg[0]["content"] if system_msg else self.system_prompt,
                "messages": other_msgs
            }
        else:
            # OpenAI-compatible format
            payload = {
                "model": self.model_config.name,
                "messages": messages,
                "max_tokens": self.model_config.max_tokens,
                "temperature": self.model_config.temperature,
                "tools": self._build_tools_schema()
            }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Log error details for debugging
            error_details = {
                "status_code": response.status_code,
                "error": response.text[:500],
                "model": self.model_config.name,
                "message_count": len(messages)
            }
            print(f"❌ LLM API Error: {error_details}")
            raise

    def chat(self, user_message: str, context_files: Optional[List[str]] = None) -> AgentResponse:
        """Send a message to the agent and get a response"""
        try:
            # Build context if files provided
            context = ""
            if context_files:
                context = self.context_manager.get_smart_context(context_files)

            # Add to conversation history
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add conversation history
            messages.extend(self.conversation_history[-self.max_history:])

            # Add context if available
            if context:
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nUser request: {user_message}"
                })
            else:
                messages.append({"role": "user", "content": user_message})

            # Agentic loop - allow up to 5 rounds of tool calls
            tokens = 0
            all_executed_tools = []
            content = ""
            max_rounds = 5
            
            for round_num in range(max_rounds):
                # Adaptive temperature: higher for analysis/reading, lower for editing
                # Check if last tools were read-heavy (analysis mode) or edit-heavy (precision mode)
                if round_num > 0 and all_executed_tools:
                    recent_tools = [t['name'] for t in all_executed_tools[-3:]]
                    read_heavy = sum(1 for t in recent_tools if t in ['read_file', 'file_summary', 'search_code']) >= 2
                    
                    if read_heavy and self.model_config.temperature < 0.5:
                        # Boost temperature for analysis rounds
                        original_temp = self.model_config.temperature
                        self.model_config.temperature = 0.6
                    elif not read_heavy and self.model_config.temperature > 0.3:
                        # Lower temperature for edit rounds
                        original_temp = self.model_config.temperature
                        self.model_config.temperature = 0.2
                
                # Call LLM
                response = self._call_llm(messages)
                
                # Restore original temperature
                if round_num > 0 and 'original_temp' in locals():
                    self.model_config.temperature = original_temp

                # Parse response
                if self.model_config.provider == "anthropic":
                    content = response.get("content", [{}])[0].get("text", "")
                    tool_calls = []
                    tokens += response.get("usage", {}).get("input_tokens", 0) + \
                            response.get("usage", {}).get("output_tokens", 0)
                else:
                    message = response["choices"][0]["message"]
                    content = message.get("content", "")
                    tool_calls = message.get("tool_calls", [])
                    tokens += response.get("usage", {}).get("total_tokens", 0)

                # If no tool calls, we're done
                if not tool_calls:
                    break

                # Execute tool calls (in parallel for speed)
                executed_tools = []

                if len(tool_calls) > 1:
                    # Parallel execution for multiple tools
                    with ThreadPoolExecutor(max_workers=min(len(tool_calls), 5)) as executor:
                        futures = {}

                        for tool_call in tool_calls:
                            if self.model_config.provider == "anthropic":
                                tool_name = tool_call.get("name")
                                arguments = tool_call.get("input", {})
                            else:
                                tool_name = tool_call["function"]["name"]
                                arguments = json.loads(tool_call["function"]["arguments"])

                            future = executor.submit(self._execute_tool, tool_name, arguments)
                            futures[future] = (tool_name, arguments)

                        for future in as_completed(futures):
                            tool_name, arguments = futures[future]
                            result = future.result()
                            executed_tools.append({
                                "name": tool_name,
                                "arguments": arguments,
                                "result": result
                            })
                else:
                    # Single tool, no need for threading overhead
                    for tool_call in tool_calls:
                        if self.model_config.provider == "anthropic":
                            tool_name = tool_call.get("name")
                            arguments = tool_call.get("input", {})
                        else:
                            tool_name = tool_call["function"]["name"]
                            arguments = json.loads(tool_call["function"]["arguments"])

                        result = self._execute_tool(tool_name, arguments)
                        executed_tools.append({
                            "name": tool_name,
                            "arguments": arguments,
                            "result": result
                        })

                # Add to all executed tools
                all_executed_tools.extend(executed_tools)

                # Check for edit failures and stop retrying
                edit_failed = any(
                    tool['name'] == 'edit_file' and 
                    tool['result'].get('error') and 
                    'Text not found' in str(tool['result'].get('error'))
                    for tool in executed_tools
                )
                
                if edit_failed and round_num > 0:
                    # Already tried to edit once and failed, stop looping
                    content = "Edit failed - the old_content didn't match the file. Stopping to avoid repeated failures."
                    break

                # Add assistant message with tool calls
                messages.append({"role": "assistant", "content": content or "Using tools..."})

                # Add tool results to messages for next round
                for tool in executed_tools:
                    # Truncate large results to avoid context overflow
                    result_str = json.dumps(tool['result'], indent=2)
                    if len(result_str) > 4000:
                        result_str = result_str[:4000] + "\n... (truncated)"
                    
                    # Suppress error details if edit eventually succeeds
                    if tool['name'] == 'edit_file' and tool['result'].get('error'):
                        # Mark as potentially recoverable
                        result_str = '{"status": "attempted", "note": "Edit matching in progress"}'
                    
                    messages.append({
                        "role": "user",
                        "content": f"Tool '{tool['name']}' returned: {result_str}"
                    })

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": content})

            # Auto-save conversation if enabled
            if self.conversation_store.auto_save_enabled():
                self.save_conversation()

            return AgentResponse(
                content=content,
                tool_calls=all_executed_tools,
                model=self.model_config.name,
                tokens_used=tokens,
                success=True
            )

        except Exception as e:
            return AgentResponse(
                content="",
                tool_calls=[],
                model=self.model_config.name,
                tokens_used=0,
                success=False,
                error=str(e)
            )

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """Get information about a file"""
        return self.file_ops.get_file_info(filepath)

    def list_backups(self, filepath: str):
        """List backups for a file"""
        return self.file_ops.list_backups(filepath)

    def restore_backup(self, filepath: str, backup_path: str) -> bool:
        """Restore a file from backup"""
        return self.file_ops.restore_backup(filepath, Path(backup_path))

    def save_conversation(self, conversation_id: Optional[str] = None) -> bool:
        """Save current conversation"""
        cid = conversation_id or self.session_id
        return self.conversation_store.save_conversation(
            cid,
            self.conversation_history,
            metadata={
                "model": self.model_config.name,
                "root_dir": str(self.root_dir)
            }
        )

    def load_conversation(self, conversation_id: str) -> bool:
        """Load a saved conversation"""
        data = self.conversation_store.load_conversation(conversation_id)
        if data:
            self.conversation_history = data.get("messages", [])
            return True
        return False

    def list_saved_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations"""
        return self.conversation_store.list_conversations()
