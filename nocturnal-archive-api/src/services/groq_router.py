"""
Groq Model Router - Capability-aware model selection for different task types.
Routes to appropriate Groq model based on task complexity and requirements.
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from groq import Groq, AsyncGroq

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels that map to model capabilities."""
    LITE = "lite"        # Lookup, grep, quote, simple Q&A (≤300 tokens)
    MEDIUM = "medium"    # Code explain, short synthesis (≤800 tokens)  
    HEAVY = "heavy"      # Multi-doc synthesis, reasoning, safety-critical (≥800 tokens)


class GroqModel(Enum):
    """Available Groq models with their capabilities."""
    LLAMA3_8B_INSTANT = "llama-3.1-8b-instant"     # Fast, cheap, good for lite tasks
    GEMMA2_9B = "gemma2-9b-it"                     # Alternative lite model
    LLAMA3_70B_VERSATILE = "llama-3.3-70b-versatile"  # Most capable, for heavy tasks


@dataclass
class ModelCapability:
    """Model capability profile."""
    model: GroqModel
    max_tokens: int
    cost_per_1k: float  # Relative cost
    latency_tier: str   # "fast", "medium", "slow"
    recommended_for: List[TaskComplexity]


# Model capability matrix
MODEL_CAPABILITIES = {
    GroqModel.LLAMA3_8B_INSTANT: ModelCapability(
        model=GroqModel.LLAMA3_8B_INSTANT,
        max_tokens=8192,
        cost_per_1k=0.1,
        latency_tier="fast",
        recommended_for=[TaskComplexity.LITE]
    ),
    GroqModel.GEMMA2_9B: ModelCapability(
        model=GroqModel.GEMMA2_9B,
        max_tokens=8192,
        cost_per_1k=0.15,
        latency_tier="fast",
        recommended_for=[TaskComplexity.LITE, TaskComplexity.MEDIUM]
    ),
    GroqModel.LLAMA3_70B_VERSATILE: ModelCapability(
        model=GroqModel.LLAMA3_70B_VERSATILE,
        max_tokens=8192,
        cost_per_1k=1.0,
        latency_tier="slow",
        recommended_for=[TaskComplexity.LITE, TaskComplexity.MEDIUM, TaskComplexity.HEAVY]
    )
}


@dataclass
class RoutingDecision:
    """Result of model routing decision."""
    model: GroqModel
    complexity: TaskComplexity
    reasoning: str
    estimated_tokens: int
    fallback_available: bool = True


