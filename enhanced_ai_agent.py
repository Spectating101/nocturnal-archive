#!/usr/bin/env python3
"""
Enhanced Nocturnal AI Agent - Production-Ready Research Assistant
Integrates with Archive API and FinSight API for comprehensive research capabilities
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

# Suppress noise
logging.basicConfig(level=logging.ERROR)

try:
    from groq import Groq
except ImportError:
    print("❌ Install groq: pip install groq")
    exit(1)

@dataclass
class ChatRequest:
    question: str
    user_id: str = "default"
    conversation_id: str = "default"
    context: Dict[str, Any] = None

@dataclass
class ChatResponse:
    response: str
    tools_used: List[str] = None
    reasoning_steps: List[str] = None
    model: str = "enhanced-nocturnal-agent"
    timestamp: str = None
    tokens_used: int = 0
    confidence_score: float = 0.0
    execution_results: Dict[str, Any] = None
    api_results: Dict[str, Any] = None

class EnhancedNocturnalAgent:
    """
    Enhanced AI Agent with full API integration:
    - Archive API for academic research
    - FinSight API for financial data
    - Shell access for system operations
    - Memory system for context retention
    """
    
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.shell_session = None
        self.memory = {}
        self.daily_token_usage = 0
        self.daily_limit = 100000
        self.total_cost = 0.0
        self.cost_per_1k_tokens = 0.0001  # Groq pricing estimate
        
        # API clients
        self.archive_client = None
        self.finsight_client = None
        self.session = None
        self.company_name_to_ticker = {}
        
        # Initialize API clients
        self._init_api_clients()
        self._load_ticker_map()

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics and cost information"""
        return {
            "daily_tokens_used": self.daily_token_usage,
            "daily_token_limit": self.daily_limit,
            "remaining_tokens": self.daily_limit - self.daily_token_usage,
            "usage_percentage": (self.daily_token_usage / self.daily_limit) * 100,
            "total_cost": self.total_cost,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "estimated_monthly_cost": self.total_cost * 30  # Rough estimate
        }
    
    async def close(self):
        """Cleanly close resources (HTTP session and shell)."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception:
            pass
        try:
            if self.shell_session:
                self.shell_session.terminate()
        except Exception:
            pass
        
    def _init_api_clients(self):
        """Initialize API clients for Archive and FinSight"""
        try:
            # Archive API client
            self.archive_base_url = "http://127.0.0.1:8000/api"
            
            # FinSight API client  
            self.finsight_base_url = "http://127.0.0.1:8000/v1/finance"
            
            print("✅ API clients initialized")
            
        except Exception as e:
            print(f"⚠️ API client initialization warning: {e}")

    def _load_ticker_map(self):
        """Load a simple company name -> ticker map for FinSight lookups."""
        try:
            data_path = Path("nocturnal-archive-api/data/company_tickers.json")
            if not data_path.exists():
                data_path = Path("./data/company_tickers.json")
            if data_path.exists():
                import json as _json
                raw = _json.loads(data_path.read_text())
                # Expecting list of {"symbol": "AAPL", "name": "Apple Inc"}
                mapping = {}
                for item in raw:
                    name = str(item.get("name", "")).lower()
                    symbol = item.get("symbol")
                    if name and symbol:
                        mapping[name] = symbol
                        # Add a simplified short name variant
                        short = name.replace("inc.", "").replace("inc", "").replace("corporation", "").replace("corp.", "").strip()
                        mapping.setdefault(short, symbol)
                # Common aliases
                mapping.setdefault("apple", "AAPL")
                mapping.setdefault("microsoft", "MSFT")
                mapping.setdefault("alphabet", "GOOGL")
                mapping.setdefault("google", "GOOGL")
                mapping.setdefault("amazon", "AMZN")
                self.company_name_to_ticker = mapping
        except Exception:
            self.company_name_to_ticker = {}

    def _extract_tickers_from_text(self, text: str) -> List[str]:
        """Find tickers either as explicit symbols or from known company names."""
        text_lower = text.lower()
        # Explicit ticker-like symbols
        ticker_candidates: List[str] = []
        for token in re.findall(r"\b[A-Z]{1,5}\b", text):
            ticker_candidates.append(token)
        # Company name matches
        for name, sym in self.company_name_to_ticker.items():
            if name and name in text_lower:
                ticker_candidates.append(sym)
        # Deduplicate preserve order
        seen = set()
        ordered: List[str] = []
        for t in ticker_candidates:
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ordered[:4]
    
    async def initialize(self):
        """Initialize the agent with API keys and shell session"""
        # Try multiple API keys for better rate limits
        api_keys = [
            os.getenv('GROQ_API_KEY'),
            os.getenv('GROQ_API_KEY_2'),
            os.getenv('GROQ_API_KEY_3')
        ]
        
        for i, api_key in enumerate(api_keys):
            if api_key:
                try:
                    self.client = Groq(api_key=api_key)
                    print(f"✅ Enhanced Nocturnal Agent Ready! (Using API key {i+1})")
                    
                    # Initialize persistent shell session
                    self.shell_session = subprocess.Popen(['bash'], 
                                                        stdin=subprocess.PIPE, 
                                                        stdout=subprocess.PIPE, 
                                                        stderr=subprocess.STDOUT,
                                                        text=True,
                                                        cwd=os.getcwd())
                    
                    # Initialize HTTP session
                    self.session = aiohttp.ClientSession()
                    
                    return True
                except Exception as e:
                    print(f"❌ API key {i+1} failed: {e}")
                    continue
        
        print("❌ No valid API keys found!")
        return False
    
    async def _call_archive_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Archive API endpoint"""
        try:
            if not self.session:
                return {"error": "HTTP session not initialized"}
            
            url = f"{self.archive_base_url}/{endpoint}"
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Archive API error: {response.status}"}
                    
        except Exception as e:
            return {"error": f"Archive API call failed: {e}"}
    
    async def _call_finsight_api(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call FinSight API endpoint"""
        try:
            if not self.session:
                return {"error": "HTTP session not initialized"}
            
            url = f"{self.finsight_base_url}/{endpoint}"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"FinSight API error: {response.status}"}
                    
        except Exception as e:
            return {"error": f"FinSight API call failed: {e}"}
    
    async def search_academic_papers(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search academic papers using Archive API"""
        data = {
            "query": query,
            "limit": limit,
            "sources": ["openalex", "pubmed"]
        }
        return await self._call_archive_api("search", data)
    
    async def synthesize_research(self, paper_ids: List[str], max_words: int = 500) -> Dict[str, Any]:
        """Synthesize research papers using Archive API"""
        data = {
            "paper_ids": paper_ids,
            "max_words": max_words,
            "focus": "key_findings",
            "style": "academic"
        }
        return await self._call_archive_api("synthesize", data)
    
    async def get_financial_data(self, ticker: str, metric: str, limit: int = 12) -> Dict[str, Any]:
        """Get financial data using FinSight API"""
        params = {
            "freq": "Q",
            "limit": limit
        }
        return await self._call_finsight_api(f"kpis/{ticker}/{metric}", params)
    
    async def get_financial_calculation(self, ticker: str, expression: str) -> Dict[str, Any]:
        """Get financial calculation using FinSight API"""
        data = {
            "ticker": ticker,
            "expr": expression,
            "period": "2024-Q4",
            "freq": "Q"
        }
        return await self._call_archive_api("calc/explain", data)
    
    def execute_command(self, command: str) -> str:
        """Execute command in persistent shell session and return output"""
        try:
            if self.shell_session is None:
                return "ERROR: Shell session not initialized"
            
            # Send command to persistent shell
            self.shell_session.stdin.write(command + '\n')
            self.shell_session.stdin.flush()
            
            # Read output with timeout
            import select
            
            output_lines = []
            start_time = time.time()
            timeout = 10  # seconds
            
            while time.time() - start_time < timeout:
                if select.select([self.shell_session.stdout], [], [], 0.1)[0]:
                    line = self.shell_session.stdout.readline()
                    if line:
                        output_lines.append(line.rstrip())
                    else:
                        break
                else:
                    # No more output available
                    break
            
            output = '\n'.join(output_lines)
            return output if output else "Command executed successfully"
            
        except Exception as e:
            return f"ERROR: {e}"
    
    def _check_token_budget(self, estimated_tokens: int) -> bool:
        """Check if we have enough token budget"""
        return (self.daily_token_usage + estimated_tokens) < self.daily_limit
    
    def _charge_tokens(self, tokens: int):
        """Charge tokens to daily usage"""
        self.daily_token_usage += tokens
    
    def _get_memory_context(self, user_id: str, conversation_id: str) -> str:
        """Get relevant memory context for the conversation"""
        if user_id not in self.memory:
            self.memory[user_id] = {}
        
        if conversation_id not in self.memory[user_id]:
            self.memory[user_id][conversation_id] = []
        
        # Get last 3 interactions for context
        recent_memory = self.memory[user_id][conversation_id][-3:]
        if not recent_memory:
            return ""
        
        context = "Recent conversation context:\n"
        for mem in recent_memory:
            context += f"- {mem}\n"
        return context
    
    def _update_memory(self, user_id: str, conversation_id: str, interaction: str):
        """Update memory with new interaction"""
        if user_id not in self.memory:
            self.memory[user_id] = {}
        
        if conversation_id not in self.memory[user_id]:
            self.memory[user_id][conversation_id] = []
        
        self.memory[user_id][conversation_id].append(interaction)
        
        # Keep only last 10 interactions
        if len(self.memory[user_id][conversation_id]) > 10:
            self.memory[user_id][conversation_id] = self.memory[user_id][conversation_id][-10:]
    
    async def _analyze_request_type(self, question: str) -> Dict[str, Any]:
        """Analyze what type of request this is and what APIs to use"""
        
        # Financial indicators
        financial_keywords = [
            'financial', 'revenue', 'profit', 'earnings', 'stock', 'market',
            'ticker', 'company', 'balance sheet', 'income statement', 'cash flow',
            'valuation', 'pe ratio', 'debt', 'equity', 'dividend', 'growth'
        ]
        
        # Research indicators
        research_keywords = [
            'research', 'paper', 'study', 'academic', 'literature', 'journal',
            'synthesis', 'findings', 'methodology', 'abstract', 'citation',
            'author', 'publication', 'peer review', 'scientific'
        ]
        
        # System/technical indicators
        system_keywords = [
            'file', 'directory', 'command', 'run', 'execute', 'install',
            'python', 'code', 'script', 'program', 'system', 'terminal'
        ]
        
        question_lower = question.lower()
        
        # Determine request type
        request_type = "general"
        apis_to_use = []
        
        if any(keyword in question_lower for keyword in financial_keywords):
            request_type = "financial"
            apis_to_use.append("finsight")
        
        if any(keyword in question_lower for keyword in research_keywords):
            request_type = "research"
            apis_to_use.append("archive")
        
        if any(keyword in question_lower for keyword in system_keywords):
            request_type = "system"
            apis_to_use.append("shell")
        
        # If multiple types detected, prioritize
        if len(apis_to_use) > 1:
            if "financial" in request_type and "research" in request_type:
                request_type = "comprehensive"  # Both financial and research
        
        return {
            "type": request_type,
            "apis": apis_to_use,
            "confidence": 0.8 if apis_to_use else 0.5
        }
    
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """Process request with full AI capabilities and API integration"""
        try:
            if not self.client:
                return ChatResponse(
                    response="❌ AI response not available (no Groq API key)",
                    timestamp=datetime.now().isoformat()
                )
            
            # Analyze request type
            request_analysis = await self._analyze_request_type(request.question)
            
            # Get memory context
            memory_context = self._get_memory_context(request.user_id, request.conversation_id)
            
            # Call appropriate APIs based on request type
            api_results = {}
            tools_used = []

            # Auto file-reading: detect filenames in the prompt and attach previews
            def _extract_filenames(text: str) -> List[str]:
                # Match common file patterns (no spaces) and simple quoted paths
                patterns = [
                    r"[\w\-./]+\.(?:py|md|txt|json|csv|yml|yaml|toml|ini|ts|tsx|js|ipynb)",
                    r"(?:\./|/)?[\w\-./]+/"  # directories
                ]
                matches: List[str] = []
                for pat in patterns:
                    matches.extend(re.findall(pat, text))
                # Deduplicate and keep reasonable length
                uniq = []
                for m in matches:
                    if len(m) <= 256 and m not in uniq:
                        uniq.append(m)
                return uniq[:5]

            def _safe_preview_file(path_str: str) -> Optional[Dict[str, Any]]:
                try:
                    p = Path(path_str)
                    if not p.exists():
                        return None
                    if p.is_dir():
                        # list first few entries
                        entries = sorted([e.name for e in p.iterdir()][:10])
                        return {"path": str(p), "type": "dir", "preview": "\n".join(entries)}
                    # For binary or huge files, skip
                    if p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".parquet", ".zip"}:
                        return {"path": str(p), "type": "binary", "preview": "(binary file preview skipped)"}
                    # Read first 60 lines max 32KB
                    content = p.read_text(errors="ignore")
                    head = "\n".join(content.splitlines()[:60])
                    if len(head) > 32768:
                        head = head[:32768]
                    return {"path": str(p), "type": "text", "preview": head}
                except Exception as e:
                    return {"path": path_str, "type": "error", "preview": f"error: {e}"}

            mentioned = _extract_filenames(request.question)
            file_previews: List[Dict[str, Any]] = []
            files_forbidden: List[str] = []
            base_dir = Path.cwd().resolve()
            sensitive_roots = {Path('/etc'), Path('/proc'), Path('/sys'), Path('/dev'), Path('/root'), Path('/usr'), Path('/bin'), Path('/sbin'), Path('/var')}
            def _is_safe_path(path_str: str) -> bool:
                try:
                    rp = Path(path_str).resolve()
                    if any(str(rp).startswith(str(sr)) for sr in sensitive_roots):
                        return False
                    return str(rp).startswith(str(base_dir))
                except Exception:
                    return False
            for m in mentioned:
                if not _is_safe_path(m):
                    files_forbidden.append(m)
                    continue
                pr = _safe_preview_file(m)
                if pr:
                    file_previews.append(pr)
            if file_previews:
                api_results["files"] = file_previews
                # Build grounded context from first text preview
                text_previews = [fp for fp in file_previews if fp.get("type") == "text" and fp.get("preview")]
                files_context = ""
                if text_previews:
                    fp = text_previews[0]
                    quoted = "\n".join(fp["preview"].splitlines()[:20])
                    files_context = f"File: {fp['path']} (first lines)\n" + quoted
                api_results["files_context"] = files_context
            elif mentioned:
                # Mentioned files but none found
                api_results["files_missing"] = mentioned
            if files_forbidden:
                api_results["files_forbidden"] = files_forbidden
            
            if "finsight" in request_analysis["apis"]:
                # Extract tickers from symbols or company names
                tickers = self._extract_tickers_from_text(request.question)
                financial_payload = {}
                if not tickers:
                    # Heuristic defaults for common requests
                    if "apple" in request.question.lower():
                        tickers = ["AAPL"]
                    if "microsoft" in request.question.lower():
                        tickers = tickers + ["MSFT"] if "AAPL" in tickers else ["MSFT"]
                # Fetch revenue for each ticker requested (cap 2)
                for t in tickers[:2]:
                    financial_payload[t] = await self.get_financial_data(t, "revenue")
                if financial_payload:
                    api_results["financial"] = financial_payload
                    tools_used.append("finsight_api")
            
            if "archive" in request_analysis["apis"]:
                # Extract research query
                api_results["research"] = await self.search_academic_papers(request.question, 5)
                tools_used.append("archive_api")
            
            # Build enhanced system prompt
            system_prompt = f"""You are the Enhanced Nocturnal AI Agent, a sophisticated research assistant with access to:

CAPABILITIES:
- Academic Research API (Archive) - Search and synthesize academic papers
- Financial Data API (FinSight) - Get SEC-regulator financial data with citations
- System Operations - Execute terminal commands with persistent state
- Memory System - Remember conversation context and user preferences

REQUEST ANALYSIS:
- Type: {request_analysis['type']}
- APIs to use: {request_analysis['apis']}
- Confidence: {request_analysis['confidence']}

{memory_context}

API RESULTS AVAILABLE:
{json.dumps(api_results, indent=2) if api_results else "No API results"}

IMPORTANT RULES:
- Be direct and concise - NO <think> tags or internal reasoning
- Use API results when available to provide accurate, cited information
- Only suggest terminal commands in backticks when users ask about files/directories/system info
- You have a PERSISTENT shell session - directory changes persist between interactions
- When commands are executed, you receive real results - use them for accurate analysis
- Cite sources when using API data (e.g., "According to SEC filings..." or "Research shows...")
- If file previews are provided, quote 3-6 lines to ground your answer and reference the file path.

INTERACTION STYLE:
- Normal conversation first, tools only when needed
- Give helpful, direct responses without verbose explanations
- Focus on being useful, not showing your reasoning process
- Use API data to provide authoritative, cited responses

You have real system access and API integration. Be smart and efficient."""
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            # If we have file context, inject it as an additional grounding message
            fc = api_results.get("files_context")
            if fc:
                messages.append({"role": "system", "content": f"Grounding from mentioned file(s):\n{fc}\n\nAnswer based strictly on this content when relevant. Do not run shell commands."})
            missing = api_results.get("files_missing")
            if missing:
                messages.append({"role": "system", "content": f"User mentioned file(s) not found: {missing}. Respond explicitly that the file was not found and avoid speculation."})
            forbidden = api_results.get("files_forbidden")
            if forbidden:
                messages.append({"role": "system", "content": f"User mentioned file(s) outside the allowed workspace or sensitive paths: {forbidden}. Refuse to access and explain the restriction succinctly."})
            
            # Add conversation history with smart context management
            if len(self.conversation_history) > 12:
                # For long conversations, summarize early context and keep recent history
                early_history = self.conversation_history[:-6]
                recent_history = self.conversation_history[-6:]
                
                # Create a summary of early conversation
                summary_prompt = "Summarize the key points from this conversation history in 2-3 sentences:"
                summary_messages = [
                    {"role": "system", "content": summary_prompt},
                    {"role": "user", "content": str(early_history)}
                ]
                
                try:
                    summary_response = self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=summary_messages,
                        max_tokens=200,
                        temperature=0.3
                    )
                    conversation_summary = summary_response.choices[0].message.content
                    messages.append({"role": "system", "content": f"Previous conversation summary: {conversation_summary}"})
                except:
                    # If summary fails, just use recent history
                    pass
                
                messages.extend(recent_history)
            else:
                # For shorter conversations, use full history
                messages.extend(self.conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": request.question})
            
            # Check token budget
            estimated_tokens = len(str(messages)) // 4  # Rough estimate
            if not self._check_token_budget(estimated_tokens):
                return ChatResponse(
                    response="⚠️ Daily token limit reached. Please try again tomorrow or upgrade your plan.",
                    timestamp=datetime.now().isoformat()
                )
            
            # Get Groq's response with rate limit handling
            try:
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=1000,  # Increased for more comprehensive responses
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else estimated_tokens
                self._charge_tokens(tokens_used)
                
                # Track cost
                cost = (tokens_used / 1000) * self.cost_per_1k_tokens
                self.total_cost += cost
                
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limit errors specifically
                if "rate limit" in error_str.lower() or "429" in error_str:
                    return ChatResponse(
                        response="⚠️ **API Rate Limit Reached**\n\nI've temporarily hit my daily usage limit. This is a free tier limitation.\n\n**Options:**\n- Wait 24 hours for the limit to reset\n- Upgrade to a paid Groq plan for higher limits\n- Try again in a few hours\n\nYour conversation history is saved, so you can continue where you left off.",
                        timestamp=datetime.now().isoformat(),
                        tools_used=tools_used,
                        api_results=api_results,
                        error_message=f"Rate limit reached: {error_str}"
                    )
                
                # Handle other API errors
                return ChatResponse(
                    response=f"❌ **API Error**\n\nI encountered an error while processing your request: {error_str}\n\nPlease try again in a moment.",
                    timestamp=datetime.now().isoformat(),
                    tools_used=tools_used,
                    api_results=api_results,
                    error_message=error_str
                )
            
            # Check for commands in backticks (disabled if file context provided or files missing)
            commands = [] if (api_results.get("files_context") or api_results.get("files_missing") or api_results.get("files_forbidden")) else re.findall(r'`([^`]+)`', response_text)
            execution_results = {}
            final_response = response_text
            
            def _is_safe_command(cmd: str) -> bool:
                # Block obvious dangerous characters/pipelines/subshells
                blocked_tokens = [';', '|', '&&', '||', '<', '`', '$(', '${']
                if any(bt in cmd for bt in blocked_tokens):
                    return False
                # Disallow commands that are just filenames/paths without an executable
                if ' ' not in cmd and (Path(cmd).exists() or cmd.startswith(('./', '../', '/'))):
                    return False
                # Allow limited, safe redirection only for echo to allowed paths
                if '>' in cmd:
                    import re as _re
                    m = _re.match(r"^\s*echo\s+(.+?)\s*(>>|>)\s*(.+?)\s*$", cmd)
                    if not m:
                        return False
                    target = m.group(3).strip().strip('"\'')
                    try:
                        target_path = Path(target).resolve()
                        base_dir = Path.cwd().resolve()
                        if str(target_path).startswith(str(base_dir)) or str(target_path).startswith('/tmp/'):
                            pass
                        else:
                            return False
                    except Exception:
                        return False
                    # sanitize content length
                    return True
                # Simple allowlist for base commands
                allowed = { 'ls', 'pwd', 'cat', 'head', 'tail', 'wc', 'stat', 'cd', 'export', 'echo', 'rm', 'whoami' }
                first = cmd.split()[0]
                return first in allowed

            if commands:
                command = commands[0].strip()
                if _is_safe_command(command):
                    print(f"\n🔧 Executing: {command}")
                    output = self.execute_command(command)
                    print(f"✅ Command completed")
                    execution_results = {
                        "command": command,
                        "output": output,
                        "success": not output.startswith("ERROR:")
                    }
                    tools_used.append("shell_execution")
                else:
                    execution_results = {
                        "command": command,
                        "output": "Command blocked by safety policy",
                        "success": False
                    }
                    tools_used.append("shell_blocked")
                
                # Create analysis prompt only if we actually executed and have output
                if execution_results.get("success") and isinstance(execution_results.get("output"), str):
                    truncated_output = execution_results["output"]
                    if len(truncated_output) > 1000:
                        truncated_output = truncated_output[:1000]
                    analysis_prompt = f"""User asked: "{request.question}"
Command: `{command}`
Results: {truncated_output}

Brief summary:"""
                    
                    # Get Groq's analysis of the real results
                    analysis_response = self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": analysis_prompt}],
                        max_tokens=300,
                        temperature=0.3
                    )
                    
                    analysis = analysis_response.choices[0].message.content
                    final_response = f"{response_text}\n\n{analysis}"
                    
                    # Charge additional tokens
                    additional_tokens = analysis_response.usage.total_tokens if analysis_response.usage else 100
                    self._charge_tokens(additional_tokens)
                    tokens_used += additional_tokens
            else:
                final_response = response_text
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": request.question})
            self.conversation_history.append({"role": "assistant", "content": final_response})
            
            # Update memory
            self._update_memory(
                request.user_id, 
                request.conversation_id, 
                f"Q: {request.question[:100]}... A: {final_response[:100]}..."
            )
            
            return ChatResponse(
                response=final_response,
                tools_used=tools_used,
                reasoning_steps=[f"Request type: {request_analysis['type']}", f"APIs used: {request_analysis['apis']}"],
                timestamp=datetime.now().isoformat(),
                tokens_used=tokens_used,
                confidence_score=request_analysis['confidence'],
                execution_results=execution_results,
                api_results=api_results
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"❌ Error: {str(e)}",
                timestamp=datetime.now().isoformat(),
                confidence_score=0.0
            )
    
    async def run_interactive(self):
        """Run interactive chat session"""
        if not await self.initialize():
            return
            
        print("\n" + "="*70)
        print("🤖 ENHANCED NOCTURNAL AI AGENT")
        print("="*70)
        print("Research Assistant with Archive API + FinSight API Integration")
        print("Type 'quit' to exit")
        print("="*70)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    # Clean up
                    if self.shell_session:
                        self.shell_session.terminate()
                    if self.session:
                        await self.session.close()
                    break
                
                # Process request
                request = ChatRequest(question=user_input)
                response = await self.process_request(request)
                
                print(f"\n🤖 Agent: {response.response}")
                
                if response.api_results:
                    print(f"📊 API Results: {len(response.api_results)} sources used")
                
                if response.execution_results:
                    print(f"🔧 Command: {response.execution_results['command']}")
                    print(f"📊 Success: {response.execution_results['success']}")
                
                print(f"📈 Tokens used: {response.tokens_used}")
                print(f"🎯 Confidence: {response.confidence_score:.2f}")
                print(f"🛠️ Tools used: {', '.join(response.tools_used) if response.tools_used else 'None'}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                # Clean up
                if self.shell_session:
                    self.shell_session.terminate()
                if self.session:
                    await self.session.close()
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

async def main():
    """Main entry point"""
    agent = EnhancedNocturnalAgent()
    await agent.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())
