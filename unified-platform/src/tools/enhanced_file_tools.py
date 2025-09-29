#!/usr/bin/env python3
"""
Enhanced File Tools - Real Functionality Like Claude
"""

import os
import json
import subprocess
import shutil
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class EnhancedFileTools:
    """Enhanced file tools that actually work like Claude"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.current_dir = self.base_path
        
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base directory"""
        if os.path.isabs(path):
            return Path(path)
        return self.base_path / path
    
    def read_file(self, file_path: str, offset: int = None, limit: int = None) -> Dict[str, Any]:
        """Read file contents - actually works"""
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                if offset is not None and limit is not None:
                    lines = f.readlines()
                    start_line = max(0, offset - 1)
                    end_line = min(len(lines), start_line + limit)
                    content = ''.join(lines[start_line:end_line])
                    line_info = f"Lines {offset}-{offset + limit - 1} of {len(lines)}"
                else:
                    content = f.read()
                    line_info = f"Full file ({len(content.splitlines())} lines)"
            
            return {
                "success": True,
                "content": content,
                "file_path": str(full_path),
                "line_info": line_info,
                "size": len(content),
                "lines": len(content.splitlines())
            }
            
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied: {file_path}",
                "content": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}",
                "content": None
            }
    
    def write_file(self, file_path: str, contents: str) -> Dict[str, Any]:
        """Write content to file - actually works"""
        try:
            full_path = self._resolve_path(file_path)
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(contents)
            
            return {
                "success": True,
                "file_path": str(full_path),
                "size": len(contents),
                "lines": len(contents.splitlines())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}"
            }
    
    def list_dir(self, path: str = None) -> Dict[str, Any]:
        """List directory contents - actually works"""
        try:
            target_path = self._resolve_path(path) if path else self.current_dir
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {path}",
                    "contents": []
                }
            
            if not target_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}",
                    "contents": []
                }
            
            contents = []
            for item in target_path.iterdir():
                contents.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime
                })
            
            return {
                "success": True,
                "path": str(target_path),
                "contents": contents
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory: {str(e)}",
                "contents": []
            }
    
    def execute_terminal_command(self, command: str, working_dir: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute terminal command - actually works"""
        try:
            # Set working directory
            if working_dir:
                work_dir = self._resolve_path(working_dir)
                if not work_dir.exists() or not work_dir.is_dir():
                    return {
                        "success": False,
                        "error": f"Working directory not found: {working_dir}",
                        "stdout": "",
                        "stderr": "",
                        "return_code": -1
                    }
            else:
                work_dir = self.current_dir
            
            logger.info(f"Executing command: {command} in {work_dir}")
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": True,
                "command": command,
                "working_directory": str(work_dir),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "execution_time": "< 1s"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing command: {str(e)}",
                "command": command,
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
    
    def execute_python_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code - actually works"""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute the Python code
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.current_dir
                )
                
                return {
                    "success": True,
                    "code": code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "execution_time": "< 1s"
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timed out after {timeout} seconds",
                "code": code,
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Error executing Python code: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing Python code: {str(e)}",
                "code": code,
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
    
    def search_files(self, pattern: str, path: str = None) -> Dict[str, Any]:
        """Search for files matching pattern - actually works"""
        try:
            import glob
            
            target_path = self._resolve_path(path) if path else self.current_dir
            search_pattern = str(target_path / "**" / pattern)
            
            matches = glob.glob(search_pattern, recursive=True)
            
            results = []
            for match in matches:
                match_path = Path(match)
                results.append({
                    "path": str(match_path),
                    "name": match_path.name,
                    "type": "directory" if match_path.is_dir() else "file",
                    "size": match_path.stat().st_size if match_path.is_file() else 0
                })
            
            return {
                "success": True,
                "pattern": pattern,
                "search_path": str(target_path),
                "matches": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching files: {str(e)}",
                "matches": [],
                "count": 0
            }
    
    def search_files(self, pattern: str, search_path: str = None) -> Dict[str, Any]:
        """Search for files/directories matching a pattern"""
        try:
            if search_path is None:
                search_path = str(self.base_path)
            
            target_path = Path(search_path)
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Search path does not exist: {search_path}",
                    "matches": [],
                    "count": 0
                }
            
            results = []
            
            # Search recursively for directories/files matching pattern
            for item in target_path.rglob("*"):
                if pattern.lower() in item.name.lower():
                    results.append({
                        "path": str(item),
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "search_path": str(target_path),
                "matches": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching files: {str(e)}",
                "matches": [],
                "count": 0
            }