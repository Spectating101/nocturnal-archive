"""
File Operations Tool - Safe file system operations
"""

import asyncio
import logging
import os
import json
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class FileOperationsTool:
    """
    Safe file operations tool with security restrictions.
    
    Features:
    - Read, write, list file operations
    - Directory traversal and analysis
    - File content analysis and search
    - Security validation and path restrictions
    - Support for various file formats
    """
    
    def __init__(self):
        # Security restrictions
        self.allowed_extensions = ['.txt', '.py', '.js', '.json', '.md', '.csv', '.log', '.yml', '.yaml']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.forbidden_paths = ['/etc', '/sys', '/proc', '/dev', '/root']
        
        logger.info("File Operations Tool initialized")
    
    async def execute(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute file operation based on task description.
        
        Args:
            task_description: Description of the file operation
            context: Additional context including file paths, content, etc.
            
        Returns:
            Operation result with file data and metadata
        """
        try:
            # Parse task description to determine operation
            task_lower = task_description.lower()
            
            # Determine operation from task description
            if any(keyword in task_lower for keyword in ["list", "directory", "folder", "ls", "dir"]):
                operation = "list"
                directory = context.get("directory", ".")
                return await self._list_directory(directory)
            elif any(keyword in task_lower for keyword in ["read", "open", "get"]):
                operation = "read"
                file_path = context.get("file_path", "")
                return await self._read_file(file_path)
            elif any(keyword in task_lower for keyword in ["write", "create", "save"]):
                operation = "write"
                file_path = context.get("file_path", "")
                content = context.get("content", "")
                return await self._write_file(file_path, content)
            elif any(keyword in task_lower for keyword in ["search", "find", "look"]):
                operation = "search"
                pattern = context.get("pattern", "")
                directory = context.get("directory", ".")
                return await self._search_files(pattern, directory)
            elif any(keyword in task_lower for keyword in ["analyze", "info", "stat"]):
                operation = "analyze"
                file_path = context.get("file_path", "")
                return await self._analyze_file(file_path)
            else:
                # Default to list operation for general file operations
                directory = context.get("directory", ".")
                return await self._list_directory(directory)
            
        except Exception as e:
            logger.error(f"File operation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file content safely."""
        if not self._is_path_safe(file_path):
            return {
                "status": "error",
                "error": "Path not allowed for security reasons",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "status": "error",
                    "error": f"File not found: {file_path}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if path.is_dir():
                return {
                    "status": "error",
                    "error": f"Path is a directory, not a file: {file_path}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return {
                    "status": "error",
                    "error": f"File too large: {file_size} bytes (max: {self.max_file_size})",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "file_size": file_size,
                "file_type": path.suffix,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to read file: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file safely."""
        if not self._is_path_safe(file_path):
            return {
                "status": "error",
                "error": "Path not allowed for security reasons",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            path = Path(file_path)
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "file_path": file_path,
                "content_length": len(content),
                "message": "File written successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to write file: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _list_directory(self, directory: str) -> Dict[str, Any]:
        """List directory contents safely."""
        if not self._is_path_safe(directory):
            return {
                "status": "error",
                "error": "Path not allowed for security reasons",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            path = Path(directory)
            if not path.exists():
                return {
                    "status": "error",
                    "error": f"Directory not found: {directory}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if not path.is_dir():
                return {
                    "status": "error",
                    "error": f"Path is not a directory: {directory}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # List contents
            files = []
            directories = []
            
            for item in path.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "size": item.stat().st_size,
                        "extension": item.suffix,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                elif item.is_dir():
                    directories.append({
                        "name": item.name,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            
            return {
                "status": "success",
                "directory": directory,
                "files": files,
                "directories": directories,
                "total_files": len(files),
                "total_directories": len(directories),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to list directory: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _search_files(self, pattern: str, directory: str) -> Dict[str, Any]:
        """Search for files matching pattern."""
        if not self._is_path_safe(directory):
            return {
                "status": "error",
                "error": "Path not allowed for security reasons",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return {
                    "status": "error",
                    "error": f"Invalid directory: {directory}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Search for files matching pattern
            matches = []
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    matches.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix
                    })
            
            return {
                "status": "success",
                "pattern": pattern,
                "directory": directory,
                "matches": matches,
                "total_matches": len(matches),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to search files: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze file content and properties."""
        read_result = await self._read_file(file_path)
        if read_result["status"] != "success":
            return read_result
        
        content = read_result["content"]
        analysis = {
            "file_path": file_path,
            "file_size": read_result["file_size"],
            "file_type": read_result["file_type"],
            "line_count": len(content.splitlines()),
            "word_count": len(content.split()),
            "character_count": len(content),
            "has_content": len(content.strip()) > 0
        }
        
        # Additional analysis based on file type
        if file_path.endswith('.json'):
            try:
                json.loads(content)
                analysis["is_valid_json"] = True
            except:
                analysis["is_valid_json"] = False
        
        elif file_path.endswith('.py'):
            analysis["python_lines"] = len([line for line in content.splitlines() if line.strip()])
            analysis["has_imports"] = "import " in content or "from " in content
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _is_path_safe(self, path: str) -> bool:
        """Check if path is safe to access."""
        path = os.path.abspath(path)
        
        # Check for forbidden paths
        for forbidden in self.forbidden_paths:
            if path.startswith(forbidden):
                return False
        
        # Check for path traversal attempts
        if '..' in path:
            return False
        
        # Allow paths within the project directory
        project_root = "/home/phyrexian/Downloads/llm_automation/project_portfolio/Nocturnal-Archive"
        if path.startswith(project_root):
            return True
        
        # Allow relative paths that don't go outside current directory
        if not path.startswith('/'):
            return True
        
        return False
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file content specifically."""
        return await self._read_file(file_path)
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file specifically."""
        return await self._write_file(file_path, content)
    
    async def list_directory(self, directory: str) -> Dict[str, Any]:
        """List directory contents specifically."""
        return await self._list_directory(directory)
    
    async def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search for files matching pattern specifically."""
        return await self._search_files(pattern, directory)
