"""
Unified Platform Settings - Combines all three systems
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UnifiedSettings(BaseSettings):
    """Unified platform settings combining FinSight, Archive, and Assistant"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === API Keys ===
    groq_api_key: str = Field(..., description="Groq API key (primary LLM provider)")
    
    # Legacy API keys (deprecated but kept for compatibility)
    openai_api_key: str = Field(default="", description="OpenAI API key (deprecated - use Groq)")
    anthropic_api_key: str = Field(default="", description="Anthropic API key (deprecated - use Groq)")
    mistral_api_key: str = Field(default="", description="Mistral API key (deprecated - use Groq)")
    cerebras_api_key: str = Field(default="", description="Cerebras API key (deprecated - use Groq)")
    cohere_api_key: str = Field(default="", description="Cohere API key (deprecated - use Groq)")
    
    # External APIs
    openalex_api_key: str = Field(default="", description="OpenAlex API key")
    
    # === Database Configuration ===
    database_url: str = Field(..., description="PostgreSQL connection URL")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # === Application Configuration ===
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    log_level: str = Field(default="INFO", description="Log level")
    debug: bool = Field(default=False, description="Debug mode")
    
    # === Rate Limiting ===
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour (increased for unified platform)")
    rate_limit_burst: int = Field(default=50, description="Rate limit burst")
    
    # === Monitoring ===
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")
    
    # === CORS ===
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # === API Configuration ===
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    
    # === Groq Configuration ===
    groq_model_default: str = Field(default="llama-3.1-8b-instant", description="Default Groq model")
    groq_model_synthesis: str = Field(default="llama-3.1-8b-instant", description="Groq model for synthesis")
    groq_model_analysis: str = Field(default="llama-3.1-8b-instant", description="Groq model for analysis")
    groq_max_tokens: int = Field(default=4000, description="Maximum tokens for Groq requests")
    groq_temperature: float = Field(default=0.1, description="Temperature for Groq requests")
    
    # === FinSight Configuration ===
    finsight_enabled: bool = Field(default=True, description="Enable FinSight service")
    finsight_sec_edgar_enabled: bool = Field(default=True, description="Enable SEC EDGAR integration")
    finsight_cache_ttl: int = Field(default=3600, description="FinSight cache TTL in seconds")
    
    # === Archive Configuration ===
    archive_enabled: bool = Field(default=True, description="Enable Archive service")
    archive_mongodb_url: str = Field(default="", description="MongoDB URL for Archive (optional)")
    archive_vector_search_enabled: bool = Field(default=True, description="Enable vector search")
    
    # === Assistant Configuration ===
    assistant_enabled: bool = Field(default=True, description="Enable Assistant service")
    assistant_project_root: str = Field(default=".", description="Default project root for Assistant")
    assistant_safe_mode: bool = Field(default=True, description="Enable safe mode for Assistant")
    
    # === Security ===
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    require_api_key: bool = Field(default=True, description="Require API key for all requests")
    
    # === File System ===
    max_file_size_mb: int = Field(default=5, description="Maximum file size in MB")
    allowed_file_extensions: List[str] = Field(
        default=[".py", ".r", ".sql", ".md", ".txt", ".json", ".csv"],
        description="Allowed file extensions"
    )
    
    # === Performance ===
    max_concurrent_requests: int = Field(default=100, description="Maximum concurrent requests")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # === Feature Flags ===
    enable_rag: bool = Field(default=True, description="Enable RAG (Retrieval-Augmented Generation)")
    enable_vector_search: bool = Field(default=True, description="Enable vector search")
    enable_caching: bool = Field(default=True, description="Enable caching")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    
    # Removed Config class to fix pydantic v2 compatibility


@lru_cache()
def get_settings() -> UnifiedSettings:
    """Get cached settings instance"""
    return UnifiedSettings()


# Backward compatibility
Settings = UnifiedSettings
