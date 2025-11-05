"""Conversation persistence for Optiplex Agent"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationStore:
    """Store and retrieve conversation history"""

    def __init__(self, storage_dir: str = ".optiplex/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save conversation to disk"""
        try:
            filepath = self.storage_dir / f"{conversation_id}.json"

            data = {
                "id": conversation_id,
                "messages": messages,
                "metadata": metadata or {},
                "updated_at": datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation from disk"""
        try:
            filepath = self.storage_dir / f"{conversation_id}.json"

            if not filepath.exists():
                return None

            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return None

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations"""
        conversations = []

        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    conversations.append({
                        "id": data.get("id"),
                        "message_count": len(data.get("messages", [])),
                        "updated_at": data.get("updated_at"),
                        "metadata": data.get("metadata", {})
                    })
            except:
                continue

        return sorted(conversations, key=lambda x: x.get("updated_at", ""), reverse=True)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            filepath = self.storage_dir / f"{conversation_id}.json"
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    def auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled"""
        config_file = self.storage_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("auto_save", True)
            except:
                pass
        return True

    def set_auto_save(self, enabled: bool):
        """Enable or disable auto-save"""
        config_file = self.storage_dir / "config.json"
        try:
            config = {"auto_save": enabled}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error setting auto-save: {e}")


class SessionManager:
    """Manage agent sessions"""

    def __init__(self, storage_dir: str = ".optiplex/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        model: str,
        root_dir: str,
        prompt_type: str = "default"
    ) -> str:
        """Create a new session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        session_data = {
            "id": session_id,
            "model": model,
            "root_dir": root_dir,
            "prompt_type": prompt_type,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }

        filepath = self.storage_dir / f"{session_id}.json"
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

        return session_id

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data"""
        filepath = self.storage_dir / f"{session_id}.json"

        if filepath.exists():
            with open(filepath, 'r') as f:
                session_data = json.load(f)

            session_data.update(updates)
            session_data["last_active"] = datetime.now().isoformat()

            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        filepath = self.storage_dir / f"{session_id}.json"

        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return None

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions"""
        sessions = []

        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    sessions.append(json.load(f))
            except:
                continue

        sessions.sort(key=lambda x: x.get("last_active", ""), reverse=True)
        return sessions[:limit]
