"""
Production-ready secure shell access with proper isolation
"""

import asyncio
import subprocess
import tempfile
import os
import signal
import time
from typing import Dict, Any, Optional
import structlog
from fastapi import HTTPException, status
import docker
from docker.errors import DockerException

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

class SecureShell:
    """Production-ready secure shell with Docker isolation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_mode = self.settings.environment == "test"
        self.docker_client = None
        self.containers = {}  # Track active containers per user
        self.max_containers = 10  # Limit concurrent containers
        
        if self.test_mode:
            logger.info("SecureShell running in test mode with mocked execution")
            return
        
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error("Failed to initialize Docker client", error=str(e))
            self.docker_client = None
    
    def _get_container_name(self, user_id: str) -> str:
        """Generate unique container name for user"""
        return f"nocturnal-shell-{user_id}"
    
    def _get_safe_commands(self) -> set:
        """Define safe commands that are allowed"""
        return {
            "ls", "pwd", "cd", "cat", "head", "tail", "grep", "find", "which",
            "ps", "top", "df", "du", "free", "uptime", "whoami", "id",
            "git", "python", "python3", "pip", "pip3", "node", "npm",
            "curl", "wget", "tar", "zip", "unzip", "mkdir", "rmdir",
            "touch", "cp", "mv", "rm", "chmod", "chown", "ln", "stat",
            "file", "type", "env", "echo", "date", "history", "alias",
            "wc", "sort", "uniq", "cut", "awk", "sed", "tr", "diff",
            "less", "more", "man", "info", "help", "apropos", "whereis",
            "locate", "updatedb", "tree", "basename", "dirname", "realpath",
            "at", "R", "r", "julia", "matlab", "octave", "sage", "maxima"
        }
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute"""
        if not command or not command.strip():
            return False
        
        command_lower = command.lower().strip()
        
        # First check for dangerous patterns (this takes priority)
        # Use word boundaries to avoid false positives
        dangerous_patterns = [
            "rm -rf", "sudo", "su ", "passwd", "chmod 777", "chown root",
            "dd if=", "mkfs", "fdisk", "mount", "umount", "reboot", "shutdown",
            "kill -9", "killall", "pkill", "xkill", "halt", "poweroff",
            "init 0", "init 6", "service", "systemctl", "systemd",
            "crontab", " at ", "batch", "nohup", "screen", "tmux",
            "ssh", "scp", "rsync", "nc", "netcat", "telnet", "ftp",
            "wget", "curl", "nc", "netcat", "telnet", "ftp", "sftp",
            "python -c", "perl -e", "ruby -e", "node -e", "bash -c",
            "sh -c", "zsh -c", "fish -c", "tcsh -c", "csh -c",
            "rm -r", "rm -f", "rm -", "chmod +", "chown +", "chmod 0",
            "dd of=", "mkfs.", "fdisk", "mount -", "umount -",
            "kill -", "killall", "pkill", "xkill", "halt", "poweroff",
            "init ", "service ", "systemctl ", "systemd-",
            "crontab ", " at ", "batch ", "nohup ", "screen ", "tmux ",
            "ssh ", "scp ", "rsync ", "nc ", "netcat ", "telnet ", "ftp ",
            "wget ", "curl ", "nc ", "netcat ", "telnet ", "ftp ", "sftp ",
            "python -c", "perl -e", "ruby -e", "node -e", "bash -c",
            "sh -", "zsh -", "fish -", "tcsh -", "csh -"
        ]
        
        # Block redirections, pipes, subshells explicitly
        meta_chars = ['|', '>', '>>', '2>', '&>', '<', '`', '$(', ');', '&&', '||']
        for meta in meta_chars:
            if meta in command_lower:
                return False

        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        # Extract the base command (first word)
        base_command = command.strip().split()[0] if command.strip() else ""
        
        # Check against safe commands list
        if base_command in self._get_safe_commands():
            return True
        
        # If not in safe list and no dangerous patterns, it's unsafe
        return False
    
    async def _create_secure_container(self, user_id: str) -> Optional[docker.models.containers.Container]:
        """Create a secure Docker container for shell access"""
        if self.test_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Secure shell containerization disabled in test mode"
            )

        if not self.docker_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Docker service not available"
            )
        
        container_name = self._get_container_name(user_id)
        
        try:
            # Remove existing container if it exists
            try:
                existing = self.docker_client.containers.get(container_name)
                existing.remove(force=True)
            except docker.errors.NotFound:
                pass
            
            # Create new secure container
            container = self.docker_client.containers.run(
                "python:3.11-alpine",
                name=container_name,
                detach=True,
                stdin_open=True,
                tty=True,
                working_dir="/workspace",
                volumes={
                    # Mount a temporary directory as workspace
                    tempfile.mkdtemp(): {"bind": "/workspace", "mode": "rw"}
                },
                environment={
                    "HOME": "/workspace",
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "SHELL": "/bin/sh"
                },
                # Security constraints
                network_mode="none",  # No network access
                mem_limit="512m",     # Memory limit
                cpu_quota=50000,      # CPU limit (50% of one core)
                cpu_period=100000,    # CPU period
                read_only=False,      # Allow writing to workspace
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],     # Drop all capabilities
                cap_add=[],           # No additional capabilities
                user="1000:1000",     # Non-root user
                command="sh"          # Start with shell
            )
            
            # Wait for container to be ready
            await asyncio.sleep(1)
            
            logger.info(
                "Secure container created",
                user_id=user_id,
                container_id=container.short_id,
                container_name=container_name
            )
            
            return container
            
        except Exception as e:
            logger.error(
                "Failed to create secure container",
                user_id=user_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create secure environment: {str(e)}"
            )
    
    async def _get_or_create_container(self, user_id: str) -> docker.models.containers.Container:
        """Get existing container or create new one for user"""
        container_name = self._get_container_name(user_id)
        
        # Check if container already exists and is running
        if container_name in self.containers:
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status == "running":
                    return container
                else:
                    # Container exists but not running, remove it
                    container.remove(force=True)
                    del self.containers[container_name]
            except docker.errors.NotFound:
                # Container doesn't exist, remove from tracking
                if container_name in self.containers:
                    del self.containers[container_name]
        
        # Check container limit
        if len(self.containers) >= self.max_containers:
            # Remove oldest container
            oldest_user = min(self.containers.keys(), key=lambda k: self.containers[k]["created_at"])
            await self.cleanup_user_container(oldest_user)
        
        # Create new container
        container = await self._create_secure_container(user_id)
        self.containers[container_name] = {
            "container": container,
            "created_at": time.time(),
            "user_id": user_id
        }
        
        return container
    
    async def execute_command(self, user_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in secure container"""
        # Validate command safety
        if not self._is_safe_command(command):
            logger.warning(
                "Unsafe command blocked",
                user_id=user_id,
                command=command
            )
            return {
                "success": False,
                "output": "Error: Command not allowed for security reasons",
                "error": "UNSAFE_COMMAND",
                "command": command
            }
        
        try:
            if self.test_mode:
                execution_time = 0.01
                logger.info(
                    "Mock command executed",
                    user_id=user_id,
                    command=command,
                    success=True,
                    execution_time=execution_time
                )
                return {
                    "success": True,
                    "output": f"[mocked stdout] {command}",
                    "exit_code": 0,
                    "execution_time": execution_time,
                    "command": command
                }

            # Get or create container for user
            container = await self._get_or_create_container(user_id)
            
            # Execute command with timeout
            start_time = time.time()
            
            # Use docker exec to run command
            exec_result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                privileged=False,
                user="1000:1000",
                workdir="/workspace",
                environment={
                    "HOME": "/workspace",
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "SHELL": "/bin/sh"
                }
            )
            
            execution_time = time.time() - start_time
            
            # Parse result
            output = exec_result.output.decode("utf-8") if exec_result.output else ""
            exit_code = exec_result.exit_code
            
            success = exit_code == 0
            
            logger.info(
                "Command executed",
                user_id=user_id,
                command=command,
                success=success,
                exit_code=exit_code,
                execution_time=execution_time,
                output_length=len(output)
            )
            
            return {
                "success": success,
                "output": output,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "Command execution failed",
                user_id=user_id,
                command=command,
                error=str(e)
            )
            
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "error": "EXECUTION_ERROR",
                "command": command
            }
    
    async def cleanup_user_container(self, user_id: str):
        """Clean up container for a specific user"""
        container_name = self._get_container_name(user_id)
        
        if container_name in self.containers:
            try:
                container = self.containers[container_name]["container"]
                container.remove(force=True)
                del self.containers[container_name]
                
                logger.info(
                    "Container cleaned up",
                    user_id=user_id,
                    container_name=container_name
                )
            except Exception as e:
                logger.error(
                    "Failed to cleanup container",
                    user_id=user_id,
                    error=str(e)
                )
    
    async def cleanup_all_containers(self):
        """Clean up all containers"""
        if self.test_mode:
            self.containers.clear()
            return

        for user_id in list(self.containers.keys()):
            await self.cleanup_user_container(user_id)
    
    async def get_container_stats(self) -> Dict[str, Any]:
        """Get statistics about active containers"""
        return {
            "active_containers": len(self.containers),
            "max_containers": self.max_containers,
            "containers": [
                {
                    "user_id": info["user_id"],
                    "container_name": self._get_container_name(info["user_id"]),
                    "created_at": info["created_at"],
                    "uptime": time.time() - info["created_at"]
                }
                for info in self.containers.values()
            ]
        }

# Global secure shell instance
secure_shell = None

async def get_secure_shell() -> SecureShell:
    """Get the global secure shell instance"""
    global secure_shell
    if secure_shell is None:
        secure_shell = SecureShell()
    return secure_shell
