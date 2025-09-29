#!/usr/bin/env python3
"""
Hybrid Model Router - Smart routing with auto-escalation
Implements GPT's recommended strategy for token efficiency
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    LOCAL = "local"      # No LLM calls
    EIGHT_B = "8B"       # Fast, cheap model
    THIRTY_TWO_B = "32B" # Balanced model
    SEVENTY_B = "70B"    # High-quality model

@dataclass
class TaskComplexity:
    steps: int
    topics: int
    has_comparison: bool
    has_conflicts: bool
    confidence: float
    is_urgent: bool

class HybridRouter:
    """Smart routing system with auto-escalation triggers"""
    
    def __init__(self):
        self.model_configs = {
            ModelTier.LOCAL: {"tokens_per_call": 0, "cost_factor": 0},
            ModelTier.EIGHT_B: {"tokens_per_call": 200, "cost_factor": 1},
            ModelTier.THIRTY_TWO_B: {"tokens_per_call": 400, "cost_factor": 2},
            ModelTier.SEVENTY_B: {"tokens_per_call": 800, "cost_factor": 4}
        }
        
        # Auto-escalation triggers
        self.escalation_triggers = {
            "max_steps": 3,
            "min_confidence": 0.75,
            "comparison_keywords": ["compare", "versus", "vs", "against", "difference"],
            "complex_keywords": ["analyze", "synthesize", "recommend", "strategy"],
            "urgent_keywords": ["urgent", "exam", "paid", "critical"]
        }
    
    def analyze_task_complexity(self, query: str, context: Dict[str, Any] = None) -> TaskComplexity:
        """Analyze task complexity to determine routing needs"""
        
        # Count steps (rough heuristic)
        steps = len(re.findall(r'(?:then|next|after|followed by|step)', query.lower())) + 1
        
        # Count topics
        topics = len(re.findall(r'(?:and|also|additionally|furthermore)', query.lower())) + 1
        
        # Check for comparisons
        has_comparison = any(keyword in query.lower() for keyword in self.escalation_triggers["comparison_keywords"])
        
        # Check for complex operations
        has_complex = any(keyword in query.lower() for keyword in self.escalation_triggers["complex_keywords"])
        
        # Check for urgency
        is_urgent = any(keyword in query.lower() for keyword in self.escalation_triggers["urgent_keywords"])
        
        # Estimate confidence (simplified)
        confidence = 0.8
        if has_comparison or has_complex:
            confidence -= 0.1
        if steps > 2:
            confidence -= 0.1
        if topics > 1:
            confidence -= 0.1
        
        # Check for conflicts in context
        has_conflicts = False
        if context and "conflicts" in context:
            has_conflicts = context["conflicts"]
        
        return TaskComplexity(
            steps=steps,
            topics=topics,
            has_comparison=has_comparison,
            has_conflicts=has_conflicts,
            confidence=max(0.0, min(1.0, confidence)),
            is_urgent=is_urgent
        )
    
    def should_escalate(self, complexity: TaskComplexity) -> bool:
        """Determine if task should be escalated to 70B"""
        
        # Auto-escalation triggers
        if complexity.steps > self.escalation_triggers["max_steps"]:
            logger.info(f"Escalating: {complexity.steps} steps > {self.escalation_triggers['max_steps']}")
            return True
        
        if complexity.confidence < self.escalation_triggers["min_confidence"]:
            logger.info(f"Escalating: confidence {complexity.confidence:.2f} < {self.escalation_triggers['min_confidence']}")
            return True
        
        if complexity.has_comparison:
            logger.info("Escalating: comparison detected")
            return True
        
        if complexity.has_conflicts:
            logger.info("Escalating: conflicts detected")
            return True
        
        if complexity.is_urgent:
            logger.info("Escalating: urgent task")
            return True
        
        return False
    
    def route_task(self, task_type: str, query: str, context: Dict[str, Any] = None) -> Tuple[ModelTier, str]:
        """Route task to appropriate model tier"""
        
        complexity = self.analyze_task_complexity(query, context)
        
        # Auto-escalation check
        if self.should_escalate(complexity):
            return ModelTier.SEVENTY_B, "escalated"
        
        # Task-specific routing
        if task_type == "memory_summary":
            return ModelTier.LOCAL, "local_summary"
        
        elif task_type == "memory_retrieval":
            return ModelTier.LOCAL, "local_retrieval"
        
        elif task_type == "basic_planning":
            if complexity.steps <= 2:
                return ModelTier.EIGHT_B, "simple_planning"
            else:
                return ModelTier.SEVENTY_B, "complex_planning"
        
        elif task_type == "criticism":
            return ModelTier.EIGHT_B, "basic_criticism"
        
        elif task_type == "template_match":
            return ModelTier.LOCAL, "template_execution"
        
        elif task_type == "synthesis":
            return ModelTier.SEVENTY_B, "complex_synthesis"
        
        elif task_type == "tool_orchestration":
            return ModelTier.SEVENTY_B, "complex_orchestration"
        
        else:
            # Default routing
            if complexity.steps <= 2 and complexity.confidence >= 0.8:
                return ModelTier.THIRTY_TWO_B, "balanced_default"
            else:
                return ModelTier.SEVENTY_B, "complex_default"
    
    def estimate_tokens(self, model_tier: ModelTier, task_type: str) -> int:
        """Estimate token usage for a task"""
        base_tokens = self.model_configs[model_tier]["tokens_per_call"]
        
        # Adjust based on task type
        if task_type in ["synthesis", "orchestration"]:
            return base_tokens * 2
        elif task_type in ["planning", "criticism"]:
            return base_tokens
        else:
            return base_tokens
    
    def get_routing_summary(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comprehensive routing analysis"""
        complexity = self.analyze_task_complexity(query, context)
        
        # Determine routing for different task types
        routings = {}
        task_types = ["memory_summary", "basic_planning", "criticism", "synthesis", "tool_orchestration"]
        
        for task_type in task_types:
            model_tier, reason = self.route_task(task_type, query, context)
            tokens = self.estimate_tokens(model_tier, task_type)
            routings[task_type] = {
                "model": model_tier.value,
                "reason": reason,
                "estimated_tokens": tokens
            }
        
        total_tokens = sum(r["estimated_tokens"] for r in routings.values())
        
        return {
            "complexity": {
                "steps": complexity.steps,
                "topics": complexity.topics,
                "has_comparison": complexity.has_comparison,
                "has_conflicts": complexity.has_conflicts,
                "confidence": complexity.confidence,
                "is_urgent": complexity.is_urgent
            },
            "routings": routings,
            "total_estimated_tokens": total_tokens,
            "escalation_triggered": self.should_escalate(complexity)
        }

# Example usage and testing
if __name__ == "__main__":
    router = HybridRouter()
    
    test_queries = [
        "Calculate mean of [1,2,3,4,5]",
        "Compare Tesla vs Apple financial performance",
        "Go to cm522 directory, read README, then research econometrics papers",
        "What did we discuss about Tesla?",
        "Analyze the data and create a comprehensive report"
    ]
    
    print("🧠 HYBRID ROUTER TEST")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        summary = router.get_routing_summary(query)
        
        print(f"  Complexity: {summary['complexity']['steps']} steps, {summary['complexity']['confidence']:.2f} confidence")
        print(f"  Escalation: {'YES' if summary['escalation_triggered'] else 'NO'}")
        print(f"  Total tokens: {summary['total_estimated_tokens']}")
        
        for task_type, routing in summary['routings'].items():
            if routing['estimated_tokens'] > 0:
                print(f"    {task_type}: {routing['model']} ({routing['reason']}) - {routing['estimated_tokens']} tokens")
