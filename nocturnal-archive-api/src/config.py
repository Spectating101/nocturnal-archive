"""
Configuration settings for FinSight
"""

import os

# Strict mode - no mocks in staging/prod
FINSIGHT_STRICT = os.getenv("FINSIGHT_STRICT", "0") == "1"

# API settings
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEMO_API_KEY = os.getenv("DEMO_API_KEY", "demo-key-123")

# SEC EDGAR settings
SEC_BASE_URL = "https://data.sec.gov"
SEC_USER_AGENT = "FinSight Financial Data (contact@nocturnal.dev)"

# Rate limiting
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "100"))
RATE_LIMIT_BURST_LIMIT = int(os.getenv("RATE_LIMIT_BURST_LIMIT", "10"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
