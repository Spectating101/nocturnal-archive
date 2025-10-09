"""
Application settings and configuration
"""

import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key (deprecated - use Groq)")
    anthropic_api_key: str = Field(default="", description="Anthropic API key (deprecated - use Groq)")
    # LLM Providers (all optional; router selects available one)
    groq_api_key: str = Field(default="", description="Groq API key (primary LLM provider)")
    openai_api_keys: List[str] = Field(default_factory=list, description="Optional: multiple OpenAI API keys for rotation")
    mistral_api_keys: List[str] = Field(default_factory=list, description="Optional: multiple Mistral API keys for rotation")
    cohere_api_keys: List[str] = Field(default_factory=list, description="Optional: multiple Cohere API keys for rotation")
    openalex_api_key: str = Field(default="", description="OpenAlex API key")
    
    # Database
    database_url: str = Field(default="", description="Database connection URL")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # App Configuration
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    log_level: str = Field(default="INFO", description="Log level")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Rate Limiting
    rate_limit_per_hour: int = Field(default=100, description="Rate limit per hour")
    rate_limit_burst: int = Field(default=10, description="Rate limit burst")
    
    # Monitoring
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    max_papers_per_request: int = Field(default=50, description="Maximum papers per request")
    max_synthesis_words: int = Field(default=2000, description="Maximum synthesis words")
    
    # LLM Configuration
    default_llm_model: str = Field(default="gpt-3.5-turbo", description="Default LLM model")
    max_tokens: int = Field(default=1000, description="Maximum tokens for LLM responses")
    temperature: float = Field(default=0.7, description="LLM temperature")
    
    # Search Configuration
    default_search_limit: int = Field(default=10, description="Default search result limit")
    max_search_limit: int = Field(default=100, description="Maximum search result limit")
    
    # Cache Configuration
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    enable_caching: bool = Field(default=True, description="Enable caching")
    
    # FinSight Configuration
    finsight_strict: bool = Field(default=True, description="Enable strict mode (no mocks)")
    
    # FinGPT Configuration
    fingpt_base_model: str = Field(default="meta-llama/Llama-3.1-8B-Instruct", description="FinGPT base model")
    fingpt_lora_id: str = Field(default="FinGPT/fingpt-mt_llama2-7b_lora", description="FinGPT LoRA adapter ID")
    fingpt_load_4bit: bool = Field(default=True, description="Load model in 4-bit quantization")
    hf_token: str = Field(default="", description="HuggingFace token for gated models")
    nlp_max_new_tokens: int = Field(default=128, description="Maximum new tokens for NLP generation")
    nlp_temperature: float = Field(default=0.2, description="Temperature for NLP generation")
    nlp_cache_ttl: int = Field(default=900, description="NLP cache TTL in seconds")
    
    # RAG Configuration
    enable_rag: bool = Field(default=False, description="Enable RAG Q&A endpoints")
    db_url: str = Field(default="postgresql+psycopg2://postgres:postgres@localhost:5432/finsight", description="Database URL for RAG")
    rag_embed_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model for RAG")
    rag_top_k: int = Field(default=5, description="Default number of results for RAG search")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()

    # Automatically switch to test mode when running under pytest without needing env vars
    is_test_env = (
        settings.environment.lower() == "test"
        or os.getenv("PYTEST_CURRENT_TEST")
        or os.getenv("PYTEST_ENV")
    )

    if is_test_env:
        settings.environment = "test"
        settings.debug = True
        settings.finsight_strict = False

        # Provide deterministic low rate limits suitable for unit tests unless explicitly overridden
        settings.rate_limit_per_hour = int(os.getenv("NA_TEST_RATE_LIMIT_PER_HOUR", "120"))
        settings.rate_limit_burst = int(os.getenv("NA_TEST_RATE_LIMIT_BURST", "30"))

    return settings
