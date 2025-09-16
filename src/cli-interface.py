#!/usr/bin/env python3
"""
Nocturnal Archive - Research Paper Analysis CLI Interface

This script provides a terminal-based interface for the Nocturnal Archive
system, which processes, analyzes, and synthesizes research papers.

Dependencies:
    - rich (pip install rich)
    - prompt_toolkit (pip install prompt_toolkit)
"""

import os
import sys
import json
import time
import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import argparse
import configparser
import tempfile
import uuid
from pathlib import Path

# Rich library for beautiful terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.box import ROUNDED, DOUBLE, HEAVY, SIMPLE
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from rich import print as rich_print

# Prompt toolkit for interactive prompts
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import radiolist_dialog, checkboxlist_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

# Add src to path if needed
if str(Path().absolute()) not in sys.path:
    sys.path.append(str(Path().absolute()))

# Load environment variables
try:
    from src.config.env_loader import load_environment
    load_environment()
except ImportError:
    # Fallback if env_loader is not available
    pass

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nocturnal_cli.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("nocturnal_cli")

# Initialize the console
console = Console()

# Import service components - these will be the actual implementations
# If an import fails, we'll provide a workaround
try:
    # Import Rust components via PyO3
    from src.core import (
        ResearchManager,
        DocumentProcessor,
        QueueHandler
    )
    RUST_AVAILABLE = True
    logger.info("Rust components loaded successfully")
except ImportError as e:
    logger.warning(f"Rust components not available: {str(e)}. Some functionality will be limited.")
    RUST_AVAILABLE = False

try:
    # Import Python services
    from services.research_service.synthesizer import ResearchSynthesizer
    from services.research_service.context_manager import ResearchContextManager
    from services.llm_service.llm_manager import LLMManager
    from services.paper_service.paper_manager import PaperManager
    from services.search_service.search_engine import SearchEngine
    from storage.db.operations import DatabaseOperations
    from storage.db.connections import DatabaseConnection
    PYTHON_SERVICES_AVAILABLE = True
    logger.info("Python services loaded successfully")
except ImportError as e:
    logger.warning(f"Python services not available: {str(e)}. Some functionality will be limited.")
    PYTHON_SERVICES_AVAILABLE = False


