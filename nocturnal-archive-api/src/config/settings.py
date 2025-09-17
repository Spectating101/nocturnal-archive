"""
Application settings and configuration
"""

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
    openai_api_key: str = Field(..., description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openalex_api_key: str = Field(default="", description="OpenAlex API key")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
