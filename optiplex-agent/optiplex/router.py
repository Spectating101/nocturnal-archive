"""Smart model routing based on task complexity"""
from typing import Optional, Dict, Any
import re


class ModelRouter:
    """Intelligently route requests to appropriate models"""

    # Task complexity indicators
    HEAVY_KEYWORDS = [
        "refactor", "architect", "design", "optimize", "analyze",
        "debug complex", "large codebase", "multi-file", "system design",
        "performance", "scale", "entire project", "full rewrite"
    ]

    CODING_KEYWORDS = [
        "implement", "write function", "create class", "build feature",
        "add method", "code", "program", "algorithm", "data structure"
    ]

    SIMPLE_KEYWORDS = [
        "explain", "what is", "how does", "show me", "list",
        "status", "diff", "read file", "simple fix", "quick"
    ]

    def __init__(self, default_model: str = "llama-3.3-70b"):
        self.default_model = default_model
        self.model_tiers = {
            "heavy": "qwen-3-coder-480b",      # 480B coding specialist
            "coding": "qwen-3-32b",            # 32B fast coding
            "general": "llama-3.3-70b",        # 70B general purpose
            "simple": "llama-4-scout-17b"      # 17B lightweight
        }

    def detect_complexity(self, message: str) -> str:
        """Detect task complexity from user message"""
        message_lower = message.lower()

        # Check for heavy tasks
        for keyword in self.HEAVY_KEYWORDS:
            if keyword in message_lower:
                return "heavy"

        # Check for coding tasks
        for keyword in self.CODING_KEYWORDS:
            if keyword in message_lower:
                return "coding"

        # Check for simple tasks
        for keyword in self.SIMPLE_KEYWORDS:
            if keyword in message_lower:
                return "simple"

        # Check message length as complexity indicator
        if len(message.split()) > 50:
            return "heavy"
        elif len(message.split()) < 10:
            return "simple"

        # Default to general
        return "general"

    def route(
        self,
        message: str,
        context_files: Optional[list] = None,
        conversation_length: int = 0
    ) -> Dict[str, Any]:
        """Route request to appropriate model"""

        complexity = self.detect_complexity(message)

        # Adjust based on context
        if context_files and len(context_files) > 5:
            complexity = "heavy"

        if conversation_length > 20:
            # Long conversations need better models
            if complexity == "simple":
                complexity = "general"

        selected_model = self.model_tiers.get(complexity, self.default_model)

        return {
            "model": selected_model,
            "complexity": complexity,
            "reason": self._get_reason(complexity, context_files, conversation_length)
        }

    def _get_reason(
        self,
        complexity: str,
        context_files: Optional[list],
        conversation_length: int
    ) -> str:
        """Get human-readable reason for model selection"""
        reasons = []

        if complexity == "heavy":
            reasons.append("Complex task detected")
        elif complexity == "coding":
            reasons.append("Coding task")
        elif complexity == "simple":
            reasons.append("Simple query")
        else:
            reasons.append("General task")

        if context_files and len(context_files) > 5:
            reasons.append(f"{len(context_files)} context files")

        if conversation_length > 20:
            reasons.append("Long conversation")

        return " - ".join(reasons)

    def override_model(self, model_name: str):
        """Override automatic routing with specific model"""
        self.default_model = model_name

    def set_tier_model(self, tier: str, model_name: str):
        """Customize model for a specific tier"""
        if tier in self.model_tiers:
            self.model_tiers[tier] = model_name


class AdaptiveAgent:
    """Agent that adapts model selection based on task"""

    def __init__(self, agent, enable_routing: bool = True):
        self.agent = agent
        self.router = ModelRouter(agent.model_config.name)
        self.enable_routing = enable_routing
        self.routing_history = []

    def chat(self, message: str, context_files: Optional[list] = None):
        """Chat with automatic model routing"""

        if self.enable_routing:
            # Get routing decision
            routing = self.router.route(
                message,
                context_files,
                len(self.agent.conversation_history)
            )

            # Switch model if different
            if routing["model"] != self.agent.model_config.name:
                print(f"🔄 Switching to {routing['model']} ({routing['reason']})")
                # Store current model
                original_model = self.agent.model_config.name

                # Update agent's model config
                from .config import OptiplexConfig
                self.agent.model_config = OptiplexConfig.get_model(routing["model"])

            # Track routing decision
            self.routing_history.append({
                "message_preview": message[:50],
                "selected_model": routing["model"],
                "complexity": routing["complexity"],
                "reason": routing["reason"]
            })

        # Execute chat
        response = self.agent.chat(message, context_files)

        return response

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics on model routing"""
        if not self.routing_history:
            return {"total_requests": 0}

        model_counts = {}
        complexity_counts = {}

        for entry in self.routing_history:
            model = entry["selected_model"]
            complexity = entry["complexity"]

            model_counts[model] = model_counts.get(model, 0) + 1
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

        return {
            "total_requests": len(self.routing_history),
            "model_usage": model_counts,
            "complexity_distribution": complexity_counts,
            "last_10": self.routing_history[-10:]
        }

    def enable_auto_routing(self):
        """Enable automatic model routing"""
        self.enable_routing = True

    def disable_auto_routing(self):
        """Disable automatic model routing"""
        self.enable_routing = False
