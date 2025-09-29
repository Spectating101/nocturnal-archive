#!/usr/bin/env python3
"""
File System Tools - Mimics Claude's file system capabilities
Provides read_file, list_dir, search_replace, and other file operations
"""

import os
import json
import subprocess
import shutil
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class FileSystemTools:
    """Tools for file system operations - mimicking Claude's capabilities"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.current_dir = self.base_path
        
    def read_file(self, file_path: str, offset: int = None, limit: int = None) -> Dict[str, Any]:
        """
        Read a file - mimics Claude's read_file tool
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None
                }
            
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}",
                    "content": None
                }
            
            # Read file content
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
    
    def list_dir(self, target_directory: str = None, ignore_globs: List[str] = None) -> Dict[str, Any]:
        """
        List directory contents - mimics Claude's list_dir tool
        """
        try:
            if target_directory:
                full_path = self._resolve_path(target_directory)
            else:
                full_path = self.current_dir
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {target_directory or 'current'}",
                    "contents": []
                }
            
            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {target_directory or 'current'}",
                    "contents": []
                }
            
            # Get directory contents
            contents = []
            for item in full_path.iterdir():
                # Skip hidden files by default
                if item.name.startswith('.'):
                    continue
                
                # Apply ignore patterns
                if ignore_globs:
                    should_ignore = False
                    for pattern in ignore_globs:
                        if item.match(pattern):
                            should_ignore = True
                            break
                    if should_ignore:
                        continue
                
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "path": str(item)
                }
                contents.append(item_info)
            
            # Sort: directories first, then files, both alphabetically
            contents.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "success": True,
                "contents": contents,
                "directory": str(full_path),
                "count": len(contents)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory: {str(e)}",
                "contents": []
            }
    
    def search_replace(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> Dict[str, Any]:
        """
        Search and replace in file - mimics Claude's search_replace tool
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "changes_made": 0
                }
            
            # Read file content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                changes_made = content.count(old_string)
            else:
                if old_string not in content:
                    return {
                        "success": False,
                        "error": f"String not found: {old_string}",
                        "changes_made": 0
                    }
                new_content = content.replace(old_string, new_string, 1)
                changes_made = 1
            
            # Write back to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "changes_made": changes_made,
                "file_path": str(full_path),
                "old_string": old_string,
                "new_string": new_string
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in search_replace: {str(e)}",
                "changes_made": 0
            }
    
    def write_file(self, file_path: str, contents: str) -> Dict[str, Any]:
        """
        Write content to file - mimics Claude's write tool
        """
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
                "error": f"Error writing file: {str(e)}",
                "file_path": file_path
            }
    
    def run_terminal_cmd(self, command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Run terminal command - mimics Claude's run_terminal_cmd tool
        """
        try:
            working_dir = self._resolve_path(cwd) if cwd else self.current_dir
            
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": True,
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "working_directory": str(working_dir)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running command: {str(e)}",
                "command": command
            }
    
    def glob_file_search(self, glob_pattern: str, target_directory: str = None) -> Dict[str, Any]:
        """
        Search for files matching glob pattern - mimics Claude's glob_file_search tool
        """
        try:
            if target_directory:
                search_path = self._resolve_path(target_directory)
            else:
                search_path = self.current_dir
            
            # Find matching files
            matches = []
            for file_path in search_path.rglob(glob_pattern):
                if file_path.is_file():
                    matches.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
            
            # Sort by modification time (newest first)
            matches.sort(key=lambda x: x["modified"], reverse=True)
            
            return {
                "success": True,
                "matches": matches,
                "pattern": glob_pattern,
                "search_directory": str(search_path),
                "count": len(matches)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in glob search: {str(e)}",
                "matches": []
            }
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve relative paths against current directory"""
        if os.path.isabs(path):
            return Path(path)
        return self.current_dir / path
    
    def change_directory(self, new_dir: str) -> Dict[str, Any]:
        """Change current working directory"""
        try:
            full_path = self._resolve_path(new_dir)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {new_dir}"
                }
            
            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {new_dir}"
                }
            
            self.current_dir = full_path
            return {
                "success": True,
                "current_directory": str(self.current_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error changing directory: {str(e)}"
            }
    
    async def execute_terminal_command(self, command: str, working_dir: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a terminal command - mimics Claude's terminal execution capabilities
        """
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
            
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                shell=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                # Decode output
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                return {
                    "success": True,
                    "command": command,
                    "working_directory": str(work_dir),
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "return_code": process.returncode,
                    "execution_time": "< 1s"
                }
                
            except asyncio.TimeoutError:
                process.kill()
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
    
    def execute_terminal_command_sync(self, command: str, working_dir: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a terminal command synchronously - for non-async contexts
        """
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