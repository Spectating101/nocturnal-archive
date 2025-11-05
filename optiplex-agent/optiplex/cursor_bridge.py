"""Bridge to continue work from Cursor when it hits token limits"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import json


class CursorContinuation:
    """Read Cursor context and continue work when Cursor dies from token limits"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.cursor_dir = self.project_path / ".cursor"
        self.vscode_dir = self.project_path / ".vscode"
    
    def can_continue_from_cursor(self) -> bool:
        """Check if there's Cursor context to continue from"""
        return self.cursor_dir.exists() or self.vscode_dir.exists()
    
    def extract_cursor_context(self) -> Optional[Dict[str, Any]]:
        """Extract what you were working on in Cursor"""
        
        context = {
            "last_session": None,
            "open_files": [],
            "recent_edits": [],
            "cursor_instructions": None,
            "inferred_task": None
        }
        
        # Try to read Cursor chat history
        chat_history = self._read_cursor_chats()
        if chat_history:
            context["cursor_instructions"] = chat_history[-1] if chat_history else None
            context["inferred_task"] = self._infer_task_from_chat(chat_history)
        
        # Read workspace state
        workspace_state = self._read_workspace_state()
        if workspace_state:
            context["open_files"] = workspace_state.get("open_files", [])
        
        # Check git for recent uncommitted changes (likely what Cursor was working on)
        context["recent_edits"] = self._get_recent_uncommitted_files()
        
        return context if any(context.values()) else None
    
    def _read_cursor_chats(self) -> List[str]:
        """Try to read Cursor chat history"""
        
        chats = []
        
        # Cursor stores chats in various places, try common locations
        possible_chat_files = [
            self.cursor_dir / "chats.json",
            self.cursor_dir / "chat_history.json",
            Path.home() / ".cursor" / "chats" / f"{self.project_path.name}.json"
        ]
        
        for chat_file in possible_chat_files:
            if chat_file.exists():
                try:
                    with open(chat_file, 'r') as f:
                        data = json.load(f)
                        
                        # Extract chat messages
                        if isinstance(data, list):
                            chats.extend([msg.get("content", "") for msg in data if "content" in msg])
                        elif isinstance(data, dict):
                            messages = data.get("messages", [])
                            chats.extend([msg.get("content", "") for msg in messages if "content" in msg])
                except Exception:
                    pass
        
        return chats
    
    def _read_workspace_state(self) -> Optional[Dict]:
        """Read VSCode/Cursor workspace state"""
        
        state_file = self.vscode_dir / "workspace.code-workspace"
        if not state_file.exists():
            state_file = self.cursor_dir / "workspace.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def _get_recent_uncommitted_files(self) -> List[str]:
        """Get files modified but not committed (likely Cursor's work)"""
        
        import subprocess
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception:
            pass
        
        return []
    
    def _infer_task_from_chat(self, chat_history: List[str]) -> Optional[str]:
        """Infer what task you were working on from chat"""
        
        if not chat_history:
            return None
        
        # Get last user message (your instruction to Cursor)
        user_messages = [msg for msg in chat_history if msg and not msg.startswith("I'll")]
        
        if user_messages:
            last_instruction = user_messages[-1]
            
            # Extract task intent
            task_keywords = {
                "add": "Adding feature",
                "fix": "Fixing bug",
                "refactor": "Refactoring code",
                "implement": "Implementing feature",
                "create": "Creating new component",
                "update": "Updating existing code",
                "test": "Adding tests",
                "deploy": "Setting up deployment"
            }
            
            for keyword, task_type in task_keywords.items():
                if keyword in last_instruction.lower():
                    return f"{task_type}: {last_instruction[:100]}"
            
            return f"Working on: {last_instruction[:100]}"
        
        return None
    
    def generate_continuation_prompt(self) -> Optional[str]:
        """Generate a prompt to continue Cursor's work"""
        
        context = self.extract_cursor_context()
        if not context:
            return None
        
        prompt_parts = []
        
        # Add inferred task
        if context.get("inferred_task"):
            prompt_parts.append(f"CONTEXT: User was working on: {context['inferred_task']}")
        
        # Add open files
        if context.get("open_files"):
            prompt_parts.append(f"\nFILES IN FOCUS: {', '.join(context['open_files'][:5])}")
        
        # Add recent edits
        if context.get("recent_edits"):
            prompt_parts.append(f"\nRECENT CHANGES: {', '.join(context['recent_edits'][:5])}")
        
        # Add cursor instructions
        if context.get("cursor_instructions"):
            prompt_parts.append(f"\nLAST INSTRUCTION: {context['cursor_instructions'][:200]}")
        
        if prompt_parts:
            prompt_parts.append("\n\nTASK: Continue this work. Complete what was started, handle edge cases, add tests if needed.")
            return '\n'.join(prompt_parts)
        
        return None


def check_cursor_continuation(project_path: Path) -> Optional[str]:
    """Quick check if we can continue from Cursor"""
    
    bridge = CursorContinuation(project_path)
    
    if bridge.can_continue_from_cursor():
        prompt = bridge.generate_continuation_prompt()
        if prompt:
            return prompt
    
    return None