class GroqModelRouter:
    """Routes tasks to appropriate Groq models based on complexity and requirements."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncGroq(api_key=api_key)
        self.model_availability = {}  # Cache model availability
        self._last_availability_check = 0
        
    async def classify_task_complexity(
        self,
        task_type: str,
        input_size: int = 0,
        output_requirements: Dict[str, Any] = None
    ) -> TaskComplexity:
        """Classify task complexity based on requirements."""
        output_requirements = output_requirements or {}
        
        # Extract key requirements
        max_words = output_requirements.get('max_words', 0)
        paper_count = output_requirements.get('paper_count', 1)
        requires_reasoning = output_requirements.get('requires_reasoning', False)
        safety_critical = output_requirements.get('safety_critical', False)
        
        # Estimate output tokens (rough: 1 word ≈ 1.3 tokens)
        estimated_output_tokens = int(max_words * 1.3)
        
        # Classification logic
        if (task_type in ['lookup', 'grep', 'quote', 'simple_qa'] or 
            estimated_output_tokens <= 300 or
            (paper_count == 1 and max_words <= 200)):
            return TaskComplexity.LITE
            
        elif (task_type in ['code_explain', 'short_synthesis'] or
              estimated_output_tokens <= 800 or
              (paper_count <= 3 and max_words <= 500)):
            return TaskComplexity.MEDIUM
            
        else:
            return TaskComplexity.HEAVY
    
    async def select_model(
        self,
        complexity: TaskComplexity,
        strict_mode: bool = False,
        preferred_model: Optional[GroqModel] = None
    ) -> RoutingDecision:
        """Select appropriate model for task complexity."""
        
        # Check model availability
        await self._check_model_availability()
        
        # If preferred model is specified and available, use it
        if preferred_model and self.model_availability.get(preferred_model.value, False):
            capability = MODEL_CAPABILITIES[preferred_model]
            if complexity in capability.recommended_for:
                return RoutingDecision(
                    model=preferred_model,
                    complexity=complexity,
                    reasoning=f"Using preferred model {preferred_model.value}",
                    estimated_tokens=capability.max_tokens
                )
        
        # Find best available model for complexity
        suitable_models = []
        for model, capability in MODEL_CAPABILITIES.items():
            if (complexity in capability.recommended_for and 
                self.model_availability.get(model.value, False)):
                suitable_models.append((model, capability))
        
        if not suitable_models:
            if strict_mode:
                raise RuntimeError(f"No suitable models available for {complexity.value} tasks")
            
            # Fallback to any available model
            for model, capability in MODEL_CAPABILITIES.items():
                if self.model_availability.get(model.value, False):
                    return RoutingDecision(
                        model=model,
                        complexity=complexity,
                        reasoning=f"Fallback to {model.value} (not optimal for {complexity.value})",
                        estimated_tokens=capability.max_tokens,
                        fallback_available=False
                    )
            
            raise RuntimeError("No Groq models available")
        
        # Select best model (prefer faster/cheaper for same capability)
        best_model, best_capability = min(suitable_models, key=lambda x: x[1].cost_per_1k)
        
        return RoutingDecision(
            model=best_model,
            complexity=complexity,
            reasoning=f"Selected {best_model.value} for {complexity.value} task (cost: {best_capability.cost_per_1k})",
            estimated_tokens=best_capability.max_tokens
        )
    
    async def _check_model_availability(self, force_refresh: bool = False):
        """Check which models are available (with caching)."""
        import time
        
        # Cache for 5 minutes
        if (not force_refresh and 
            time.time() - self._last_availability_check < 300 and 
            self.model_availability):
            return
        
        self.model_availability = {}
        
        for model in GroqModel:
            try:
                # Test with a minimal request
                response = await self.client.chat.completions.create(
                    model=model.value,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                    timeout=5.0
                )
                self.model_availability[model.value] = True
                logger.debug(f"Model {model.value} is available")
                
            except Exception as e:
                self.model_availability[model.value] = False
                logger.warning(f"Model {model.value} unavailable: {e}")
        
        self._last_availability_check = time.time()
    
    async def generate_with_routing(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "general",
        output_requirements: Dict[str, Any] = None,
        strict_mode: bool = False,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using capability-aware routing."""
        
        # Classify task and select model
        complexity = await self.classify_task_complexity(task_type, output_requirements=output_requirements)
        decision = await self.select_model(complexity, strict_mode=strict_mode)
        
        # Prepare generation parameters
        capability = MODEL_CAPABILITIES[decision.model]
        max_tokens = min(
            kwargs.get('max_tokens', 1000),
            capability.max_tokens - 100  # Leave buffer
        )
        
        # Generate response
        try:
            response = await self.client.chat.completions.create(
                model=decision.model.value,
                messages=messages,
                max_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            )
            
            content = response.choices[0].message.content
            usage = response.usage.dict() if response.usage else {}
            
            # Add routing metadata
            metadata = {
                "routing_decision": {
                    "model": decision.model.value,
                    "complexity": decision.complexity.value,
                    "reasoning": decision.reasoning,
                    "estimated_tokens": decision.estimated_tokens,
                    "fallback_used": not decision.fallback_available
                },
                "usage": usage,
                "capability": {
                    "max_tokens": capability.max_tokens,
                    "cost_tier": capability.cost_per_1k,
                    "latency_tier": capability.latency_tier
                }
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Generation failed with {decision.model.value}: {e}")
            
            if strict_mode:
                raise
            
            # Try fallback to lighter model
            if decision.complexity != TaskComplexity.LITE:
                fallback_complexity = TaskComplexity.LITE
                fallback_decision = await self.select_model(fallback_complexity, strict_mode=False)
                
                logger.info(f"Falling back to {fallback_decision.model.value}")
                return await self.generate_with_routing(
                    messages, task_type, output_requirements, 
                    strict_mode=False, **kwargs
                )
            
            raise


# Convenience function for easy integration
async def get_groq_router(api_key: str) -> GroqModelRouter:
    """Get configured Groq model router."""
    router = GroqModelRouter(api_key)
    await router._check_model_availability()
    return router
