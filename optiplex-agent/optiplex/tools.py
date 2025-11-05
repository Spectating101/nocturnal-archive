"""Advanced tools for Optiplex Agent"""
import subprocess
import glob
import re
import os
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BashResult:
    """Result from bash execution"""
    stdout: str
    stderr: str
    returncode: int
    success: bool


class BashTool:
    """Execute bash commands"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def execute(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> BashResult:
        """Execute a bash command"""
        work_dir = Path(cwd) if cwd else self.root_dir

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return BashResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                success=result.returncode == 0
            )
        except subprocess.TimeoutExpired:
            return BashResult(
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                returncode=-1,
                success=False
            )
        except Exception as e:
            return BashResult(
                stdout="",
                stderr=str(e),
                returncode=-1,
                success=False
            )


class GrepTool:
    """Search for patterns in files"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def search(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: Optional[str] = None,
        case_sensitive: bool = True,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for pattern in files"""
        results = []
        search_path = Path(path) if path else self.root_dir

        # Compile regex
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return [{"error": f"Invalid regex: {e}"}]

        # Determine files to search
        if file_pattern:
            files = glob.glob(str(search_path / file_pattern), recursive=True)
        else:
            files = [str(f) for f in search_path.rglob('*') if f.is_file()]

        # Search files
        for filepath in files:
            if len(results) >= max_results:
                break

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                'file': filepath,
                                'line': line_num,
                                'content': line.rstrip()
                            })
                            if len(results) >= max_results:
                                break
            except:
                continue

        return results


class GlobTool:
    """Find files matching patterns"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def find(
        self,
        pattern: str,
        path: Optional[str] = None,
        recursive: bool = True
    ) -> List[str]:
        """Find files matching glob pattern"""
        search_path = Path(path) if path else self.root_dir
        full_pattern = str(search_path / pattern)

        try:
            matches = glob.glob(full_pattern, recursive=recursive)
            return sorted(matches)
        except Exception as e:
            return [f"Error: {e}"]


class TodoManager:
    """Manage todo list for task tracking"""

    def __init__(self):
        self.todos: List[Dict[str, Any]] = []

    def add(self, content: str, status: str = "pending") -> Dict[str, Any]:
        """Add a todo item"""
        todo = {
            "id": len(self.todos),
            "content": content,
            "status": status
        }
        self.todos.append(todo)
        return todo

    def update(self, todo_id: int, status: str) -> bool:
        """Update todo status"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = status
                return True
        return False

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all todos"""
        return self.todos

    def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending todos"""
        return [t for t in self.todos if t["status"] == "pending"]

    def clear(self):
        """Clear all todos"""
        self.todos = []


class WebTool:
    """Web search and fetch capabilities"""

    def __init__(self, search_api_key: Optional[str] = None):
        self.search_api_key = search_api_key or os.getenv("SERPER_API_KEY")

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search the web using Serper API"""
        if not self.search_api_key:
            return [{"error": "SERPER_API_KEY not set"}]

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.search_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query, "num": num_results},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })

            return results
        except Exception as e:
            return [{"error": str(e)}]

    def fetch(self, url: str, timeout: int = 10) -> Dict[str, str]:
        """Fetch content from URL"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            return {
                "url": url,
                "status": response.status_code,
                "content": response.text[:50000],  # Limit content
                "content_type": response.headers.get("content-type", "")
            }
        except Exception as e:
            return {"error": str(e)}


class PlannerTool:
    """Multi-step task planning"""

    def __init__(self):
        self.current_plan: List[Dict[str, Any]] = []
        self.current_step = 0

    def create_plan(self, steps: List[str]) -> List[Dict[str, Any]]:
        """Create a new plan"""
        self.current_plan = [
            {
                "id": i,
                "description": step,
                "status": "pending",
                "result": None
            }
            for i, step in enumerate(steps)
        ]
        self.current_step = 0
        return self.current_plan

    def get_current_step(self) -> Optional[Dict[str, Any]]:
        """Get current step"""
        if self.current_step < len(self.current_plan):
            return self.current_plan[self.current_step]
        return None

    def complete_step(self, result: str):
        """Mark current step as complete and move to next"""
        if self.current_step < len(self.current_plan):
            self.current_plan[self.current_step]["status"] = "completed"
            self.current_plan[self.current_step]["result"] = result
            self.current_step += 1

    def get_plan_status(self) -> Dict[str, Any]:
        """Get plan status"""
        return {
            "total_steps": len(self.current_plan),
            "completed_steps": sum(1 for s in self.current_plan if s["status"] == "completed"),
            "current_step": self.current_step,
            "steps": self.current_plan
        }
