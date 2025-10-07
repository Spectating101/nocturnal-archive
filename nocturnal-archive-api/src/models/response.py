"""Response models shared across API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Structured payload returned from the `/health` endpoint."""

    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str
    issues: Optional[List[str]] = None
