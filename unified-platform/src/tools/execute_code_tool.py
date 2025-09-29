#!/usr/bin/env python3
"""
Execute Code Tool - Sandboxed code execution for Python/R
"""

import os
import sys
import json
import uuid
import tempfile
import subprocess
import resource
import signal
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    artifacts: List[Dict[str, str]] = None
    tables: List[Dict[str, Any]] = None
    runtime_ms: int = 0

class ExecuteCodeTool:
    """Sandboxed code execution tool"""
    
    def __init__(self, workspace_root: str = "/tmp/vertikal_run"):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(exist_ok=True)
        
        # Allowed libraries for Python
        self.allowed_imports = {
            'numpy', 'pandas', 'scipy', 'statsmodels', 'matplotlib',
            'seaborn', 'sklearn', 'plotly', 'json', 'csv', 'math',
            'statistics', 'random', 'datetime', 'collections'
        }
        
        # Resource limits
        self.max_cpu_time = 8  # seconds
        self.max_memory = 512 * 1024 * 1024  # 512MB
        self.max_file_size = 20 * 1024 * 1024  # 20MB
        
    def execute_python(self, code: str, files: List[str] = None, timeout_s: int = 8) -> ExecutionResult:
        """Execute Python code in sandboxed environment"""
        start_time = time.time()
        
        # Create isolated workspace
        workspace = self.workspace_root / str(uuid.uuid4())
        workspace.mkdir(exist_ok=True)
        
        try:
            # Copy input files to workspace
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        dest_path = workspace / os.path.basename(file_path)
                        subprocess.run(['cp', file_path, str(dest_path)], check=True)
            
            # Sanitize code
            sanitized_code = self._sanitize_python_code(code)
            
            # Create execution script
            script_path = workspace / "execute.py"
            with open(script_path, 'w') as f:
                f.write(sanitized_code)
            
            # Execute with resource limits
            result = self._run_with_limits(
                ['python3', str(script_path)],
                cwd=str(workspace),
                timeout=timeout_s
            )
            
            # Collect artifacts
            artifacts = self._collect_artifacts(workspace)
            
            runtime_ms = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                artifacts=artifacts,
                runtime_ms=runtime_ms
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {timeout_s} seconds",
                exit_code=124,
                runtime_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                runtime_ms=int((time.time() - start_time) * 1000)
            )
        finally:
            # Cleanup workspace
            import shutil
            if workspace.exists():
                shutil.rmtree(workspace, ignore_errors=True)
    
    def execute_r(self, code: str, files: List[str] = None, timeout_s: int = 8) -> ExecutionResult:
        """Execute R code in sandboxed environment"""
        start_time = time.time()
        
        # Create isolated workspace
        workspace = self.workspace_root / str(uuid.uuid4())
        workspace.mkdir(exist_ok=True)
        
        try:
            # Copy input files to workspace
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        dest_path = workspace / os.path.basename(file_path)
                        subprocess.run(['cp', file_path, str(dest_path)], check=True)
            
            # Create R script
            script_path = workspace / "execute.R"
            with open(script_path, 'w') as f:
                f.write(code)
            
            # Execute with resource limits
            result = self._run_with_limits(
                ['Rscript', '--vanilla', str(script_path)],
                cwd=str(workspace),
                timeout=timeout_s
            )
            
            # Collect artifacts
            artifacts = self._collect_artifacts(workspace)
            
            runtime_ms = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                artifacts=artifacts,
                runtime_ms=runtime_ms
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"R execution timed out after {timeout_s} seconds",
                exit_code=124,
                runtime_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=f"R execution error: {str(e)}",
                exit_code=1,
                runtime_ms=int((time.time() - start_time) * 1000)
            )
        finally:
            # Cleanup workspace
            import shutil
            if workspace.exists():
                shutil.rmtree(workspace, ignore_errors=True)
    
    def _sanitize_python_code(self, code: str) -> str:
        """Sanitize Python code to prevent dangerous operations"""
        # Remove dangerous imports
        dangerous_imports = [
            'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib',
            'http', 'ftplib', 'smtplib', 'telnetlib', 'webbrowser'
        ]
        
        lines = code.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Skip dangerous imports
            if any(f'import {dangerous}' in line or f'from {dangerous}' in line 
                   for dangerous in dangerous_imports):
                sanitized_lines.append(f"# BLOCKED: {line}")
                continue
            
            # Allow safe imports
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)
    
    def _run_with_limits(self, cmd: List[str], cwd: str, timeout: int) -> subprocess.CompletedProcess:
        """Run command with resource limits"""
        def set_limits():
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory, self.max_memory))
            # Set file size limit
            resource.setrlimit(resource.RLIMIT_FSIZE, (self.max_file_size, self.max_file_size))
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=set_limits
            )
            return result
        except subprocess.TimeoutExpired as e:
            # Kill the process
            if e.process:
                e.process.kill()
            raise
    
    def _collect_artifacts(self, workspace: Path) -> List[Dict[str, str]]:
        """Collect generated artifacts (plots, files) from workspace"""
        artifacts = []
        
        # Look for common output files
        for pattern in ['*.png', '*.jpg', '*.pdf', '*.csv', '*.json']:
            for file_path in workspace.glob(pattern):
                if file_path.is_file():
                    # Determine MIME type
                    mime_type = self._get_mime_type(file_path)
                    artifacts.append({
                        'path': str(file_path),
                        'mime': mime_type,
                        'name': file_path.name
                    })
        
        return artifacts
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        suffix = file_path.suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.txt': 'text/plain'
        }
        return mime_types.get(suffix, 'application/octet-stream')

# Global instance
execute_tool = ExecuteCodeTool()

def execute_code(language: str, code: str, files: List[str] = None, timeout_s: int = 8) -> Dict[str, Any]:
    """
    Execute code in sandboxed environment
    
    Args:
        language: "python" or "r"
        code: Code to execute
        files: Optional list of input files
        timeout_s: Timeout in seconds
    
    Returns:
        Dict with stdout, stderr, exit_code, artifacts, runtime_ms
    """
    if language.lower() == "python":
        result = execute_tool.execute_python(code, files, timeout_s)
    elif language.lower() == "r":
        result = execute_tool.execute_r(code, files, timeout_s)
    else:
        return {
            "stdout": "",
            "stderr": f"Unsupported language: {language}",
            "exit_code": 1,
            "artifacts": [],
            "runtime_ms": 0
        }
    
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "artifacts": result.artifacts or [],
        "runtime_ms": result.runtime_ms
    }
