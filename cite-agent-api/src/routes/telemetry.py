"""Telemetry ingestion endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.services.telemetry_ingestor import (
    TelemetryAuthError,
    get_telemetry_authenticator,
    get_telemetry_ingestor,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/telemetry")


class TelemetryIngestRequest(BaseModel):
    """Incoming telemetry payload from the CLI."""

    model_config = ConfigDict(extra="allow")

    event: str = Field(..., min_length=1, max_length=128, description="Event name")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Client-side event timestamp",
    )
    session: Optional[str] = Field(None, max_length=128, description="Session identifier")
    account_id: Optional[str] = Field(None, max_length=128, description="Account identifier")
    client_version: Optional[str] = Field(None, max_length=64, description="CLI version string")
    platform: Optional[str] = Field(None, max_length=64, description="Client platform")

    @model_validator(mode="after")
    def validate_payload_size(self) -> "TelemetryIngestRequest":
        raw = json.dumps(self.model_dump(mode="json"), ensure_ascii=False)
        if len(raw.encode("utf-8")) > 65536:
            raise ValueError("Telemetry payload exceeds 64KB limit")
        return self


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:]
    return authorization


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryIngestRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_ingest_token: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Accept telemetry events from the CLI and persist them for analysis."""
    authenticator = get_telemetry_authenticator()
    token = _extract_bearer(authorization) or x_ingest_token

    try:
        token_hash = authenticator.authenticate(token)
    except TelemetryAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "telemetry_auth",
                "message": str(exc),
            },
        ) from exc

    ingestor = get_telemetry_ingestor()
    meta = {
        "trace_id": getattr(request.state, "trace_id", None),
        "client_ip": request.headers.get("x-forwarded-for") or (request.client.host if request.client else None),
        "user_agent": request.headers.get("user-agent"),
    }

    background_tasks.add_task(
        ingestor.persist,
        payload.model_dump(mode="python"),
        token_hash=token_hash,
        metadata={k: v for k, v in meta.items() if v},
    )

    logger.debug(
        "telemetry_ingest_accepted",
        telemetry_event=payload.event,
        token_hash=token_hash[:12],
        trace_id=meta.get("trace_id"),
    )

    return {
        "status": "accepted",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "trace_id": meta.get("trace_id"),
    }


class TelemetrySummary(BaseModel):
    """Aggregated view of telemetry activity."""

    total_events: int
    by_event: Dict[str, int]
    unique_sessions: int
    unique_accounts: int
    last_seen: Optional[str]
    days: int
    inspected_at: str


def _authenticate(authorization: Optional[str], x_ingest_token: Optional[str]) -> str:
    authenticator = get_telemetry_authenticator()
    token = _extract_bearer(authorization) or x_ingest_token
    try:
        return authenticator.authenticate(token)
    except TelemetryAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "telemetry_auth",
                "message": str(exc),
            },
        ) from exc


@router.get("/summary", response_model=TelemetrySummary)
async def telemetry_summary(
    authorization: Optional[str] = Header(default=None),
    x_ingest_token: Optional[str] = Header(default=None, convert_underscores=False),
    days: int = Query(7, ge=1, le=30),
):
    """Return aggregated telemetry metrics for the provided token."""

    token_hash = _authenticate(authorization, x_ingest_token)
    ingestor = get_telemetry_ingestor()
    summary = ingestor.summarize(token_hash=token_hash, days=days)
    logger.debug("telemetry_summary_fetch", token_hash=token_hash[:12], days=days)
    return summary


@router.get("/events")
async def telemetry_events(
    authorization: Optional[str] = Header(default=None),
    x_ingest_token: Optional[str] = Header(default=None, convert_underscores=False),
    limit: int = Query(100, ge=1, le=1000),
    days: int = Query(3, ge=1, le=30),
):
    """Return recent telemetry events for investigative workflows."""

    token_hash = _authenticate(authorization, x_ingest_token)
    ingestor = get_telemetry_ingestor()
    events = ingestor.iter_events(token_hash=token_hash, days=days, limit=limit)
    logger.debug(
        "telemetry_events_fetch",
        token_hash=token_hash[:12],
        requested_limit=limit,
        returned=len(events),
    )
    return {
        "events": events,
        "count": len(events),
        "limit": limit,
        "days": days,
    }


class TelemetryDailySeries(BaseModel):
    date: str
    total_events: int
    by_event: Dict[str, int]
    unique_sessions: int
    unique_accounts: int


class TelemetryDailyResponse(BaseModel):
    days: int
    series: List[TelemetryDailySeries]


@router.get("/daily", response_model=TelemetryDailyResponse)
async def telemetry_daily(
    authorization: Optional[str] = Header(default=None),
    x_ingest_token: Optional[str] = Header(default=None, convert_underscores=False),
    days: int = Query(7, ge=1, le=30),
):
    """Return per-day telemetry aggregates for the provided token."""

    token_hash = _authenticate(authorization, x_ingest_token)
    ingestor = get_telemetry_ingestor()
    series = ingestor.summarize_by_day(token_hash=token_hash, days=days)
    logger.debug(
        "telemetry_daily_fetch",
        token_hash=token_hash[:12],
        days=days,
        returned=len(series),
    )
    return TelemetryDailyResponse(days=days, series=series)
