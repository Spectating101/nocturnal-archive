"""
Multi-provider LLM service with automatic failover
Supports: Groq (4 keys), Cerebras, Cloudflare, OpenRouter, Together, Fireworks
"""

import os
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import structlog
from groq import Groq
import httpx

logger = structlog.get_logger(__name__)

@dataclass
class ProviderConfig:
    name: str
    keys: List[str]
    endpoint: str
    models: List[str]
    rate_limit_per_day: int
    current_key_index: int = 0

class LLMProviderManager:
    """Manages multiple LLM providers with automatic failover"""
    
    def __init__(self):
        self.providers = self._load_providers()
        self.usage_tracking = {}  # Track usage per key
        
    def _load_providers(self) -> Dict[str, ProviderConfig]:
        """Load all configured providers from environment"""
        
        providers = {}
        
        # Groq (supports 4 keys)
        groq_keys = [
            os.getenv(f'GROQ_API_KEY_{i}') 
            for i in range(1, 5) 
            if os.getenv(f'GROQ_API_KEY_{i}')
        ]
        # Fallback to single key if numbered keys not set
        if not groq_keys and os.getenv('GROQ_API_KEY'):
            groq_keys = [os.getenv('GROQ_API_KEY')]
        
        if groq_keys:
            providers['groq'] = ProviderConfig(
                name='groq',
                keys=groq_keys,
                endpoint='https://api.groq.com/openai/v1/chat/completions',
                models=['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
                rate_limit_per_day=1000  # per key (70B model limit)
            )
        
        # Cerebras (supports multiple keys)
        cerebras_keys = [
            os.getenv(f'CEREBRAS_API_KEY_{i}') 
            for i in range(1, 5) 
            if os.getenv(f'CEREBRAS_API_KEY_{i}')
        ]
        # Fallback to single key if numbered keys not set
        if not cerebras_keys and os.getenv('CEREBRAS_API_KEY'):
            cerebras_keys = [os.getenv('CEREBRAS_API_KEY')]
        
        if cerebras_keys:
            providers['cerebras'] = ProviderConfig(
                name='cerebras',
                keys=cerebras_keys,
                endpoint='https://api.cerebras.ai/v1/chat/completions',
                models=['llama-3.3-70b', 'llama3.1-8b'],
                rate_limit_per_day=14400  # per key (verified from cerebras dashboard)
            )
        
        # Cloudflare Workers AI
        cf_token = os.getenv('CLOUDFLARE_API_TOKEN')
        cf_account = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        if cf_token and cf_account:
            providers['cloudflare'] = ProviderConfig(
                name='cloudflare',
                keys=[cf_token],
                endpoint=f'https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run',
                models=['@cf/meta/llama-3.1-70b-instruct', '@cf/meta/llama-3.1-8b-instruct'],
                rate_limit_per_day=10000
            )
        
        # OpenRouter (free tier)
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            providers['openrouter'] = ProviderConfig(
                name='openrouter',
                keys=[openrouter_key],
                endpoint='https://openrouter.ai/api/v1/chat/completions',
                models=['deepseek/deepseek-r1:free', 'qwen/qwen2.5-7b:free'],
                rate_limit_per_day=1000
            )
        
        # Together AI
        together_key = os.getenv('TOGETHER_API_KEY')
        if together_key:
            providers['together'] = ProviderConfig(
                name='together',
                keys=[together_key],
                endpoint='https://api.together.xyz/v1/chat/completions',
                models=['meta-llama/Llama-3.1-70B-Instruct-Turbo', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
                rate_limit_per_day=100000  # Credit-based, not strict daily limit
            )
        
        # Fireworks AI
        fireworks_key = os.getenv('FIREWORKS_API_KEY')
        if fireworks_key:
            providers['fireworks'] = ProviderConfig(
                name='fireworks',
                keys=[fireworks_key],
                endpoint='https://api.fireworks.ai/inference/v1/chat/completions',
                models=['accounts/fireworks/models/llama-v3p3-70b-instruct'],
                rate_limit_per_day=100000  # Credit-based
            )
        
        logger.info(f"Loaded {len(providers)} LLM providers", providers=list(providers.keys()))
        return providers
    
    def get_next_key(self, provider_name: str) -> Optional[str]:
        """Get next available key for provider (round-robin)"""
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        if not provider.keys:
            return None
        
        # Round-robin through keys
        key = provider.keys[provider.current_key_index]
        provider.current_key_index = (provider.current_key_index + 1) % len(provider.keys)
        
        return key
    
    async def call_provider(
        self, 
        provider_name: str, 
        api_key: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Call a specific provider with given parameters"""
        
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # MODEL MAPPING: Translate model names between providers
        # Cerebras uses 'llama-3.3-70b', Groq uses 'llama-3.3-70b-versatile'
        model_map = {
            'groq': {
                'llama-3.3-70b': 'llama-3.3-70b-versatile',
                'llama3.1-8b': 'llama-3.1-8b-instant'
            },
            'cerebras': {
                'llama-3.3-70b-versatile': 'llama-3.3-70b',
                'llama-3.1-8b-instant': 'llama3.1-8b'
            }
        }
        
        requested_model = model or provider.models[0]
        
        # Map model if needed
        if provider_name in model_map and requested_model in model_map[provider_name]:
            model_to_use = model_map[provider_name][requested_model]
        else:
            model_to_use = requested_model
        
        try:
            if provider_name in ['groq', 'cerebras', 'openrouter', 'together', 'fireworks']:
                # OpenAI-compatible providers
                return await self._call_openai_compatible(
                    endpoint=provider.endpoint,
                    api_key=api_key,
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    provider_name=provider_name
                )
            
            elif provider_name == 'cloudflare':
                return await self._call_cloudflare(
                    api_key=api_key,
                    model=model_to_use,
                    messages=messages,
                    max_tokens=max_tokens
                )
            
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")
                
        except Exception as e:
            logger.error(f"{provider_name} call failed", error=str(e))
            raise
    
    async def _call_openai_compatible(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        provider_name: str
    ) -> Dict[str, Any]:
        """Call OpenAI-compatible API"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded")
            elif response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            return {
                'content': data['choices'][0]['message']['content'],
                'tokens': data.get('usage', {}).get('total_tokens', 0),
                'model': model,
                'provider': provider_name
            }
    
    async def _call_cloudflare(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call Cloudflare Workers AI"""
        
        account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        endpoint = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}'
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            return {
                'content': data['result']['response'],
                'tokens': data['result'].get('tokens_used', 0),
                'model': model,
                'provider': 'cloudflare'
            }
    
    async def query_with_fallback(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        messages: Optional[List[Dict[str, str]]] = None,  # ← NEW: Accept pre-built messages
        model: Optional[str] = None,
        temperature: float = 0.2,  # CHANGED: Low temp for factual accuracy
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Try providers in priority order until one succeeds
        Priority: cerebras (14.4K RPD) → groq (1K RPD) → cloudflare → openrouter → together → fireworks
        """
        
        # Use pre-built messages if provided, otherwise build from query
        if messages:
            pass  # Use the provided messages as-is
        elif conversation_history:
            messages = conversation_history + [{"role": "user", "content": query}]
        else:
            messages = [{"role": "user", "content": query}]
        
        # Try providers in order (Cerebras first - highest rate limit)
        provider_priority = ['cerebras', 'groq', 'cloudflare', 'openrouter', 'together', 'fireworks']
        
        for provider_name in provider_priority:
            if provider_name not in self.providers:
                continue  # Skip if not configured
            
            provider = self.providers[provider_name]
            
            # Try each key for this provider
            for _ in range(len(provider.keys)):
                key = self.get_next_key(provider_name)
                if not key:
                    continue
                
                try:
                    logger.info(f"Trying {provider_name}", key_preview=key[:10])
                    
                    result = await self.call_provider(
                        provider_name=provider_name,
                        api_key=key,
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    logger.info(
                        f"Success with {provider_name}",
                        tokens=result['tokens'],
                        model=result['model']
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.warning(
                        f"{provider_name} failed, trying next",
                        error=str(e)[:100]
                    )
                    continue
        
        # All providers failed
        raise Exception("All LLM providers are unavailable")

# Global instance
_provider_manager = None

def get_provider_manager() -> LLMProviderManager:
    """Get singleton provider manager"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = LLMProviderManager()
    return _provider_manager