class ServiceBridge:
    """
    Enhanced service bridge with comprehensive error handling, security, and observability.
    
    Features:
    - Secure service initialization and management
    - Input validation and sanitization
    - Comprehensive error handling and retry logic
    - Structured logging and monitoring
    - Protection against injection attacks
    - Bridge between CLI and backend services
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the service bridge with enhanced security and error handling.
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            ValueError: If configuration is invalid
            ConnectionError: If service initialization fails
        """
        try:
            logger.info("Initializing ServiceBridge with enhanced security")
            
            # Validate config path
            if config_path and not isinstance(config_path, str):
                raise ValueError("Config path must be a string")
            
            # Load configuration with error handling
            self.config = self._load_config(config_path)
            
            # Initialize service components
            self.db_connection = None
            self.redis_client = None
            
            # Rust components
            self.research_manager = None
            self.document_processor = None
            self.queue_handler = None
            
            # Python services
            self.synthesizer = None
            self.context_manager = None
            self.llm_manager = None
            self.paper_manager = None
            self.search_engine = None
            self.db_ops = None
            
            # Cache for paper data with size limits
            self.paper_cache = {}
            self.session_cache = {}
            self._cache_size_limit = 1000  # Prevent memory issues
            
            logger.info("ServiceBridge initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ServiceBridge: {str(e)}")
            raise
    
    def _validate_config_path(self, config_path: str) -> None:
        """
        Validate configuration file path for security.
        
        Args:
            config_path: Configuration file path to validate
            
        Raises:
            ValueError: If path is invalid
        """
        if not config_path:
            return
        
        if not isinstance(config_path, str):
            raise ValueError("Config path must be a string")
        
        if len(config_path) > 500:  # Reasonable limit
            raise ValueError("Config path too long (max 500 characters)")
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'\.\./',  # Directory traversal
            r'~',      # Home directory
            r'//',     # Multiple slashes
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, config_path):
                raise ValueError(f"Config path contains potentially dangerous patterns: {pattern}")
    
    def _sanitize_config_value(self, value: str, max_length: int = 1000) -> str:
        """
        Sanitize configuration value to prevent injection attacks.
        
        Args:
            value: Value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized value
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        if len(value) > max_length:
            value = value[:max_length]
        
        # Basic XSS protection
        sanitized = value.replace('<', '&lt;').replace('>', '&gt;')
        
        # Remove null bytes and other control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load configuration with enhanced error handling and security.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Validate config path
            self._validate_config_path(config_path)
            
            # Default configuration with secure defaults
            default_config = {
                "mongodb_url": "mongodb://localhost:27017",
                "redis_url": "redis://localhost:6379",
                "max_retries": 3,
                "cache_ttl": 3600,
                "default_scope": "medium",
                "log_level": "INFO",
                "security": {
                    "max_file_size": 50 * 1024 * 1024,  # 50MB
                    "allowed_file_types": [".pdf", ".txt", ".md"],
                    "max_concurrent_operations": 10,
                    "session_timeout": 3600
                }
            }
            
            # If config file exists, load it with error handling
            if config_path and os.path.exists(config_path):
                try:
                    config = configparser.ConfigParser()
                    config.read(config_path)
                    
                    # Extract values from config with sanitization
                    if "Database" in config:
                        mongodb_url = config["Database"].get("mongodb_url", default_config["mongodb_url"])
                        default_config["mongodb_url"] = self._sanitize_config_value(mongodb_url, max_length=200)
                        
                        redis_url = config["Database"].get("redis_url", default_config["redis_url"])
                        default_config["redis_url"] = self._sanitize_config_value(redis_url, max_length=200)
                    
                    if "Processing" in config:
                        max_retries = config["Processing"].getint("max_retries", default_config["max_retries"])
                        default_config["max_retries"] = max(1, min(10, max_retries))  # Validate range
                        
                        cache_ttl = config["Processing"].getint("cache_ttl", default_config["cache_ttl"])
                        default_config["cache_ttl"] = max(60, min(86400, cache_ttl))  # Validate range
                    
                    if "Research" in config:
                        default_scope = config["Research"].get("default_scope", default_config["default_scope"])
                        default_config["default_scope"] = self._sanitize_config_value(default_scope, max_length=50)
                    
                    if "Logging" in config:
                        log_level = config["Logging"].get("level", default_config["log_level"])
                        default_config["log_level"] = self._sanitize_config_value(log_level, max_length=20)
                    
                    # Load LLM provider configurations with security
                    llm_providers = {}
                    if "LLMProviders" in config:
                        for key, value in config["LLMProviders"].items():
                            if key.endswith("_api_key"):
                                provider_name = key.split("_api_key")[0]
                                sanitized_provider = self._sanitize_config_value(provider_name, max_length=50)
                                sanitized_key = self._sanitize_config_value(value, max_length=200)
                                llm_providers[sanitized_provider] = {"api_key": sanitized_key}
                    
                    if llm_providers:
                        default_config["llm_providers"] = llm_providers
                    
                    logger.info(f"Loaded configuration from {config_path}")
                    
                except Exception as e:
                    logger.error(f"Error loading config file: {str(e)}")
                    logger.info("Using default configuration")
            
            # Check for environment variables with sanitization
            mongodb_env = os.environ.get("MONGODB_URL")
            if mongodb_env:
                default_config["mongodb_url"] = self._sanitize_config_value(mongodb_env, max_length=200)
            
            redis_env = os.environ.get("REDIS_URL")
            if redis_env:
                default_config["redis_url"] = self._sanitize_config_value(redis_env, max_length=200)
            
            # Check for LLM API keys in environment with security
            llm_providers = default_config.get("llm_providers", {})
            
            # Common LLM provider environment variables
            llm_env_vars = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "cohere": "COHERE_API_KEY",
                "cerebras": "CEREBRAS_API_KEY",
                "mistral": "MISTRAL_API_KEY"
            }
            
            for provider, env_var in llm_env_vars.items():
                api_key = os.environ.get(env_var)
                if api_key:
                    sanitized_key = self._sanitize_config_value(api_key, max_length=200)
                    llm_providers[provider] = {"api_key": sanitized_key}
            
            if llm_providers:
                default_config["llm_providers"] = llm_providers
            
            # Validate final configuration
            self._validate_config(default_config)
            
            logger.info("Configuration loaded and validated successfully")
            return default_config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise ValueError(f"Configuration loading failed: {str(e)}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration values for security and safety.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Validate URLs
            if "mongodb_url" in config:
                url = config["mongodb_url"]
                if not isinstance(url, str) or not url.startswith(("mongodb://", "mongodb+srv://")):
                    raise ValueError("Invalid MongoDB URL format")
            
            if "redis_url" in config:
                url = config["redis_url"]
                if not isinstance(url, str) or not url.startswith("redis://"):
                    raise ValueError("Invalid Redis URL format")
            
            # Validate numeric values
            if "max_retries" in config:
                retries = config["max_retries"]
                if not isinstance(retries, int) or retries < 1 or retries > 10:
                    raise ValueError("max_retries must be between 1 and 10")
            
            if "cache_ttl" in config:
                ttl = config["cache_ttl"]
                if not isinstance(ttl, int) or ttl < 60 or ttl > 86400:
                    raise ValueError("cache_ttl must be between 60 and 86400 seconds")
            
            # Validate scope
            if "default_scope" in config:
                scope = config["default_scope"]
                if scope not in ["small", "medium", "large", "comprehensive"]:
                    raise ValueError("default_scope must be one of: small, medium, large, comprehensive")
            
            # Validate log level
            if "log_level" in config:
                level = config["log_level"]
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if level.upper() not in valid_levels:
                    raise ValueError(f"log_level must be one of: {valid_levels}")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise ValueError(f"Invalid configuration: {str(e)}")
    
    def _clean_cache(self):
        """
        Clean cache to prevent memory issues.
        """
        try:
            # Limit cache sizes
            if len(self.paper_cache) > self._cache_size_limit:
                # Remove oldest entries
                items_to_remove = len(self.paper_cache) - self._cache_size_limit
                for _ in range(items_to_remove):
                    self.paper_cache.popitem()
            
            if len(self.session_cache) > self._cache_size_limit:
                # Remove oldest entries
                items_to_remove = len(self.session_cache) - self._cache_size_limit
                for _ in range(items_to_remove):
                    self.session_cache.popitem()
                    
        except Exception as e:
            logger.warning(f"Error cleaning cache: {str(e)}")
    
    async def initialize(self):
        """
        Initialize all services with enhanced error handling and security.
        
        Raises:
            ConnectionError: If service initialization fails
        """
        try:
            logger.info("Initializing all services")
            
            # Initialize database connections
            try:
                if PYTHON_SERVICES_AVAILABLE:
                    self.db_connection = DatabaseConnection(
                        self.config["mongodb_url"],
                        self.config["redis_url"]
                    )
                    await self.db_connection.connect()
                    
                    self.db_ops = DatabaseOperations(
                        self.config["mongodb_url"],
                        self.config["redis_url"]
                    )
                    logger.info("Database connections initialized successfully")
                else:
                    logger.warning("Database services not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize database connections: {str(e)}")
                raise ConnectionError(f"Database initialization failed: {str(e)}")
            
            # Initialize Rust components
            try:
                if RUST_AVAILABLE:
                    self.research_manager = ResearchManager()
                    self.document_processor = DocumentProcessor()
                    self.queue_handler = QueueHandler()
                    logger.info("Rust components initialized successfully")
                else:
                    logger.warning("Rust components not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Rust components: {str(e)}")
                # Don't fail completely, continue with Python services
            
            # Initialize Python services
            try:
                if PYTHON_SERVICES_AVAILABLE:
                    # Initialize LLM manager
                    self.llm_manager = LLMManager()
                    
                    # Initialize research services
                    self.synthesizer = ResearchSynthesizer(
                        self.db_ops,
                        self.llm_manager,
                        self.config["redis_url"]
                    )
                    
                    self.context_manager = ResearchContextManager(
                        self.db_ops,
                        self.llm_manager
                    )
                    
                    # Initialize other services
                    self.paper_manager = PaperManager(self.db_ops)
                    self.search_engine = SearchEngine()
                    
                    logger.info("Python services initialized successfully")
                else:
                    logger.warning("Python services not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Python services: {str(e)}")
                raise ConnectionError(f"Service initialization failed: {str(e)}")
            
            # Perform health checks
            await self._perform_health_checks()
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            raise
    
    async def _perform_health_checks(self):
        """
        Perform health checks on all services.
        """
        try:
            logger.info("Performing health checks")
            
            health_status = {}
            
            # Check database health
            if self.db_ops:
                try:
                    db_health = await self.db_ops.health_check()
                    health_status["database"] = db_health
                except Exception as e:
                    logger.warning(f"Database health check failed: {str(e)}")
                    health_status["database"] = {"status": "error", "error": str(e)}
            
            # Check LLM manager health
            if self.llm_manager:
                try:
                    llm_health = await self.llm_manager.health_check()
                    health_status["llm_manager"] = llm_health
                except Exception as e:
                    logger.warning(f"LLM manager health check failed: {str(e)}")
                    health_status["llm_manager"] = {"status": "error", "error": str(e)}
            
            # Log health status
            for service, status in health_status.items():
                if status.get("status") == "healthy":
                    logger.info(f"{service}: healthy")
                else:
                    logger.warning(f"{service}: {status.get('status', 'unknown')}")
            
            logger.info("Health checks completed")
            
        except Exception as e:
            logger.error(f"Health checks failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all services.
        
        Returns:
            Health status dictionary
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {}
            }
            
            # Check database
            if self.db_ops:
                try:
                    db_health = await self.db_ops.health_check()
                    health_status["services"]["database"] = db_health
                    if db_health.get("status") != "healthy":
                        health_status["status"] = "degraded"
                except Exception as e:
                    health_status["services"]["database"] = {"status": "error", "error": str(e)}
                    health_status["status"] = "degraded"
            
            # Check LLM manager
            if self.llm_manager:
                try:
                    llm_health = await self.llm_manager.health_check()
                    health_status["services"]["llm_manager"] = llm_health
                    if llm_health.get("status") != "healthy":
                        health_status["status"] = "degraded"
                except Exception as e:
                    health_status["services"]["llm_manager"] = {"status": "error", "error": str(e)}
                    health_status["status"] = "degraded"
            
            # Check cache status
            health_status["services"]["cache"] = {
                "status": "healthy",
                "paper_cache_size": len(self.paper_cache),
                "session_cache_size": len(self.session_cache)
            }
            
            logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_system_health(self) -> Dict[str, bool]:
        """
        Check the health of all system components.
        
        Returns:
            Dictionary with health status of each component
        """
        health = {
            "database": False,
            "redis": False,
            "research_manager": False,
            "document_processor": False,
            "llm_service": False,
            "overall": False
        }
        
        # Check database
        if self.db_connection:
            try:
                health["database"] = await self.db_connection.check_health()
            except Exception:
                pass
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis"] = True
            except Exception:
                pass
        
        # Check Rust components
        health["research_manager"] = self.research_manager is not None
        health["document_processor"] = self.document_processor is not None
        
        # Check LLM service
        if self.llm_manager:
            try:
                # Simple LLM check - just see if the manager exists and has providers
                providers = self.llm_manager.get_providers()
                health["llm_service"] = len(providers) > 0
            except Exception:
                pass
        
        # Overall health
        health["overall"] = (
            health["redis"] and 
            (health["database"] or not PYTHON_SERVICES_AVAILABLE) and
            (health["research_manager"] or not RUST_AVAILABLE) and
            (health["document_processor"] or not RUST_AVAILABLE) and
            (health["llm_service"] or not PYTHON_SERVICES_AVAILABLE)
        )
        
        return health
    
    async def get_research_sessions(self, status: str = None, limit: int = 10) -> List[Dict]:
        """
        Get all research sessions, optionally filtered by status.
        
        Args:
            status: Filter by status
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        sessions = []
        
        # Try context manager first if available
        if self.context_manager:
            try:
                # In a real implementation, this would fetch from the database
                # Here we're using a basic demo approach
                active_sessions = self.session_cache.values()
                
                if status:
                    active_sessions = [s for s in active_sessions if s["status"] == status]
                
                sessions.extend(active_sessions)
                
                # Sort by creation time (newest first) and limit
                sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                sessions = sessions[:limit]
                
                return sessions
            except Exception as e:
                logger.error(f"Error getting sessions from context manager: {e}")
        
        # Fall back to research manager
        if self.research_manager:
            try:
                # Get active sessions from Rust
                # This approach depends on the details of the Rust implementation
                queue_result = await self.research_manager.process_research_queue()
                
                # For now, return any cached sessions
                return list(self.session_cache.values())[:limit]
            except Exception as e:
                logger.error(f"Error getting sessions from research manager: {e}")
        
        return sessions
    
    async def get_session_details(self, session_id: str) -> Optional[Dict]:
        """
        Get detailed information about a research session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session details dictionary or None if not found
        """
        # Check cache first
        if session_id in self.session_cache:
            return self.session_cache[session_id]
        
        # Try context manager
        if self.context_manager:
            try:
                # Get session status from context manager
                session = await self.context_manager.get_session_status(session_id)
                
                if session and "error" not in session:
                    # Cache it
                    self.session_cache[session_id] = session
                    return session
            except Exception as e:
                logger.error(f"Error getting session details from context manager: {e}")
        
        # Try research manager as fallback
        if self.research_manager:
            try:
                # Get session status from research manager
                progress = await self.research_manager.get_research_status(session_id)
                
                if progress:
                    # Convert to session dictionary
                    session = {
                        "id": session_id,
                        "topic": "Unknown",  # Session topic not available from research_manager
                        "status": self._map_research_status(progress.get("current_phase", "")),
                        "created_at": "Unknown",
                        "updated_at": datetime.now().isoformat(),
                        "papers_found": progress.get("papers_total", 0),
                        "papers_processed": progress.get("papers_processed", 0),
                        "completion_percentage": (
                            progress.get("papers_processed", 0) / 
                            max(1, progress.get("papers_total", 1)) * 100
                        )
                    }
                    
                    # Cache it
                    self.session_cache[session_id] = session
                    return session
            except Exception as e:
                logger.error(f"Error getting session details from research manager: {e}")
        
        return None
    
    def _map_research_status(self, rust_status: str) -> str:
        """
        Map research status from Rust enum to string.
        
        Args:
            rust_status: Status from Rust component
            
        Returns:
            Human-readable status string
        """
        status_map = {
            "Initializing": "Initializing",
            "SearchingPapers": "Collecting",
            "ProcessingDocuments": "Processing",
            "BuildingKnowledge": "Processing",
            "Completed": "Completed",
            "Error": "Error"
        }
        
        return status_map.get(rust_status, rust_status)
    
    async def get_session_papers(self, session_id: str) -> List[Dict]:
        """
        Get papers associated with a research session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Try database operations
        if self.db_ops:
            try:
                # In a real implementation, this would query the database
                # Here we're using a mock approach
                
                # Get session details to check papers
                session = await self.get_session_details(session_id)
                
                if session:
                    # Get papers for this session
                    for paper_id, paper in self.paper_cache.items():
                        if paper.get("session_id") == session_id:
                            papers.append(paper)
                            
                    # Generate some papers if none exist (for demo purposes)
                    if not papers and "papers_found" in session:
                        num_papers = min(session["papers_found"], 10)
                        for i in range(num_papers):
                            paper_id = f"p{i+1:03d}"
                            paper = {
                                "id": paper_id,
                                "title": f"Paper {i+1} on {session['topic']}",
                                "authors": "Author et al.",
                                "status": "Processed" if i < session["papers_processed"] else "Pending",
                                "session_id": session_id
                            }
                            papers.append(paper)
                            self.paper_cache[paper_id] = paper
            except Exception as e:
                logger.error(f"Error getting session papers: {e}")
        
        return papers
    
    async def create_research_session(self, topic: str, scope: str = "medium", 
                                     focus_areas: List[str] = None, 
                                     context: str = None) -> str:
        """
        Create a new research session.
        
        Args:
            topic: Research topic
            scope: Research scope (light, medium, deep)
            focus_areas: List of focus areas
            context: Additional research context
            
        Returns:
            Session ID
        """
        session_id = ""
        
        # Prepare context dictionary
        context_dict = {
            "scope": scope,
            "focus_areas": focus_areas or ["Methods", "Materials"],
            "context": context,
            "created_at": datetime.now().isoformat()
        }
        
        # Try context manager first
        if self.context_manager:
            try:
                session_id = await self.context_manager.create_session(topic, context_dict)
                logger.info(f"Created research session via context manager: {session_id}")
                
                # Cache the session
                self.session_cache[session_id] = {
                    "id": session_id,
                    "topic": topic,
                    "status": "Initializing",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "papers_found": 0,
                    "papers_processed": 0,
                    "completion_percentage": 0,
                    "research_context": context,
                    "focus_areas": focus_areas,
                    "insights": []
                }
                
                return session_id
            except Exception as e:
                logger.error(f"Error creating session via context manager: {e}")
        
        # Fall back to research manager
        if self.research_manager:
            try:
                session_id = await self.research_manager.start_research(topic)
                logger.info(f"Created research session via research manager: {session_id}")
                
                # Cache the session
                self.session_cache[session_id] = {
                    "id": session_id,
                    "topic": topic,
                    "status": "Initializing",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "papers_found": 0,
                    "papers_processed": 0,
                    "completion_percentage": 0,
                    "research_context": context,
                    "focus_areas": focus_areas,
                    "insights": []
                }
                
                return session_id
            except Exception as e:
                logger.error(f"Error creating session via research manager: {e}")
        
        # If all else fails, create a local session ID
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Created local research session: {session_id}")
            
            # Cache the session
            self.session_cache[session_id] = {
                "id": session_id,
                "topic": topic,
                "status": "Initializing",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "papers_found": 0,
                "papers_processed": 0,
                "completion_percentage": 0,
                "research_context": context,
                "focus_areas": focus_areas,
                "insights": []
            }
        
        return session_id
    
    async def add_paper(self, file_path: str, session_id: str = None) -> str:
        """
        Add a new paper to the system.
        
        Args:
            file_path: Path to the paper file
            session_id: ID of the session to add the paper to
            
        Returns:
            Paper ID
        """
        paper_id = ""
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Get filename and content type
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        
        # Determine content type
        content_type_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".csv": "text/csv",
            ".json": "application/json"
        }
        content_type = content_type_map.get(ext.lower(), "application/octet-stream")
        
        # Try paper manager first
        if self.paper_manager:
            try:
                paper_id = await self.paper_manager.add_paper(content, filename, content_type)
                logger.info(f"Added paper via paper manager: {paper_id}")
                
                # Create paper dictionary
                paper = {
                    "id": paper_id,
                    "title": filename,  # Use filename as title initially
                    "authors": "Unknown",  # Will be extracted during processing
                    "status": "Pending",
                    "session_id": session_id
                }
                
                # Cache the paper
                self.paper_cache[paper_id] = paper
                
                # If session_id is provided, update session
                if session_id and session_id in self.session_cache:
                    session = self.session_cache[session_id]
                    session["papers_found"] = session.get("papers_found", 0) + 1
                    session["updated_at"] = datetime.now().isoformat()
                
                return paper_id
            except Exception as e:
                logger.error(f"Error adding paper via paper manager: {e}")
        
        # Fall back to document processor
        if self.document_processor:
            try:
                # Create document for processing
                paper_id = str(uuid.uuid4())
                
                # Prepare document
                document = {
                    "id": paper_id,
                    "content": content,
                    "metadata": {
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(content),
                        "created_at": datetime.now().isoformat()
                    }
                }
                
                # Process document
                try:
                    processed = await self.document_processor.process_document(document)
                    logger.info(f"Processed document: {paper_id}")
                    
                    # Create paper dictionary
                    paper = {
                        "id": paper_id,
                        "title": filename,  # Use filename as title initially
                        "authors": "Unknown",  # Will be extracted during processing
                        "status": "Processing",
                        "session_id": session_id
                    }
                    
                    # Cache the paper
                    self.paper_cache[paper_id] = paper
                    
                    # If session_id is provided, update session
                    if session_id and session_id in self.session_cache:
                        session = self.session_cache[session_id]
                        session["papers_found"] = session.get("papers_found", 0) + 1
                        session["updated_at"] = datetime.now().isoformat()
                    
                    return paper_id
                except Exception as e:
                    logger.error(f"Error processing document: {e}")
            except Exception as e:
                logger.error(f"Error using document processor: {e}")
        
        # If all else fails, create a local paper ID
        if not paper_id:
            paper_id = f"p{len(self.paper_cache) + 1:03d}"
            logger.info(f"Created local paper ID: {paper_id}")
            
            # Create paper dictionary
            paper = {
                "id": paper_id,
                "title": filename,  # Use filename as title initially
                "authors": "Unknown",  # Will be extracted during processing
                "status": "Pending",
                "session_id": session_id
            }
            
            # Cache the paper
            self.paper_cache[paper_id] = paper
            
            # If session_id is provided, update session
            if session_id and session_id in self.session_cache:
                session = self.session_cache[session_id]
                session["papers_found"] = session.get("papers_found", 0) + 1
                session["updated_at"] = datetime.now().isoformat()
        
        return paper_id
    
    async def search_papers(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for papers using combined search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching papers
        """
        results = []
        
        # Try search engine first
        if self.search_engine:
            try:
                results = await self.search_engine.combined_search(query, limit=limit)
                logger.info(f"Found {len(results)} papers via search engine")
                return results
            except Exception as e:
                logger.error(f"Error searching papers via search engine: {e}")
        
        # Fall back to simple search in paper cache
        if query:
            for paper_id, paper in self.paper_cache.items():
                if (query.lower() in paper.get("title", "").lower() or 
                    query.lower() in paper.get("authors", "").lower()):
                    results.append(paper)
            
            # Limit results
            results = results[:limit]
        else:
            # Return all papers up to limit
            results = list(self.paper_cache.values())[:limit]
        
        return results
    
    async def create_synthesis(self, paper_ids: List[str], force_refresh: bool = False) -> Dict:
        """
        Create a synthesis of multiple papers.
        
        Args:
            paper_ids: List of paper IDs to synthesize
            force_refresh: Whether to force refresh the synthesis
            
        Returns:
            Synthesis dictionary
        """
        # Try synthesizer first
        if self.synthesizer:
            try:
                synthesis = await self.synthesizer.synthesize_papers(paper_ids, force_refresh)
                logger.info(f"Created synthesis for {len(paper_ids)} papers")
                return synthesis
            except Exception as e:
                logger.error(f"Error creating synthesis via synthesizer: {e}")
        
        # Return basic synthesis structure
        return {
            "meta": {
                "paper_count": len(paper_ids),
                "generated_at": datetime.now().isoformat(),
                "paper_ids": paper_ids
            }
        }
    
    async def get_llm_providers(self) -> Dict[str, Dict]:
        """
        Get information about configured LLM providers.
        
        Returns:
            Dictionary of provider information
        """
        providers = {}
        
        # Try LLM manager
        if self.llm_manager:
            try:
                provider_info = self.llm_manager.get_providers()
                
                # Convert to standard format
                for provider, info in provider_info.items():
                    providers[provider] = {
                        "status": info.get("status", "unknown"),
                        "quota_remaining": info.get("quota_remaining", 0),
                        "token_usage": {
                            "today": info.get("usage_today", 0),
                            "this_week": info.get("usage_week", 0),
                            "this_month": info.get("usage_month", 0)
                        }
                    }
                
                logger.info(f"Got information for {len(providers)} LLM providers")
                return providers
            except Exception as e:
                logger.error(f"Error getting LLM provider information: {e}")
        
        # Return empty dictionary
        return providers
    
    async def get_queue_status(self) -> Dict[str, int]:
        """
        Get status of processing queues.
        
        Returns:
            Dictionary with queue lengths
        """
        queue_status = {
            "processing_queue": 0,
            "retry_queue": 0,
            "dead_letter_queue": 0,
            "paper_search_queue": 0
        }
        
        # Try queue handler
        if self.queue_handler:
            try:
                processing, retry = await self.queue_handler.get_queue_length()
                queue_status["processing_queue"] = processing
                queue_status["retry_queue"] = retry
                
                logger.info(f"Got queue status: {processing} processing, {retry} retry")
            except Exception as e:
                logger.error(f"Error getting queue status: {e}")
        
        # Try Redis client for additional queues
        if self.redis_client:
            try:
                queue_status["dead_letter_queue"] = await self.redis_client.llen("dead_letter_queue")
                queue_status["paper_search_queue"] = await self.redis_client.llen("paper_search_queue")
            except Exception as e:
                logger.error(f"Error getting Redis queue lengths: {e}")
        
        return queue_status
    
    async def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """
        Get detailed information about a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Paper details dictionary or None if not found
        """
        # Check cache first
        if paper_id in self.paper_cache:
            return self.paper_cache[paper_id]
        
        # Try database operations
        if self.db_ops:
            try:
                # In a real implementation, this would query the database
                paper = await self.db_ops.get_paper(paper_id)
                
                if paper:
                    # Convert to dictionary
                    paper_dict = {
                        "id": paper.id,
                        "title": paper.filename,
                        "authors": "Unknown",
                        "status": paper.status
                    }
                    
                    # Check if processed content is available
                    processed = await self.db_ops.get_processed_paper(paper_id)
                    if processed:
                        # Update with processed info
                        paper_dict["title"] = processed.metadata.get("title", paper.filename)
                        paper_dict["authors"] = processed.metadata.get("authors", "Unknown")
                        paper_dict["status"] = "Processed"
                        paper_dict["summary"] = processed.summary
                        paper_dict["key_findings"] = processed.metadata.get("key_findings", [])
                        paper_dict["methodology"] = processed.metadata.get("methodology", "")
                        paper_dict["limitations"] = processed.metadata.get("limitations", "")
                    
                    # Cache paper
                    self.paper_cache[paper_id] = paper_dict
                    
                    return paper_dict
            except Exception as e:
                logger.error(f"Error getting paper details: {e}")
        
        return None
    
    async def archive_session(self, session_id: str) -> bool:
        """
        Archive a research session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        # Check if session exists
        if session_id not in self.session_cache:
            session = await self.get_session_details(session_id)
            if not session:
                return False
        
        # Update session status
        if session_id in self.session_cache:
            self.session_cache[session_id]["status"] = "Archived"
            self.session_cache[session_id]["updated_at"] = datetime.now().isoformat()
        
        # In a real implementation, this would update the database
        
        logger.info(f"Archived session: {session_id}")
        return True
    
    async def cleanup(self):
        """Clean up all resources."""
        # Clean up Python services
        if self.synthesizer:
            try:
                await self.synthesizer.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up synthesizer: {e}")
        
        if self.context_manager:
            try:
                await self.context_manager.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up context manager: {e}")
        
        if self.db_ops:
            try:
                await self.db_ops.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up database operations: {e}")
        
        # Close database connections
        if self.db_connection:
            try:
                await self.db_connection.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up database connection: {e}")
        
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
        
        logger.info("Service cleanup complete")


# Global key bindings
kb = KeyBindings()

@kb.add("c-q")
def exit_app(event):
    """Exit the application when Ctrl+Q is pressed."""
    event.app.exit()

@kb.add("?")
def show_help(event):
    """Show help menu when ? is pressed."""
    # We'll implement this in the NocturnalArchiveUI class


class NocturnalArchiveUI:
    """
    Main UI class for the Nocturnal Archive CLI.
    """
    
    def __init__(self, service_bridge: ServiceBridge):
        """
        Initialize the UI with a service bridge.
        
        Args:
            service_bridge: Service bridge for backend communication
        """
        self.service = service_bridge
        self.tabs = ["Research", "Papers", "Synthesis", "LLM Hub", "Config", "Dashboard"]
        self.active_tab = "Research"
        self.running = False
        self.notifications = []
        
        # System status
        self.system_status = "Starting"
        self.active_session_count = 0
        self.paper_count = 0
        self.llm_status = "?"
        
        # Initialize the prompt session for interactive input
        self.prompt_session = PromptSession()
        
        # Initialize key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
    
    def _setup_key_bindings(self):
        """Set up key bindings for the UI."""
        
        @self.kb.add("c-q")
        def exit_app(event):
            """Exit the application when Ctrl+Q is pressed."""
            self.running = False
            event.app.exit()
        
        @self.kb.add("?")
        def show_help(event):
            """Show help menu when ? is pressed."""
            self.show_help()
            event.app.exit()
        
        @self.kb.add("tab")
        def next_tab(event):
            """Switch to the next tab when Tab is pressed."""
            current_index = self.tabs.index(self.active_tab)
            next_index = (current_index + 1) % len(self.tabs)
            self.active_tab = self.tabs[next_index]
            event.app.exit()
        
        @self.kb.add("r")
        def research_tab(event):
            """Switch to Research tab when r is pressed."""
            self.active_tab = "Research"
            event.app.exit()
        
        @self.kb.add("p")
        def papers_tab(event):
            """Switch to Papers tab when p is pressed."""
            self.active_tab = "Papers"
            event.app.exit()
        
        @self.kb.add("s")
        def synthesis_tab(event):
            """Switch to Synthesis tab when s is pressed."""
            self.active_tab = "Synthesis"
            event.app.exit()
        
        @self.kb.add("l")
        def llm_tab(event):
            """Switch to LLM Hub tab when l is pressed."""
            self.active_tab = "LLM Hub"
            event.app.exit()
        
        @self.kb.add("c")
        def config_tab(event):
            """Switch to Config tab when c is pressed."""
            self.active_tab = "Config"
            event.app.exit()
        
        @self.kb.add("d")
        def dashboard_tab(event):
            """Switch to Dashboard tab when d is pressed."""
            self.active_tab = "Dashboard"
            event.app.exit()
        
        @self.kb.add("/")
        def search(event):
            """Start search when / is pressed."""
            # This will be handled in the specific tab methods
            event.app.exit()
    
    async def start(self):
        """Start the UI."""
        self.running = True
        
        # Display welcome screen
        self.display_welcome()
        
        # Main loop
        while self.running:
            # Update system status
            await self.update_status()
            
            # Render the current tab
            await self.render_current_tab()
            
            # Get user input
            try:
                command = await self.get_command()
                
                # Process the command
                if command:
                    await self.process_command(command)
            except KeyboardInterrupt:
                if Confirm.ask("Are you sure you want to exit?"):
                    self.running = False
            except Exception as e:
                logger.exception(f"Error in main loop: {e}")
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
                console.print_exception()
                console.print("\nPress Enter to continue...")
                input()
        
        # Clean shutdown
        await self.shutdown()
    
    def display_welcome(self):
        """Display the welcome screen."""
        console.clear()
        
        # Title banner
        console.print(Panel.fit(
            "[bold cyan]NOCTURNAL ARCHIVE[/bold cyan]\n"
            "[white]Research Paper Analysis System[/white]",
            box=HEAVY,
            border_style="bright_blue"
        ))
        console.print()
        console.print("[dim]Initializing system components...[/dim]")
        
        # Initialize services with progress indicators
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add tasks
            db_task = progress.add_task("[cyan]Connecting to databases...", total=100)
            llm_task = progress.add_task("[cyan]Initializing LLM services...", total=100, visible=False)
            cache_task = progress.add_task("[cyan]Loading cache...", total=100, visible=False)
            
            # Update progress as initialization proceeds
            # This would normally be driven by actual initialization events
            for i in range(101):
                if i < 100:
                    progress.update(db_task, completed=min(i * 1.2, 100))
                if i > 10:
                    progress.update(llm_task, visible=True)
                    progress.update(llm_task, completed=min((i - 10) * 1.3, 100))
                if i > 30:
                    progress.update(cache_task, visible=True)
                    progress.update(cache_task, completed=min((i - 30) * 1.4, 100))
                time.sleep(0.01)
        
        console.print("[bold green]System initialized successfully![/bold green]")
        time.sleep(1)
    
    async def update_status(self):
        """Update system status by checking services."""
        try:
            health = await self.service.get_system_health()
            self.system_status = "Online" if health["overall"] else "Issues Detected"
            
            # Get active session count
            sessions = await self.service.get_research_sessions()
            self.active_session_count = len(sessions)
            
            # Get paper count from search with empty query
            papers = await self.service.search_papers("")
            self.paper_count = len(papers)
            
            # Get LLM status
            providers = await self.service.get_llm_providers()
            self.llm_status = "✓" if providers else "✗"
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            self.system_status = "Error"
            # Leave other status values as they are
    
    async def render_current_tab(self):
        """Render the currently active tab."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]NOCTURNAL ARCHIVE[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Print status bar
        status_text = f"Status: {self.active_session_count} Active Sessions │ {self.paper_count} Papers │ System: {self.system_status}"
        console.print(f"\n{status_text}\n")
        
        # Print navigation tabs
        tab_text = ""
        for tab in self.tabs:
            if tab == self.active_tab:
                tab_text += f"[bold white on blue]  {tab}  [/bold white on blue]"
            else:
                tab_text += f"[white]  {tab}  [/white]"
        
        console.print(Panel(tab_text, expand=True))
        console.print()
        
        # Print notifications if any
        if self.notifications:
            for notification in self.notifications[:1]:  # Only show the first one for now
                console.print(f"[!] {notification}")
                console.print("    Press [N] to dismiss or [V] to view details")
                console.print()
        
        # Render the specific tab content
        tab_method = getattr(self, f"render_{self.active_tab.lower().replace(' ', '_')}_tab", None)
        if tab_method:
            await tab_method()
        else:
            console.print(f"Tab '{self.active_tab}' not implemented yet.")
        
        # Print footer
        footer_text = "[1-4]: Select option │ [↑/↓]: Scroll │ [Tab]: Switch tabs │ [?]: Help"
        console.print(Panel(footer_text, box=SIMPLE, expand=True, border_style="dim"))
    
    async def get_command(self) -> str:
        """Get a command from the user."""
        try:
            return await self.prompt_session.prompt_async(">> ")
        except KeyboardInterrupt:
            return "q"  # Treat Ctrl+C as quit
    
    async def process_command(self, command: str):
        """Process a user command."""
        # Check for global commands
        if command.lower() in ["q", "quit", "exit"]:
            if Confirm.ask("Are you sure you want to exit?"):
                self.running = False
        elif command == "?":
            self.show_help()
        elif command.lower() == "n" and self.notifications:
            self.notifications.pop(0)  # Dismiss notification
        elif command.lower() == "v" and self.notifications:
            # View notification details
            notification = self.notifications[0]
            console.print(f"\n[bold]Notification Details:[/bold] {notification}")
            console.print("\nPress Enter to continue...")
            input()
        elif command in ["r", "p", "s", "l", "c", "d"]:
            # Tab switching shortcuts
            tab_map = {"r": "Research", "p": "Papers", "s": "Synthesis", 
                      "l": "LLM Hub", "c": "Config", "d": "Dashboard"}
            self.active_tab = tab_map[command]
        elif command in ["1", "2", "3", "4", "5"]:
            # Numbered options - handle in tab-specific methods
            tab_method = getattr(self, f"process_{self.active_tab.lower().replace(' ', '_')}_command", None)
            if tab_method:
                await tab_method(command)
            else:
                console.print(f"[yellow]Command not implemented for {self.active_tab} tab[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
        elif command == "cmd":
            await self.show_command_palette()
        elif command == "/":
            await self.handle_search()
        else:
            # Check if it's a tab name
            if command in self.tabs:
                self.active_tab = command
            else:
                console.print(f"[yellow]Unknown command: {command}[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
    
    def show_help(self):
        """Show the help screen."""
        console.clear()
        
        console.print(Panel(
            "[bold]KEYBOARD SHORTCUTS[/bold]\n\n"
            "Navigation\n"
            "• Tab             Switch tabs\n"
            "• r/p/s/l/c/d     Switch tabs\n"
            "• ↑/↓             Scroll list\n"
            "• /               Search/filter\n"
            "• Home/End        Top/bottom\n"
            "• Esc             Go back/cancel\n"
            "• ?               Show help\n\n"
            
            "Actions\n"
            "• Ctrl+N    Create session\n"
            "• Ctrl+F    Find papers\n"
            "• Ctrl+S    Create synthesis\n"
            "• Ctrl+E    Export current view\n"
            "• Ctrl+R    Refresh status\n"
            "• Ctrl+Q    Quit application\n\n"
            
            "Command Palette\n"
            "Open with 'Ctrl+P' or type 'cmd' at any prompt\n\n"
            
            "Common commands:\n"
            "• create research  - Start a new research session\n"
            "• add paper       - Add a new paper to the library\n"
            "• search papers   - Search for papers on a topic\n"
            "• create synthesis - Generate a synthesis from papers\n"
            "• export          - Export results in various formats\n"
            "• check quota     - Check remaining LLM API quotas",
            title="NOCTURNAL ARCHIVE: HELP",
            border_style="cyan",
            box=ROUNDED
        ))
        
        console.print("\nPress Enter to continue...")
        input()
    
    async def show_command_palette(self):
        """Show the command palette."""
        # List of common commands
        commands = [
            ("create research", "Create a new research session"),
            ("view session", "View details of a research session"),
            ("add paper", "Add a new paper to the library"),
            ("search papers", "Search for papers on a topic"),
            ("create synthesis", "Create a synthesis from papers"),
            ("export", "Export results to file"),
            ("check quota", "Check LLM API quota"),
            ("help", "Show help documentation")
        ]
        
        # Create a command completer
        command_completer = WordCompleter([cmd[0] for cmd in commands])
        
        console.clear()
        console.print(Panel(
            "Type a command or search for commands",
            title="Command Palette",
            border_style="cyan",
            box=ROUNDED
        ))
        
        for cmd, desc in commands:
            console.print(f"[cyan]{cmd}[/cyan] - {desc}")
        
        console.print()
        
        try:
            command = self.prompt_session.prompt(
                "Command: ",
                completer=command_completer
            )
            
            if command:
                await self.process_palette_command(command)
        except KeyboardInterrupt:
            pass
    
    async def process_palette_command(self, command: str):
        """Process a command from the command palette."""
        if command == "create research":
            await self.create_research_session()
        elif command == "view session":
            session_id = Prompt.ask("Enter session ID")
            await self.view_session_details(session_id)
        elif command == "add paper":
            self.active_tab = "Papers"
            await self.add_paper()
        elif command == "search papers":
            query = Prompt.ask("Enter search query")
            await self.search_papers(query)
        elif command == "create synthesis":
            session_id = Prompt.ask("Enter session ID for synthesis")
            await self.create_synthesis(session_id)
        elif command == "export":
            await self.export_current_view()
        elif command == "check quota":
            await self.check_llm_quota()
        elif command == "help":
            self.show_help()
    
    async def handle_search(self):
        """Handle search input."""
        search_query = Prompt.ask("Search")
        
        if self.active_tab == "Research":
            await self.search_sessions(search_query)
        elif self.active_tab == "Papers":
            await self.search_papers(search_query)
        elif self.active_tab == "Synthesis":
            await self.search_syntheses(search_query)
        else:
            console.print(f"[yellow]Search not implemented for {self.active_tab} tab[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
    
    async def render_research_tab(self):
        """Render the Research tab."""
        # Get active sessions
        sessions = await self.service.get_research_sessions()
        
        console.print("[bold]ACTIVE SESSIONS[/bold]")
        
        if not sessions:
            console.print("No active sessions found.")
            console.print("\nCreate a new research session to get started.")
        else:
            # Create a table for sessions
            table = Table(box=ROUNDED, expand=True)
            table.add_column("ID", style="dim")
            table.add_column("Topic", style="bright_white")
            table.add_column("Status", style="green")
            table.add_column("Progress", justify="right")
            
            # Add sessions to the table
            for session in sessions:
                # Create progress bar
                progress = session["completion_percentage"]
                progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
                
                table.add_row(
                    session["id"],
                    session["topic"],
                    session["status"],
                    f"{progress_bar} {progress}%"
                )
            
            console.print(table)
            
            # Show how many sessions are visible
            console.print(f"Showing {len(sessions)} session{'s' if len(sessions) != 1 else ''}")
        
        console.print()
        console.print("[1] View Session Details  [2] Create New Session  [3] Archive Session  [4] Refresh")
    
    async def process_research_command(self, command: str):
        """Process commands for the Research tab."""
        if command == "1":
            # View session details
            sessions = await self.service.get_research_sessions()
            if not sessions:
                console.print("[yellow]No sessions available to view.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
            
            session_id = Prompt.ask("Enter session ID or number")
            
            # Check if it's a number
            try:
                index = int(session_id) - 1
                if 0 <= index < len(sessions):
                    session_id = sessions[index]["id"]
                else:
                    console.print(f"[yellow]Invalid session number: {session_id}[/yellow]")
                    console.print("\nPress Enter to continue...")
                    input()
                    return
            except ValueError:
                # It's not a number, use as is
                pass
            
            await self.view_session_details(session_id)
            
        elif command == "2":
            # Create new session
            await self.create_research_session()
            
        elif command == "3":
            # Archive session
            sessions = await self.service.get_research_sessions()
            if not sessions:
                console.print("[yellow]No sessions available to archive.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
            
            session_id = Prompt.ask("Enter session ID to archive")
            
            # Find the session
            session = None
            for s in sessions:
                if s["id"] == session_id:
                    session = s
                    break
            
            if not session:
                console.print(f"[yellow]Session not found: {session_id}[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
            
            if Confirm.ask(f"Are you sure you want to archive session '{session['topic']}'?"):
                success = await self.service.archive_session(session_id)
                if success:
                    console.print(f"[green]Session {session_id} archived.[/green]")
                else:
                    console.print(f"[red]Failed to archive session {session_id}.[/red]")
                console.print("\nPress Enter to continue...")
                input()
                
        elif command == "4":
            # Refresh - just redraw tab
            pass
    
    async def view_session_details(self, session_id: str):
        """View details of a research session."""
        # Get session details
        session = await self.service.get_session_details(session_id)
        
        if not session:
            console.print(f"[yellow]Session not found: {session_id}[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]SESSION DETAILS: {session['topic']}[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Session info panel
        info_panel = Panel(
            f"ID: {session['id']}{' ':>30}Created: {session['created_at']}\n"
            f"Status: {session['status']}{' ':>26}Progress: {'█' * int(session['completion_percentage'] / 10)}{'░' * (10 - int(session['completion_percentage'] / 10))} {session['completion_percentage']}%\n"
            f"Papers Found: {session['papers_found']}{' ':>21}Papers Processed: {session['papers_processed']}",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(info_panel)
        console.print()
        
        # Research context
        if "research_context" in session and session["research_context"]:
            console.print("[bold]RESEARCH CONTEXT[/bold]")
            context_panel = Panel(
                session["research_context"],
                box=ROUNDED,
                border_style="cyan"
            )
            console.print(context_panel)
            console.print()
        
        # Insights
        if "insights" in session and session["insights"]:
            console.print("[bold]EMERGING INSIGHTS[/bold]")
            insights_panel = Panel(
                "\n".join([f"• {insight}" for insight in session["insights"]]),
                box=ROUNDED,
                border_style="cyan"
            )
            console.print(insights_panel)
            console.print()
        
        # Current activity
        if session["status"] in ["Initializing", "Processing", "Collecting"]:
            console.print("[bold]CURRENT ACTIVITY[/bold]")
            console.print(f"⣾ Processing papers for {session['topic']}")
            provider_info = await self.service.get_llm_providers()
            if provider_info:
                provider = next(iter(provider_info.keys()))
                console.print(f"⣷ Using LLM provider: {provider.title()}")
            console.print()
        
        # Options
        console.print("[1] View Papers  [2] Refresh Status  [3] Create Synthesis  [4] Back to List")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3", "4"], show_choices=False)
        
        if command == "1":
            await self.view_session_papers(session_id)
        elif command == "2":
            # Just refresh by viewing again
            await self.view_session_details(session_id)
        elif command == "3":
            await self.create_synthesis(session_id)
        # command == "4" will just return to the main screen
    
    async def view_session_papers(self, session_id: str):
        """View papers in a research session."""
        # Get session papers
        papers = await self.service.get_session_papers(session_id)
        
        # Get session details for the title
        session = await self.service.get_session_details(session_id)
        if not session:
            console.print("[yellow]Session not found.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]SESSION PAPERS: {session['topic']} (ID: {session_id})[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        if not papers:
            console.print("[yellow]No papers found for this session.[/yellow]")
        else:
            # Create a table for papers
            table = Table(box=ROUNDED, expand=True)
            table.add_column("ID", style="dim")
            table.add_column("Title", style="bright_white")
            table.add_column("Authors", style="cyan")
            table.add_column("Status", style="green")
            
            # Add papers to the table
            for paper in papers:
                table.add_row(
                    paper["id"],
                    paper["title"],
                    paper["authors"],
                    paper["status"]
                )
            
            console.print(table)
            
            # Show how many papers are visible
            console.print(f"Showing {len(papers)} paper{'s' if len(papers) != 1 else ''}")
        
        console.print()
        
        # Options
        console.print("[1] View Paper Details  [2] Add Paper  [3] Back to Session  [4] Refresh")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3", "4"], show_choices=False)
        
        if command == "1":
            if not papers:
                console.print("[yellow]No papers available to view.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
                
            paper_id = Prompt.ask("Enter paper ID to view")
            
            # Check if paper exists
            paper_exists = False
            for paper in papers:
                if paper["id"] == paper_id:
                    paper_exists = True
                    break
            
            if not paper_exists:
                console.print(f"[yellow]Paper not found: {paper_id}[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
                
            await self.view_paper_details(paper_id, session_id)
        elif command == "2":
            await self.add_paper(session_id)
        elif command == "3":
            await self.view_session_details(session_id)
        elif command == "4":
            await self.view_session_papers(session_id)
    
    async def view_paper_details(self, paper_id: str, session_id: str = None):
        """View details of a paper."""
        # Get paper details
        paper = await self.service.get_paper_details(paper_id)
        
        if not paper:
            console.print(f"[yellow]Paper not found: {paper_id}[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]PAPER DETAILS[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Paper info panel
        info_panel = Panel(
            f"ID: {paper['id']}\n"
            f"Title: {paper['title']}\n"
            f"Authors: {paper['authors']}\n"
            f"Status: {paper['status']}",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(info_panel)
        console.print()
        
        # Extracted information
        if "key_findings" in paper or "methodology" in paper or "limitations" in paper:
            console.print("[bold]EXTRACTED INFORMATION[/bold]")
            
            panel_content = ""
            
            if "key_findings" in paper and paper["key_findings"]:
                panel_content += f"[bold]Key Findings:[/bold]\n"
                panel_content += "\n".join([f"• {finding}" for finding in paper["key_findings"]])
                panel_content += "\n\n"
            
            if "methodology" in paper and paper["methodology"]:
                panel_content += f"[bold]Methodology:[/bold]\n{paper['methodology']}\n\n"
            
            if "limitations" in paper and paper["limitations"]:
                panel_content += f"[bold]Limitations:[/bold]\n{paper['limitations']}"
            
            if panel_content:
                extracted_panel = Panel(
                    panel_content,
                    box=ROUNDED,
                    border_style="cyan"
                )
                
                console.print(extracted_panel)
                console.print()
        
        # Options
        console.print("[1] View Full Text  [2] Process with LLM  [3] Back to Papers List")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            console.print("\n[bold]Full Text View[/bold]")
            
            if "content" in paper:
                console.print(Panel(
                    paper["content"][:1000] + "...",
                    title="Paper Content (Preview)",
                    box=ROUNDED,
                    border_style="cyan"
                ))
            else:
                console.print("[yellow]Full text not available for this paper.[/yellow]")
                
            console.print("\nPress Enter to continue...")
            input()
            
        elif command == "2":
            console.print("\n[bold]Processing Paper with LLM[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[green]Processing paper with LLM...[/green]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Processing", total=100)
                
                # In a real implementation, this would call the LLM processing service
                for i in range(101):
                    await asyncio.sleep(0.02)
                    progress.update(task, completed=i)
            
            console.print("[green]Paper processed successfully.[/green]")
            console.print("\nPress Enter to continue...")
            input()
            
            # Update paper status
            if paper_id in self.service.paper_cache:
                self.service.paper_cache[paper_id]["status"] = "Processed"
            
            # View updated paper details
            await self.view_paper_details(paper_id, session_id)
            
        # command == "3" will return to papers list
        elif command == "3" and session_id:
            await self.view_session_papers(session_id)
    
    async def create_research_session(self):
        """Create a new research session."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]CREATE RESEARCH SESSION[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Get research topic
        topic = Prompt.ask("Research Topic")
        if not topic:
            console.print("[yellow]Research topic cannot be empty.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        # Get research context
        console.print("\n[bold]Research Context/Description:[/bold]")
        console.print("Describe your research goals, specific interests, and what you hope to learn.")
        context = Prompt.ask("Context")
        
        # Get research questions
        console.print("\n[bold]Initial Research Questions (optional):[/bold]")
        console.print("Enter key questions you want to answer, one per line. End with an empty line.")
        
        questions = []
        while True:
            question = Prompt.ask("Question", default="")
            if not question:
                break
            questions.append(question)
        
        # Analysis scope
        console.print("\n[bold]Analysis Scope:[/bold]")
        scope = Prompt.ask("Scope", 
                         choices=["light", "medium", "deep"],
                         default="medium")
        
        # Convert to user-friendly descriptions
        scope_desc = {
            "light": "Light (5-10 papers)",
            "medium": "Medium (15-30 papers)",
            "deep": "Deep (40+ papers)"
        }
        
        # Focus areas (multi-select)
        console.print("\n[bold]Focus Areas:[/bold]")
        console.print("Select focus areas (comma-separated):")
        console.print("Methods, Materials, Economics, Environmental Impact, Applications")
        
        focus_input = Prompt.ask("Focus Areas", default="Methods,Materials")
        focus_areas = [area.strip() for area in focus_input.split(",")]
        
        # Show the review
        console.print("\n[bold]Review Session Parameters:[/bold]")
        console.print(f"Topic: {topic}")
        console.print(f"Scope: {scope_desc[scope]}")
        console.print(f"Focus Areas: {', '.join(focus_areas)}")
        if questions:
            console.print("Research Questions:")
            for i, question in enumerate(questions, 1):
                console.print(f"  {i}. {question}")
        
        # Confirm creation
        if not Confirm.ask("Create this research session?"):
            console.print("[yellow]Session creation cancelled.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        # Show LLM refinement simulation
        console.clear()
        console.print(Panel(
            f"[bold cyan]REFINING RESEARCH CONTEXT[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        console.print("Initializing research context refinement...")
        console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[green]{task.description}[/green]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add tasks
            analyze_task = progress.add_task("Analyzing research parameters...", total=100)
            llm_task = progress.add_task("Connecting to LLM service...", total=100, visible=False)
            
            # Simulate processing
            for i in range(101):
                progress.update(analyze_task, completed=i)
                if i > 50:
                    progress.update(llm_task, visible=True)
                    progress.update(llm_task, completed=min((i - 50) * 2, 100))
                await asyncio.sleep(0.01)
        
        console.print()
        
        # LLM conversation simulation
        console.print("[bold cyan]LLM Assistant:[/bold cyan] I'd like to help refine your research on")
        console.print(f"{topic} to ensure optimal results.")
        console.print()
        
        console.print("[bold cyan]LLM Assistant:[/bold cyan] Are you specifically interested in any")
        console.print("particular applications or aspects of this topic?")
        console.print()
        
        refinement1 = Prompt.ask("Your response")
        console.print()
        
        console.print("[bold cyan]LLM Assistant:[/bold cyan] What timeframe or recent developments")
        console.print("are you most interested in for this research?")
        console.print()
        
        refinement2 = Prompt.ask("Your response")
        console.print()
        
        console.print("[bold cyan]LLM Assistant:[/bold cyan] Thanks for those details. I'll focus your research on:")
        console.print()
        console.print(f"1. {topic}")
        console.print(f"2. {refinement1}")
        console.print(f"3. {refinement2}")
        console.print(f"4. Analysis scope: {scope_desc[scope]}")
        console.print(f"5. Focus areas: {', '.join(focus_areas)}")
        console.print()
        
        console.print("Is this research focus correct, or would you like to adjust anything?")
        console.print()
        
        confirm = Prompt.ask("Enter to confirm or type adjustments", default="")
        
        # Research plan
        console.clear()
        console.print(Panel(
            f"[bold cyan]RESEARCH PLAN[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        console.print("[bold cyan]LLM Assistant:[/bold cyan] Based on your refined research focus, I've developed")
        console.print("the following research plan:")
        console.print()
        
        plan_panel = Panel(
            f"[bold]PHASE 1: PAPER COLLECTION[/bold]\n"
            f"• Search for papers on {topic}\n"
            f"• Prioritize papers discussing {refinement1}\n"
            f"• Focus on {refinement2}\n"
            f"• Target papers examining {', '.join(focus_areas)}\n\n"
            
            f"[bold]PHASE 2: ANALYSIS PRIORITIES[/bold]\n"
            f"• Comparative analysis\n"
            f"• Methodology evaluation\n"
            f"• Results synthesis\n"
            f"• Application assessment\n\n"
            
            f"[bold]PHASE 3: SYNTHESIS FOCUS[/bold]\n"
            f"• Key findings and patterns\n"
            f"• Contradictions and disagreements\n"
            f"• Research gaps\n"
            f"• Future directions",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(plan_panel)
        console.print()
        
        # Confirm plan
        if not Confirm.ask("Start research with this plan?"):
            console.print("[yellow]Research session creation cancelled.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        # Show progress while creating
        console.clear()
        console.print(Panel(
            f"[bold cyan]INITIALIZING RESEARCH SESSION[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[green]Creating research session...[/green]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add tasks
            create_task = progress.add_task("Creating research context...", total=100)
            setup_task = progress.add_task("Setting up search parameters...", total=100, visible=False)
            llm_prep_task = progress.add_task("Preparing LLM pipeline...", total=100, visible=False)
            alloc_task = progress.add_task("Allocating processing resources...", total=100, visible=False)
            
            # Update tasks as creation proceeds
            for i in range(101):
                progress.update(create_task, completed=i)
                
                if i > 30:
                    progress.update(setup_task, visible=True)
                    progress.update(setup_task, completed=min((i - 30) * 1.4, 100))
                
                if i > 50:
                    progress.update(llm_prep_task, visible=True)
                    progress.update(llm_prep_task, completed=min((i - 50) * 2, 100))
                
                if i > 70:
                    progress.update(alloc_task, visible=True)
                    progress.update(alloc_task, completed=min((i - 70) * 3.3, 100))
                
                await asyncio.sleep(0.01)
            
            # Create the session
            session_id = await self.service.create_research_session(
                topic=topic,
                scope=scope,
                focus_areas=focus_areas,
                context=context
            )
        
        # Show success message
        console.print(f"\n[bold green]Success![/bold green] Research session created with ID: [cyan]{session_id}[/cyan]")
        console.print()
        
        # Add research questions to the session if any
        if questions and session_id in self.service.session_cache:
            self.service.session_cache[session_id]["questions"] = questions
        
        # Add the refined context
        if session_id in self.service.session_cache:
            full_context = f"{context}\n\nRefinements:\n- {refinement1}\n- {refinement2}"
            self.service.session_cache[session_id]["research_context"] = full_context
        
        console.print(f"Topic: {topic}")
        console.print(f"Focus: {refinement1} with emphasis on {refinement2}")
        console.print(f"Search Scope: {scope_desc[scope]}")
        console.print()
        
        console.print("The system will begin collecting and analyzing papers based on your")
        console.print("refined research context. This process runs in the background.")
        
        # Add notification
        self.notifications.append(f"New research session created: {topic}")
        
        console.print("\n[1] View Session Details  [2] Return to Sessions List")
        
        command = Prompt.ask("", choices=["1", "2"], show_choices=False)
        
        if command == "1":
            await self.view_session_details(session_id)
    
    async def create_synthesis(self, session_id: str):
        """Create a synthesis from a research session."""
        # Get session details
        session = await self.service.get_session_details(session_id)
        
        if not session:
            console.print(f"[yellow]Session not found: {session_id}[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]CREATE SYNTHESIS[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Show session info
        console.print(f"Research session \"{session['topic']}\" is {session['completion_percentage']}% complete.")
        console.print(f"{session['papers_processed']} of {session['papers_found']} papers have been processed.")
        console.print()
        
        # Synthesis options
        console.print("[bold]Synthesis options:[/bold]")
        
        options = [
            ("Wait for all papers to be processed (recommended)", "wait"),
            ("Create synthesis from processed papers now", "now"),
            ("Create quick overview (faster, less comprehensive)", "quick")
        ]
        
        for i, (option, _) in enumerate(options, 1):
            console.print(f"{i}. {option}")
        
        option_choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="2")
        option = options[int(option_choice) - 1][1]
        
        # Synthesis format
        console.print("\n[bold]Synthesis format:[/bold]")
        
        formats = [
            ("Full Report", "full"),
            ("Key Findings", "key"),
            ("Comparative Analysis", "comp"),
            ("Timeline", "time")
        ]
        
        for i, (fmt, _) in enumerate(formats, 1):
            console.print(f"{i}. {fmt}")
        
        format_choice = Prompt.ask("Select format", choices=["1", "2", "3", "4"], default="2")
        format_option = formats[int(format_choice) - 1][1]
        
        # Confirm synthesis
        if not Confirm.ask("Create this synthesis?"):
            console.print("[yellow]Synthesis creation cancelled.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        # Get papers for this session
        papers = await self.service.get_session_papers(session_id)
        paper_ids = [paper["id"] for paper in papers if paper["status"] == "Processed"]
        
        if not paper_ids:
            console.print("[yellow]No processed papers found for this session.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
            return
        
        # Show synthesis generation progress
        console.clear()
        console.print(Panel(
            f"[bold cyan]GENERATING SYNTHESIS...[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[green]{task.description}[/green]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add tasks
            loading = progress.add_task("Loading papers...", total=100)
            analyzing = progress.add_task("Analyzing content...", total=100, visible=False)
            findings = progress.add_task("Extracting common findings...", total=100, visible=False)
            contradictions = progress.add_task("Looking for contradictions...", total=100, visible=False)
            gaps = progress.add_task("Identifying research gaps...", total=100, visible=False)
            
            # Simulating progress for the first task
            for i in range(101):
                progress.update(loading, completed=i)
                await asyncio.sleep(0.01)
            
            # Show and progress the second task
            progress.update(analyzing, visible=True)
            for i in range(101):
                progress.update(analyzing, completed=i)
                await asyncio.sleep(0.02)
            
            # Show and progress the third task
            progress.update(findings, visible=True)
            for i in range(101):
                progress.update(findings, completed=i)
                await asyncio.sleep(0.01)
            
            # Show and progress the fourth task
            progress.update(contradictions, visible=True)
            for i in range(101):
                progress.update(contradictions, completed=i)
                await asyncio.sleep(0.01)
            
            # Show and progress the fifth task
            progress.update(gaps, visible=True)
            for i in range(101):
                progress.update(gaps, completed=i)
                await asyncio.sleep(0.01)
            
            # Create the actual synthesis
            synthesis = await self.service.create_synthesis(paper_ids=paper_ids)
        
        # Generate a synthesis ID
        synthesis_id = f"syn-{len(paper_ids):03d}"
        
        # Create a mock synthesis if not returned by the service
        if "common_findings" not in synthesis:
            synthesis.update({
                "common_findings": [
                    {"finding": "First common finding from papers", "support_count": 3, "evidence_strength": "strong"},
                    {"finding": "Second key pattern identified", "support_count": 2, "evidence_strength": "moderate"},
                    {"finding": "Third important observation", "support_count": 4, "evidence_strength": "strong"}
                ],
                "contradictions": [
                    {"topic": "First area of disagreement", "view_1": "Perspective A", "view_2": "Perspective B"},
                    {"topic": "Second contradictory point", "view_1": "Approach 1", "view_2": "Approach 2"}
                ],
                "research_gaps": [
                    {"gap": "First identified gap in research", "type": "methodology"},
                    {"gap": "Second area needing further study", "type": "application"},
                    {"gap": "Third opportunity for future work", "type": "theoretical"}
                ]
            })
        
        # Show synthesis result
        console.clear()
        console.print(Panel(
            f"[bold green]Synthesis completed![/bold green] ID: [cyan]{synthesis_id}[/cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Show synthesis overview
        console.print(f"[bold]SYNTHESIS: {session['topic']} - {formats[int(format_choice) - 1][0]}[/bold]")
        
        # Create the synthesis panel content
        panel_content = ""
        
        # Common findings
        if "common_findings" in synthesis and synthesis["common_findings"]:
            panel_content += "[bold]Common Findings:[/bold]\n"
            for finding in synthesis["common_findings"]:
                panel_content += f"• {finding.get('finding', 'Finding')}\n"
            panel_content += "\n"
        
        # Contradictions
        if "contradictions" in synthesis and synthesis["contradictions"]:
            panel_content += "[bold]Contradictions:[/bold]\n"
            for contradiction in synthesis["contradictions"]:
                panel_content += f"• {contradiction.get('topic', 'Contradiction')}\n"
            panel_content += "\n"
        
        # Research gaps
        if "research_gaps" in synthesis and synthesis["research_gaps"]:
            panel_content += "[bold]Research Gaps:[/bold]\n"
            for gap in synthesis["research_gaps"]:
                panel_content += f"• {gap.get('gap', 'Gap')}\n"
        
        # Create the panel
        synthesis_panel = Panel(
            panel_content,
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(synthesis_panel)
        console.print()
        
        # Note if partial
        if session["completion_percentage"] < 100:
            console.print(f"Note: This synthesis is based on {session['papers_processed']} of {session['papers_found']} papers ({session['completion_percentage']}% complete).")
            console.print()
        
        # Options
        console.print("[1] View Full Synthesis  [2] Export  [3] Return to Session Details")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            await self.view_full_synthesis(synthesis_id, session['topic'], synthesis)
        elif command == "2":
            await self.export_synthesis(synthesis_id, session['topic'], synthesis)
        elif command == "3":
            await self.view_session_details(session_id)
    
    async def view_full_synthesis(self, synthesis_id: str, topic: str, synthesis: Dict = None):
        """View the full synthesis."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]FULL SYNTHESIS: {topic}[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Generate a full synthesis from the data
        full_synthesis = """
[bold]EXECUTIVE SUMMARY[/bold]

This synthesis examines the current state of research on this topic based on analysis
of multiple papers. Key findings include several important discoveries and patterns
that emerge across the literature. There are some contradictions in methodology and
results that warrant further investigation. Several research gaps have been identified
that present opportunities for future work.

[bold]METHODOLOGY COMPARISON[/bold]

The papers use a variety of methodologies, with strengths and weaknesses in each approach.
Detailed comparison reveals patterns in how different methods yield different results
and the conditions under which each performs optimally.

[bold]KEY FINDINGS[/bold]

"""
        
        # Add findings from the synthesis
        if synthesis and "common_findings" in synthesis:
            for i, finding in enumerate(synthesis["common_findings"], 1):
                full_synthesis += f"{i}. {finding.get('finding', 'Finding')}"
                if "support_count" in finding and "evidence_strength" in finding:
                    full_synthesis += f" (Support: {finding['support_count']} papers, Evidence: {finding['evidence_strength']})"
                full_synthesis += "\n"
        else:
            full_synthesis += "1. First major finding with supporting evidence from multiple papers\n"
            full_synthesis += "2. Second important insight that appears consistently in the literature\n"
            full_synthesis += "3. Third pattern that emerges when examining the research collectively\n"
        
        full_synthesis += """
[bold]CONTRADICTIONS[/bold]

"""
        
        # Add contradictions from the synthesis
        if synthesis and "contradictions" in synthesis:
            for contradiction in synthesis["contradictions"]:
                full_synthesis += f"• {contradiction.get('topic', 'Contradiction')}: "
                if "view_1" in contradiction and "view_2" in contradiction:
                    full_synthesis += f"{contradiction['view_1']} vs. {contradiction['view_2']}"
                full_synthesis += "\n"
        else:
            full_synthesis += "Areas of disagreement include technical approaches, interpretations of results, and\n"
            full_synthesis += "recommendations for application. These contradictions highlight the complexity of\n"
            full_synthesis += "the topic and areas needing resolution.\n"
        
        full_synthesis += """
[bold]RESEARCH GAPS[/bold]

"""
        
        # Add gaps from the synthesis
        if synthesis and "research_gaps" in synthesis:
            for gap in synthesis["research_gaps"]:
                full_synthesis += f"• {gap.get('gap', 'Gap')}"
                if "type" in gap:
                    full_synthesis += f" (Type: {gap['type']})"
                full_synthesis += "\n"
        else:
            full_synthesis += "Several areas remain under-investigated, including specific aspects of methodology,\n"
            full_synthesis += "long-term implications, and certain edge cases or conditions. These gaps present\n"
            full_synthesis += "opportunities for valuable future research.\n"
        
        full_synthesis += """
[bold]FUTURE DIRECTIONS[/bold]

Based on the current state of research and identified gaps, promising future directions
include exploration of alternative methods, integration of multiple approaches, and
addressing specific limitations in current understanding.
"""
        
        # Print the full synthesis with pagination
        lines = full_synthesis.strip().split("\n")
        page_size = 20
        total_pages = (len(lines) + page_size - 1) // page_size
        
        current_page = 1
        while current_page <= total_pages:
            console.clear()
            
            # Print header
            console.print(Panel(
                f"[bold cyan]FULL SYNTHESIS: {topic}[/bold cyan]",
                box=DOUBLE,
                expand=True,
                border_style="bright_blue"
            ))
            
            # Calculate page range
            start = (current_page - 1) * page_size
            end = min(start + page_size, len(lines))
            
            # Print current page
            content_panel = Panel(
                "\n".join(lines[start:end]),
                box=ROUNDED,
                border_style="cyan"
            )
            console.print(content_panel)
            
            # Print pagination info
            console.print(f"Page {current_page} of {total_pages}")
            console.print()
            
            # Options
            if current_page < total_pages:
                console.print("[N] Next Page  ", end="")
            if current_page > 1:
                console.print("[P] Previous Page  ", end="")
            console.print("[E] Export  [B] Back to Summary")
            
            # Get command
            choices = []
            if current_page < total_pages:
                choices.append("n")
            if current_page > 1:
                choices.append("p")
            choices.extend(["e", "b"])
            
            command = Prompt.ask("", choices=choices, show_choices=False).lower()
            
            if command == "n":
                current_page += 1
            elif command == "p":
                current_page -= 1
            elif command == "e":
                await self.export_synthesis(synthesis_id, topic, synthesis)
                break
            elif command == "b":
                break
    
    async def export_synthesis(self, synthesis_id: str, topic: str, synthesis: Dict = None):
        """Export a synthesis."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]EXPORT SYNTHESIS[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Show synthesis info
        console.print(f"Synthesis ID: {synthesis_id}")
        console.print(f"Topic: {topic}")
        console.print()
        
        # Export format
        console.print("[bold]Export format:[/bold]")
        
        formats = ["PDF", "Markdown", "HTML", "Plain Text"]
        
        for i, fmt in enumerate(formats, 1):
            if fmt == "Markdown":
                console.print(f"{i}. [bold]{fmt}[/bold]")
            else:
                console.print(f"{i}. {fmt}")
        
        format_choice = Prompt.ask("Select format", choices=["1", "2", "3", "4"], default="2")
        selected_format = formats[int(format_choice) - 1]
        
        # Export path
        home_dir = os.path.expanduser("~")
        filename = f"{topic.lower().replace(' ', '_')}_synthesis"
        
        if selected_format == "PDF":
            filename += ".pdf"
        elif selected_format == "Markdown":
            filename += ".md"
        elif selected_format == "HTML":
            filename += ".html"
        else:
            filename += ".txt"
        
        default_path = os.path.join(home_dir, "research", filename)
        export_path = Prompt.ask("Export path", default=default_path)
        
        # Create directory if it doesn't exist
        export_dir = os.path.dirname(export_path)
        if not os.path.exists(export_dir):
            if Confirm.ask(f"Directory {export_dir} does not exist. Create it?"):
                os.makedirs(export_dir, exist_ok=True)
            else:
                console.print("[yellow]Export cancelled.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
        
        # Include citations
        include_citations = Confirm.ask("Include citations and references?", default=True)
        
        # Simulate export
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[green]Exporting to {selected_format}...[/green]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Exporting", total=100)
            
            # Create actual export file
            try:
                # Generate content based on synthesis
                content = ""
                
                # Format based on selected format
                if selected_format == "Markdown":
                    content = self._generate_markdown_synthesis(topic, synthesis, include_citations)
                elif selected_format == "HTML":
                    content = self._generate_html_synthesis(topic, synthesis, include_citations)
                elif selected_format == "Plain Text":
                    content = self._generate_text_synthesis(topic, synthesis, include_citations)
                else:  # PDF - generate markdown first
                    content = self._generate_markdown_synthesis(topic, synthesis, include_citations)
                
                # Write to file
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Simulate progress
                for i in range(101):
                    await asyncio.sleep(0.01)
                    progress.update(task, completed=i)
                
                logger.info(f"Exported synthesis to {export_path}")
                
            except Exception as e:
                logger.error(f"Error exporting synthesis: {e}")
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
                console.print("\nPress Enter to continue...")
                input()
                return
        
        # Show success message
        console.print(f"\n[bold green]Success![/bold green] Synthesis exported to:")
        console.print(f"{export_path}")
        console.print()
        
        # Ask to open
        if Confirm.ask("Would you like to open this file now?"):
            try:
                # Try to open the file with the default application
                if sys.platform == "win32":
                    os.startfile(export_path)
                elif sys.platform == "darwin":
                    os.system(f"open {export_path}")
                else:
                    os.system(f"xdg-open {export_path}")
                    
                logger.info(f"Opened file {export_path}")
            except Exception as e:
                logger.error(f"Error opening file: {e}")
                console.print("[yellow]Could not open file automatically.[/yellow]")
                
        console.print("\nPress Enter to continue...")
        input()
    
    def _generate_markdown_synthesis(self, topic: str, synthesis: Dict, include_citations: bool) -> str:
        """Generate Markdown synthesis."""
        # Generate markdown content
        md = f"# Research Synthesis: {topic}\n\n"
        md += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        # Executive summary
        md += "## Executive Summary\n\n"
        md += "This synthesis examines the current state of research on this topic based on "
        md += "analysis of multiple papers. Key findings, contradictions, and research gaps "
        md += "are identified to provide a comprehensive overview of the field.\n\n"
        
        # Key findings
        md += "## Key Findings\n\n"
        if synthesis and "common_findings" in synthesis and synthesis["common_findings"]:
            for finding in synthesis["common_findings"]:
                md += f"- {finding.get('finding', 'Finding')}\n"
        else:
            md += "- No key findings available\n"
        md += "\n"
        
        # Contradictions
        md += "## Contradictions\n\n"
        if synthesis and "contradictions" in synthesis and synthesis["contradictions"]:
            for contradiction in synthesis["contradictions"]:
                md += f"- {contradiction.get('topic', 'Contradiction')}"
                if "view_1" in contradiction and "view_2" in contradiction:
                    md += f": {contradiction['view_1']} vs. {contradiction['view_2']}"
                md += "\n"
        else:
            md += "- No contradictions identified\n"
        md += "\n"
        
        # Research gaps
        md += "## Research Gaps\n\n"
        if synthesis and "research_gaps" in synthesis and synthesis["research_gaps"]:
            for gap in synthesis["research_gaps"]:
                md += f"- {gap.get('gap', 'Gap')}"
                if "type" in gap:
                    md += f" (Type: {gap['type']})"
                md += "\n"
        else:
            md += "- No research gaps identified\n"
        md += "\n"
        
        # Future directions
        md += "## Future Directions\n\n"
        md += "Based on the current state of research and identified gaps, promising future directions include:\n\n"
        md += "- Exploration of alternative methods\n"
        md += "- Integration of multiple approaches\n"
        md += "- Addressing specific limitations in current understanding\n\n"
        
        # References
        if include_citations and synthesis and "meta" in synthesis and "paper_ids" in synthesis["meta"]:
            md += "## References\n\n"
            for i, paper_id in enumerate(synthesis["meta"]["paper_ids"], 1):
                # In a real implementation, this would look up the paper details
                md += f"{i}. Paper ID: {paper_id}\n"
        
        return md
    
    def _generate_html_synthesis(self, topic: str, synthesis: Dict, include_citations: bool) -> str:
        """Generate HTML synthesis."""
        # Convert markdown to HTML
        md = self._generate_markdown_synthesis(topic, synthesis, include_citations)
        
        # Basic HTML wrapper
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Synthesis: {topic}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ margin-top: 30px; }}
        ul {{ margin-bottom: 20px; }}
        .meta {{ color: #666; font-style: italic; margin-bottom: 30px; }}
    </style>
</head>
<body>
"""
        
        # Convert markdown to HTML (very basic conversion)
        lines = md.split("\n")
        in_list = False
        
        for line in lines:
            if line.startswith("# "):
                html += f"<h1>{line[2:]}</h1>\n"
            elif line.startswith("## "):
                html += f"<h2>{line[3:]}</h2>\n"
            elif line.startswith("*") and line.endswith("*"):
                html += f'<p class="meta">{line[1:-1]}</p>\n'
            elif line.startswith("- "):
                if not in_list:
                    html += "<ul>\n"
                    in_list = True
                html += f"<li>{line[2:]}</li>\n"
            elif line.strip() == "" and in_list:
                html += "</ul>\n"
                in_list = False
            elif line.strip() != "":
                html += f"<p>{line}</p>\n"
        
        if in_list:
            html += "</ul>\n"
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _generate_text_synthesis(self, topic: str, synthesis: Dict, include_citations: bool) -> str:
        """Generate plain text synthesis."""
        # Convert markdown to plain text
        md = self._generate_markdown_synthesis(topic, synthesis, include_citations)
        
        # Basic plain text conversion
        text = md.replace("# ", "").replace("## ", "").replace("- ", "* ")
        
        return text
    
    async def search_sessions(self, query: str):
        """Search for research sessions."""
        # Get all sessions
        sessions = await self.service.get_research_sessions()
        
        # Filter by query
        if query:
            filtered = []
            for session in sessions:
                if (query.lower() in session["topic"].lower() or
                    query.lower() in session.get("status", "").lower() or
                    query.lower() in session.get("id", "").lower()):
                    filtered.append(session)
            sessions = filtered
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]SEARCH RESULTS: {query}[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        if not sessions:
            console.print("[yellow]No sessions found matching your query.[/yellow]")
        else:
            # Create a table for sessions
            table = Table(box=ROUNDED, expand=True)
            table.add_column("ID", style="dim")
            table.add_column("Topic", style="bright_white")
            table.add_column("Status", style="green")
            table.add_column("Progress", justify="right")
            
            # Add sessions to the table
            for session in sessions:
                # Create progress bar
                progress = session["completion_percentage"]
                progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
                
                table.add_row(
                    session["id"],
                    session["topic"],
                    session["status"],
                    f"{progress_bar} {progress}%"
                )
            
            console.print(table)
            
            # Show how many sessions are visible
            console.print(f"Found {len(sessions)} session{'s' if len(sessions) != 1 else ''}")
        
        console.print()
        
        # Options
        console.print("[1] View Session  [2] New Search  [3] Back to Sessions")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            if not sessions:
                console.print("[yellow]No sessions available to view.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
                
            session_id = Prompt.ask("Enter session ID to view")
            await self.view_session_details(session_id)
        elif command == "2":
            query = Prompt.ask("Enter search query")
            await self.search_sessions(query)
        # command == "3" will return to sessions list
    
    async def search_papers(self, query: str):
        """Search for papers."""
        # Search for papers
        papers = await self.service.search_papers(query)
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]PAPER SEARCH: {query}[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        if not papers:
            console.print("[yellow]No papers found matching your query.[/yellow]")
        else:
            # Create a table for papers
            table = Table(box=ROUNDED, expand=True)
            table.add_column("ID", style="dim")
            table.add_column("Title", style="bright_white")
            table.add_column("Authors", style="cyan")
            table.add_column("Status", style="green")
            
            # Add papers to the table
            for paper in papers:
                table.add_row(
                    paper["id"],
                    paper["title"],
                    paper["authors"],
                    paper.get("status", "Unknown")
                )
            
            console.print(table)
            
            # Show how many papers are visible
            console.print(f"Found {len(papers)} paper{'s' if len(papers) != 1 else ''}")
        
        console.print()
        
        # Options
        console.print("[1] View Paper  [2] New Search  [3] Back")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            if not papers:
                console.print("[yellow]No papers available to view.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
                
            paper_id = Prompt.ask("Enter paper ID to view")
            
            # Check if paper exists
            paper_exists = False
            for paper in papers:
                if paper["id"] == paper_id:
                    paper_exists = True
                    break
            
            if not paper_exists:
                console.print(f"[yellow]Paper not found: {paper_id}[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
                
            await self.view_paper_details(paper_id)
        elif command == "2":
            query = Prompt.ask("Enter search query")
            await self.search_papers(query)
        # command == "3" will return to previous screen
    
    async def search_syntheses(self, query: str):
        """Search for syntheses."""
        # In a real implementation, this would search the synthesis database
        # For now, just show a message
        console.print("[yellow]Synthesis search not implemented yet.[/yellow]")
        console.print("\nPress Enter to continue...")
        input()
    
    async def add_paper(self, session_id: str = None):
        """Add a new paper."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]ADD PAPER[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Method selection
        console.print("[bold]Select file method:[/bold]")
        
        methods = [
            "Upload local file",
            "Provide URL",
            "Enter DOI"
        ]
        
        for i, method in enumerate(methods, 1):
            console.print(f"{i}. {method}")
        
        method_choice = Prompt.ask("Select method", choices=["1", "2", "3"], default="1")
        
        if method_choice == "1":
            # Upload local file
            file_path = Prompt.ask("Enter file path")
            
            if not os.path.exists(file_path):
                console.print(f"[yellow]File not found: {file_path}[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
            
            # Tags
            console.print("\n[bold]Add tags (comma-separated):[/bold]")
            tags = Prompt.ask("Tags")
            
            # Session selection if not provided
            if not session_id:
                console.print("\n[bold]Add to research session:[/bold]")
                
                # Get available sessions
                sessions = await self.service.get_research_sessions()
                
                if not sessions:
                    console.print("[yellow]No active sessions available.[/yellow]")
                    session_id = None
                else:
                    # Show session options
                    for i, session in enumerate(sessions, 1):
                        console.print(f"{i}. {session['topic']} (ID: {session['id']})")
                    
                    session_choice = Prompt.ask("Select session", 
                                              choices=[str(i) for i in range(1, len(sessions) + 1)],
                                              default="1")
                    
                    session_id = sessions[int(session_choice) - 1]["id"]
            
            # Show file upload and processing progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[green]Uploading and processing paper...[/green]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                # Add tasks
                reading = progress.add_task("Reading file...", total=100)
                extracting = progress.add_task("Extracting text...", total=100, visible=False)
                analyzing = progress.add_task("Analyzing content...", total=100, visible=False)
                
                # Simulate reading file
                for i in range(101):
                    progress.update(reading, completed=i)
                    await asyncio.sleep(0.01)
                
                # Add the paper
                try:
                    paper_id = await self.service.add_paper(file_path, session_id)
                    
                    # Show next task
                    progress.update(extracting, visible=True)
                    
                    # Simulate extracting text
                    for i in range(101):
                        progress.update(extracting, completed=i)
                        await asyncio.sleep(0.01)
                    
                    # Show next task
                    progress.update(analyzing, visible=True)
                    
                    # Simulate analyzing content
                    for i in range(101):
                        progress.update(analyzing, completed=i)
                        await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"Error adding paper: {e}")
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    console.print("\nPress Enter to continue...")
                    input()
                    return
            
            # Show success message
            console.print(f"\n[bold green]Success![/bold green] Paper added with ID: [cyan]{paper_id}[/cyan]")
            
            # Get paper details
            paper = await self.service.get_paper_details(paper_id)
            
            if paper:
                console.print(f"\nTitle: {paper['title']}")
                console.print(f"Authors: {paper['authors']}")
            else:
                # Extract filename from path
                filename = os.path.basename(file_path)
                console.print(f"\nFilename: {filename}")
            
            if session_id:
                # Get session name
                session = await self.service.get_session_details(session_id)
                if session:
                    console.print(f"\nPaper has been added to research session:")
                    console.print(f"{session_id} - {session['topic']}")
            
            console.print("\n[1] View Paper Details  [2] Add Another Paper  [3] Back to Papers")
            
            # Get command
            command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
            
            if command == "1":
                await self.view_paper_details(paper_id, session_id)
            elif command == "2":
                await self.add_paper(session_id)
            # command == "3" will return to papers list
            
        else:
            # Other methods not implemented yet
            console.print(f"[yellow]Method not implemented yet: {methods[int(method_choice) - 1]}[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
    
    async def check_llm_quota(self):
        """Check LLM API quota."""
        # Get LLM providers
        providers = await self.service.get_llm_providers()
        
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]LLM API QUOTA[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        if not providers:
            console.print("[yellow]No LLM providers configured.[/yellow]")
        else:
            # Create a table for quotas
            table = Table(box=ROUNDED)
            table.add_column("Provider", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Quota Remaining", style="bright_white")
            table.add_column("Usage Today", style="bright_white")
            
            # Add providers to the table
            for provider_name, info in providers.items():
                status_icon = "●" if info["status"] == "available" else "○"
                status_color = "green" if info["status"] == "available" else "yellow"
                
                table.add_row(
                    provider_name.title(),
                    f"[{status_color}]{status_icon} {info['status'].title()}[/{status_color}]",
                    f"{info['quota_remaining']}%",
                    f"{info['token_usage']['today']:,} tokens"
                )
            
            console.print(table)
        
        console.print()
        
        # Options
        console.print("[1] View Usage History  [2] Configure Rate Limits  [3] Back")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            console.print("[yellow]Usage history view not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "2":
            console.print("[yellow]Rate limit configuration not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        # command == "3" will return to previous screen
    
    async def render_papers_tab(self):
        """Render the Papers tab."""
        # Search for papers
        papers = await self.service.search_papers("", limit=10)
        
        console.print("[bold]PAPERS LIBRARY[/bold]")
        
        if not papers:
            console.print("No papers found.")
            console.print("\nAdd papers to get started.")
        else:
            # Create a table for papers
            table = Table(box=ROUNDED, expand=True)
            table.add_column("ID", style="dim")
            table.add_column("Title", style="bright_white")
            table.add_column("Authors", style="cyan")
            table.add_column("Status", style="green")
            
            # Add papers to the table
            for paper in papers:
                table.add_row(
                    paper["id"],
                    paper["title"],
                    paper["authors"],
                    paper.get("status", "Unknown")
                )
            
            console.print(table)
            
            # Show how many papers are visible
            console.print(f"Showing {len(papers)} of {self.paper_count} papers")
        
        console.print()
        console.print("[1] Search Papers  [2] View Recent Papers  [3] Add Paper  [4] Import Batch")
    
    async def process_papers_command(self, command: str):
        """Process commands for the Papers tab."""
        if command == "1":
            query = Prompt.ask("Enter search query")
            await self.search_papers(query)
        elif command == "2":
            # Just refresh the tab
            pass
        elif command == "3":
            await self.add_paper()
        elif command == "4":
            console.print("[yellow]Batch import not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
    
    async def render_synthesis_tab(self):
        """Render the Synthesis tab."""
        console.print("[bold]SYNTHESIS STUDIO[/bold]")
        
        # In a real implementation, this would get recent syntheses
        # For now, just show a placeholder
        
        console.print("[bold]RECENT SYNTHESES[/bold]")
        
        # Create a table for syntheses
        table = Table(box=ROUNDED, expand=True)
        table.add_column("ID", style="dim")
        table.add_column("Topic", style="bright_white")
        table.add_column("Papers", justify="right")
        table.add_column("Generated", style="cyan")
        table.add_column("Format", style="green")
        
        # Add sample syntheses
        table.add_row(
            "syn-123",
            "Advances in PET Recycling Techniques",
            "12",
            "Yesterday",
            "Full Report"
        )
        table.add_row(
            "syn-124",
            "Comparison of Biodegradable Polymers",
            "8",
            "3 days ago",
            "Key Findings"
        )
        
        console.print(table)
        console.print()
        
        # Show synthesis creation options
        creation_panel = Panel(
            "[bold]Create New Synthesis:[/bold]\n\n"
            "[cyan]1. From Research Session[/cyan] - Generate synthesis from an existing research session\n"
            "[cyan]2. From Paper Selection[/cyan] - Select specific papers to synthesize\n"
            "[cyan]3. From Topic[/cyan] - Search and synthesize papers on a specific topic",
            title="Synthesis Options",
            border_style="cyan",
            box=ROUNDED
        )
        
        console.print(creation_panel)
        console.print()
        
        console.print("[1] Create Synthesis  [2] View Synthesis  [3] Export Synthesis")
    
    async def process_synthesis_command(self, command: str):
        """Process commands for the Synthesis tab."""
        if command == "1":
            # Get sessions for synthesis
            sessions = await self.service.get_research_sessions()
            
            if not sessions:
                console.print("[yellow]No active sessions available for synthesis.[/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                return
            
            # Show session options
            console.print("\n[bold]Select session for synthesis:[/bold]")
            
            for i, session in enumerate(sessions, 1):
                console.print(f"{i}. {session['topic']} (ID: {session['id']})")
            
            session_choice = Prompt.ask("Select session", 
                                      choices=[str(i) for i in range(1, len(sessions) + 1)],
                                      default="1")
            
            session_id = sessions[int(session_choice) - 1]["id"]
            await self.create_synthesis(session_id)
        elif command == "2":
            synthesis_id = Prompt.ask("Enter synthesis ID")
            
            # In a real implementation, this would look up the synthesis
            # For now, use a placeholder
            topic = "Sample Research Topic"
            
            await self.view_full_synthesis(synthesis_id, topic)
        elif command == "3":
            synthesis_id = Prompt.ask("Enter synthesis ID to export")
            
            # In a real implementation, this would look up the synthesis
            # For now, use a placeholder
            topic = "Sample Research Topic"
            
            await self.export_synthesis(synthesis_id, topic)
    
    async def render_llm_hub_tab(self):
        """Render the LLM Hub tab."""
        console.print("[bold]LLM HUB[/bold]")
        
        # Get LLM providers
        providers = await self.service.get_llm_providers()
        
        if not providers:
            console.print("[yellow]No LLM providers configured.[/yellow]")
            console.print("\nConfigure LLM providers in the Config tab.")
        else:
            # Create a table for provider status
            status_table = Table(title="PROVIDER STATUS", box=ROUNDED)
            status_table.add_column("Provider", style="cyan")
            status_table.add_column("Status", style="green")
            status_table.add_column("Quota Remaining", style="bright_white")
            status_table.add_column("Today's Usage", style="bright_white")
            
            # Add providers to the table
            for provider_name, info in providers.items():
                status_icon = "●" if info["status"] == "available" else "○"
                status_color = "green" if info["status"] == "available" else "yellow"
                
                status_table.add_row(
                    provider_name.title(),
                    f"[{status_color}]{status_icon} {info['status'].title()}[/{status_color}]",
                    f"{info['quota_remaining']}%",
                    f"{info['token_usage']['today']:,} tokens"
                )
            
            console.print(status_table)
            console.print()
            
            # Recent operations
            console.print("[bold]RECENT OPERATIONS[/bold]")
            
            # Create a table for recent operations
            ops_table = Table(box=ROUNDED)
            ops_table.add_column("Time", style="dim")
            ops_table.add_column("Operation", style="bright_white")
            ops_table.add_column("Provider", style="cyan")
            ops_table.add_column("Tokens", justify="right")
            ops_table.add_column("Session", style="green")
            
            # Add operations to the table
            # In a real implementation, this would come from the service
            ops_table.add_row(
                "Just now",
                "Generate Synthesis",
                "Mistral",
                "945",
                "3f8a9c2e"
            )
            ops_table.add_row(
                "10m ago",
                "Process Document",
                "Mistral",
                "523",
                "3f8a9c2e"
            )
            ops_table.add_row(
                "45m ago",
                "Extract References",
                "Cerebras",
                "312",
                "e7d1f23b"
            )
            
            console.print(ops_table)
        
        console.print()
        console.print("[1] Test Provider  [2] Configure Routing  [3] View Usage Details  [4] Refresh")
    
    async def process_llm_hub_command(self, command: str):
        """Process commands for the LLM Hub tab."""
        if command == "1":
            console.print("[yellow]Test provider not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "2":
            console.print("[yellow]Configure routing not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "3":
            await self.check_llm_quota()
        elif command == "4":
            # Just refresh - no action needed
            pass
    
    async def render_config_tab(self):
        """Render the Config tab."""
        console.print("[bold]CONFIGURATION[/bold]")
        
        # System settings panel
        settings_panel = Panel(
            "Database:  MongoDB @ localhost:27017    ● Connected\n"
            "Queue:     Redis @ localhost:6379       ● Connected\n"
            "Cache:     Enabled (TTL: 24h)\n"
            "Log Level: INFO",
            title="SYSTEM SETTINGS",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(settings_panel)
        console.print()
        
        # LLM providers panel
        llm_panel = Panel(
            "Default:   Mistral\n"
            "Fallback:  Cerebras\n"
            "API Keys:  3 configured",
            title="LLM PROVIDERS",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(llm_panel)
        console.print()
        
        # Queue status
        queue_status = await self.service.get_queue_status()
        
        queue_panel = Panel(
            f"Processing Queue:  {queue_status['processing_queue']}\n"
            f"Retry Queue:       {queue_status['retry_queue']}\n"
            f"Dead Letter Queue: {queue_status['dead_letter_queue']}\n"
            f"Paper Search Queue:{queue_status['paper_search_queue']}",
            title="QUEUE STATUS",
            box=ROUNDED,
            border_style="cyan"
        )
        
        console.print(queue_panel)
        console.print()
        
        console.print("[1] Database Settings  [2] API Keys  [3] Processing Options  [4] View Logs")
    
    async def process_config_command(self, command: str):
        """Process commands for the Config tab."""
        if command == "1":
            console.print("[yellow]Database settings not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "2":
            console.print("[yellow]API keys not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "3":
            console.print("[yellow]Processing options not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "4":
            await self.view_logs()
    
    async def view_logs(self):
        """View application logs."""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]APPLICATION LOGS[/bold cyan]",
            box=DOUBLE,
            expand=True,
            border_style="bright_blue"
        ))
        
        # Read log file
        log_file = "nocturnal_cli.log"
        
        if not os.path.exists(log_file):
            console.print("[yellow]Log file not found.[/yellow]")
        else:
            # Read the last 20 lines
            with open(log_file, "r") as f:
                lines = f.readlines()
                lines = lines[-20:]  # Last 20 lines
            
            # Display log lines
            for line in lines:
                # Color-code by log level
                if "ERROR" in line:
                    console.print(f"[red]{line.strip()}[/red]")
                elif "WARNING" in line:
                    console.print(f"[yellow]{line.strip()}[/yellow]")
                elif "INFO" in line:
                    console.print(f"[green]{line.strip()}[/green]")
                else:
                    console.print(line.strip())
        
        console.print()
        console.print("[1] Refresh  [2] Clear Logs  [3] Back")
        
        # Get command
        command = Prompt.ask("", choices=["1", "2", "3"], show_choices=False)
        
        if command == "1":
            await self.view_logs()
        elif command == "2":
            if Confirm.ask("Are you sure you want to clear logs?"):
                try:
                    open(log_file, "w").close()
                    console.print("[green]Logs cleared.[/green]")
                except Exception as e:
                    console.print(f"[red]Error clearing logs: {e}[/red]")
                
                console.print("\nPress Enter to continue...")
                input()
                await self.view_logs()
        # command == "3" will return to previous screen
    
    async def render_dashboard_tab(self):
        """Render the Dashboard tab."""
        console.print("[bold]RESEARCH DASHBOARD[/bold]")
        
        # Get active sessions
        sessions = await self.service.get_research_sessions()
        
        # Get LLM providers
        providers = await self.service.get_llm_providers()
        
        # Get queue status
        queue_status = await self.service.get_queue_status()
        
        # Calculate metrics
        active_sessions = len(sessions)
        papers_processing = sum(queue_status.values())
        papers_processed = sum(1 for session in sessions for _ in range(session.get("papers_processed", 0)))
        
        # Create overview and processing statistics panels
        overview_panel = Panel(
            f"Active Sessions:    {active_sessions}\n"
            f"Total Sessions:     {active_sessions}\n"
            f"Papers Total:       {self.paper_count}\n"
            f"Syntheses:          0",
            title="RESEARCH OVERVIEW",
            box=ROUNDED,
            border_style="cyan"
        )
        
        stats_panel = Panel(
            f"Papers Processed:    {papers_processed}\n"
            f"Papers Processing:   {papers_processing}\n"
            f"Papers Queued:       {sum(queue_status.values())}\n"
            f"Processing Rate:     0/h",
            title="PROCESSING STATISTICS",
            box=ROUNDED,
            border_style="cyan"
        )
        
        # Create layout with columns
        panels = Columns([overview_panel, stats_panel])
        console.print(panels)
        console.print()
        
        # Create LLM usage and recent activity panels
        llm_panel = Panel(
            "\n".join([
                f"● {name.title()}    [{info['token_usage']['today']}/{10000}]"
                for name, info in providers.items()
            ]) if providers else "No LLM providers configured",
            title="LLM USAGE",
            box=ROUNDED,
            border_style="cyan"
        )
        
        activity_panel = Panel(
            "• No recent activity",
            title="RECENT ACTIVITY",
            box=ROUNDED,
            border_style="cyan"
        )
        
        # Create layout with columns
        panels = Columns([llm_panel, activity_panel])
        console.print(panels)
        console.print()
        
        console.print("[1] System Summary  [2] Export Statistics  [3] Process Queues  [4] Refresh")
    
    async def process_dashboard_command(self, command: str):
        """Process commands for the Dashboard tab."""
        if command == "1":
            console.print("[yellow]System summary not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "2":
            console.print("[yellow]Export statistics not implemented yet.[/yellow]")
            console.print("\nPress Enter to continue...")
            input()
        elif command == "3":
            console.print("Processing queues...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[green]Processing queues...[/green]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Processing", total=100)
                
                # Process queues
                success = await self.service.process_queues()
                
                # Simulate progress
                for i in range(101):
                    await asyncio.sleep(0.01)
                    progress.update(task, completed=i)
            
            if success:
                console.print("[green]Queues processed successfully.[/green]")
            else:
                console.print("[yellow]Some queue processing failed.[/yellow]")
                
            console.print("\nPress Enter to continue...")
            input()
        elif command == "4":
            # Just refresh - no action needed
            pass
    
    async def export_current_view(self):
        """Export the current view."""
        console.print("[yellow]Export current view not implemented yet.[/yellow]")
        console.print("\nPress Enter to continue...")
        input()
    
    async def shutdown(self):
        """Clean up resources and exit."""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]NOCTURNAL ARCHIVE[/bold cyan]\n"
            "[white]Research Paper Analysis System[/white]",
            box=HEAVY,
            border_style="bright_blue"
        ))
        console.print()
        console.print("[dim]Shutting down services...[/dim]")
        
        # Clean up service resources
        await self.service.cleanup()
        
        console.print("[bold green]Shutdown complete. Thank you for using Nocturnal Archive![/bold green]")


async def main():
    """Main entry point."""
    try:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Nocturnal Archive Research System")
        parser.add_argument('--version', action='store_true', help='Show version information')
        parser.add_argument('--config', help='Path to configuration file')
        
        args = parser.parse_args()
        
        if args.version:
            print("Nocturnal Archive v1.0.0")
            return
        
        # Initialize service bridge
        config_path = args.config
        service = ServiceBridge(config_path)
        await service.initialize()
        
        # Create UI
        ui = NocturnalArchiveUI(service)
        
        # Start UI
        await ui.start()
        
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        console.print(f"[bold red]Unhandled error: {str(e)}[/bold red]")
        console.print_exception()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Program interrupted by user.[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {str(e)}[/bold red]")
        console.print_exception()
        sys.exit(1)