"""
Unified Configuration for Nocturnal Platform
Combines FinSight, Archive, and R/SQL Assistant configurations
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Unified application settings for all modules"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =============================================================================
    # GROQ CONFIGURATION (Unified LLM Provider)
    # =============================================================================
    groq_api_key_1: str = Field(default="", description="Primary Groq API key")
    groq_api_key_2: str = Field(default="", description="Secondary Groq API key")
    groq_api_key_3: str = Field(default="", description="Tertiary Groq API key")
    groq_default_model: str = Field(default="llama-3.1-70b-versatile", description="Default Groq model")
    
    # Groq API Key Limits (per key)
    groq_daily_limit: int = Field(default=14400, description="Daily request limit per key")
    groq_rate_limit: int = Field(default=30, description="Rate limit per minute per key")
    
    # =============================================================================
    # DATABASE CONFIGURATION (PostgreSQL for all modules)
    # =============================================================================
    database_url: str = Field(default="postgresql://localhost:5432/nocturnal_platform", description="PostgreSQL connection URL")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    log_level: str = Field(default="INFO", description="Log level")
    debug: bool = Field(default=False, description="Debug mode")
    
    # =============================================================================
    # RATE LIMITING & SECURITY
    # =============================================================================
    rate_limit_per_hour: int = Field(default=100, description="Rate limit per hour per user")
    rate_limit_burst: int = Field(default=10, description="Rate limit burst allowance")
    admin_key: str = Field(default="admin-key-change-me", description="Admin API key")
    
    # =============================================================================
    # MONITORING & OBSERVABILITY
    # =============================================================================
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # =============================================================================
    # CORS & SECURITY
    # =============================================================================
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8000, description="Server port")
    server_workers: int = Field(default=1, description="Number of server workers")
    
    # =============================================================================
    # FINSIGHT MODULE CONFIGURATION
    # =============================================================================
    finsight_enabled: bool = Field(default=True, description="Enable FinSight module")
    finsight_strict: bool = Field(default=False, description="Enable strict mode (no mocks)")
    
    # SEC EDGAR Configuration
    sec_edgar_base_url: str = Field(default="https://data.sec.gov", description="SEC EDGAR base URL")
    sec_edgar_user_agent: str = Field(default="Nocturnal Platform (contact@example.com)", description="SEC EDGAR user agent")
    
    # Financial Data Limits
    max_financial_requests_per_hour: int = Field(default=50, description="Max financial data requests per hour")
    
    # =============================================================================
    # ARCHIVE MODULE CONFIGURATION
    # =============================================================================
    archive_enabled: bool = Field(default=True, description="Enable Archive module")
    
    # Research Data Limits
    max_papers_per_request: int = Field(default=50, description="Maximum papers per request")
    max_synthesis_words: int = Field(default=2000, description="Maximum synthesis words")
    default_search_limit: int = Field(default=10, description="Default search result limit")
    max_search_limit: int = Field(default=100, description="Maximum search result limit")
    
    # OpenAlex Configuration
    openalex_api_key: str = Field(default="", description="OpenAlex API key (optional)")
    openalex_base_url: str = Field(default="https://api.openalex.org", description="OpenAlex base URL")
    
    # =============================================================================
    # ASSISTANT MODULE CONFIGURATION
    # =============================================================================
    assistant_enabled: bool = Field(default=True, description="Enable Assistant module")
    
    # R/SQL Assistant Configuration
    assistant_server_url: str = Field(default="http://localhost:8000", description="Assistant server URL")
    max_assistant_requests_per_hour: int = Field(default=200, description="Max assistant requests per hour")
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    enable_caching: bool = Field(default=True, description="Enable caching")
    
    # Module-specific cache TTLs
    finsight_cache_ttl: int = Field(default=7200, description="FinSight cache TTL (2 hours)")
    archive_cache_ttl: int = Field(default=1800, description="Archive cache TTL (30 minutes)")
    assistant_cache_ttl: int = Field(default=900, description="Assistant cache TTL (15 minutes)")
    
    # =============================================================================
    # LLM CONFIGURATION (Groq-specific)
    # =============================================================================
    default_temperature: float = Field(default=0.7, description="Default LLM temperature")
    default_max_tokens: int = Field(default=1000, description="Default max tokens")
    
    # Module-specific LLM settings
    finsight_temperature: float = Field(default=0.3, description="FinSight LLM temperature")
    finsight_max_tokens: int = Field(default=1500, description="FinSight max tokens")
    
    archive_temperature: float = Field(default=0.4, description="Archive LLM temperature")
    archive_max_tokens: int = Field(default=2000, description="Archive max tokens")
    
    assistant_temperature: float = Field(default=0.5, description="Assistant LLM temperature")
    assistant_max_tokens: int = Field(default=1200, description="Assistant max tokens")
    
    # =============================================================================
    # DEPLOYMENT CONFIGURATION
    # =============================================================================
    # Railway deployment
    railway_environment: str = Field(default="production", description="Railway environment")
    
    # Health check configuration
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    enable_cross_module_search: bool = Field(default=True, description="Enable cross-module search")
    enable_unified_dashboard: bool = Field(default=True, description="Enable unified dashboard")
    enable_beta_features: bool = Field(default=True, description="Enable beta features")
    
    # =============================================================================
    # BETA LAUNCH CONFIGURATION
    # =============================================================================
    beta_launch_date: str = Field(default="2025-09-30", description="Beta launch date")
    max_beta_users: int = Field(default=100, description="Maximum beta users")
    beta_user_limit_per_hour: int = Field(default=50, description="Beta user rate limit per hour")
    
    def get_groq_api_keys(self) -> List[str]:
        """Get list of configured Groq API keys"""
        keys = []
        for key in [self.groq_api_key_1, self.groq_api_key_2, self.groq_api_key_3]:
            if key and key.strip():
                keys.append(key.strip())
        return keys
    
    def is_module_enabled(self, module: str) -> bool:
        """Check if a module is enabled"""
        module_flags = {
            "finsight": self.finsight_enabled,
            "archive": self.archive_enabled,
            "assistant": self.assistant_enabled
        }
        return module_flags.get(module, False)
    
    def get_module_cache_ttl(self, module: str) -> int:
        """Get cache TTL for a specific module"""
        module_ttls = {
            "finsight": self.finsight_cache_ttl,
            "archive": self.archive_cache_ttl,
            "assistant": self.assistant_cache_ttl
        }
        return module_ttls.get(module, self.cache_ttl)
    
    def get_module_llm_config(self, module: str) -> dict:
        """Get LLM configuration for a specific module"""
        module_configs = {
            "finsight": {
                "temperature": self.finsight_temperature,
                "max_tokens": self.finsight_max_tokens
            },
            "archive": {
                "temperature": self.archive_temperature,
                "max_tokens": self.archive_max_tokens
            },
            "assistant": {
                "temperature": self.assistant_temperature,
                "max_tokens": self.assistant_max_tokens
            }
        }
        return module_configs.get(module, {
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens
        })


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    rate_limit_per_hour: int = 1000  # More lenient for development


class ProductionSettings(Settings):
    """Production environment settings"""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    rate_limit_per_hour: int = 100
    enable_metrics: bool = True


def get_environment_settings() -> Settings:
    """Get environment-specific settings"""
    import os
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()
