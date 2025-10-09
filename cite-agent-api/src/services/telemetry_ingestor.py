"""Telemetry ingestion utilities for the Nocturnal Archive API."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

import structlog

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)


class TelemetryAuthError(RuntimeError):
    """Raised when telemetry authentication fails."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_hashes(raw: Optional[str]) -> Set[str]:
    """Parse a comma or newline separated list of hashes."""
    if not raw:
        return set()
    parts = [segment.strip() for segment in raw.replace("\n", ",").split(",")]
    return {part.lower() for part in parts if part}


def _load_hashes_from_file(path: Optional[str]) -> Set[str]:
    if not path:
        return set()
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("telemetry_hash_file_missing", path=path)
        return set()
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("telemetry_hash_file_error", path=path, error=str(exc))
        return set()
    return _parse_hashes(content)


@dataclass
class TelemetryAuthenticator:
    """Validates telemetry ingestion tokens against an allow-list."""

    allowed_hashes: Set[str]
    accept_unlisted: bool

    @classmethod
    def from_environment(cls) -> "TelemetryAuthenticator":
        settings = get_settings()
        hashes: Set[str] = set()
        hashes |= _parse_hashes(os.getenv("NOCTURNAL_TELEMETRY_TOKEN_HASHES"))
        hashes |= _load_hashes_from_file(os.getenv("NOCTURNAL_TELEMETRY_TOKEN_HASH_FILE"))
        accept_all_env = os.getenv("NOCTURNAL_TELEMETRY_ACCEPT_ALL", "").lower() in {"1", "true", "yes", "on"}
        if not hashes and settings.environment.lower() in {"development", "test"}:
            accept_all_env = True
        return cls(allowed_hashes=hashes, accept_unlisted=accept_all_env)

    def authenticate(self, token: Optional[str]) -> str:
        if not token:
            raise TelemetryAuthError("Telemetry token is required", status_code=401)
        token = token.strip()
        if len(token) < 16:
            raise TelemetryAuthError("Telemetry token is malformed", status_code=400)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if self.allowed_hashes:
            if digest in self.allowed_hashes:
                return digest
            raise TelemetryAuthError("Telemetry token is not permitted", status_code=403)
        if self.accept_unlisted:
            return digest
        raise TelemetryAuthError("Telemetry ingestion is disabled", status_code=403)


class TelemetryIngestor:
    """Durable JSONL sink for telemetry events."""

    def __init__(self, storage_dir: Path, retention_days: int = 30) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = max(0, retention_days)
        self._lock = threading.Lock()

    def persist(self, event: Dict[str, Any], *, token_hash: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Persist a telemetry event to disk.

        Args:
            event: Validated telemetry payload.
            token_hash: SHA-256 digest of the bearer token.
            metadata: Additional metadata (request id, IP, user agent).
        """
        payload = dict(event)
        payload.setdefault("timestamp", datetime.now(timezone.utc))
        serialized = self._serialize_record(payload, token_hash=token_hash, metadata=metadata)
        file_path = self.storage_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"

        with self._lock:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.write("\n")
            self._enforce_retention()

        logger.info(
            "telemetry_ingested",
            event=payload.get("event"),
            token_hash=token_hash[:12],
            path=str(file_path),
        )
        return file_path

    def _serialize_record(
        self,
        payload: Dict[str, Any],
        *,
        token_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        record: Dict[str, Any] = dict(payload)
        ts = record.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            record["timestamp"] = ts.astimezone(timezone.utc).isoformat()
        record.setdefault("ingest_version", 1)
        record["received_at"] = datetime.now(timezone.utc).isoformat()
        record["token_hash"] = token_hash[:32]
        if metadata:
            record["meta"] = {k: v for k, v in metadata.items() if v is not None}
        return json.dumps(record, ensure_ascii=False)

    def _enforce_retention(self) -> None:
        if self.retention_days <= 0:
            return
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=self.retention_days)
        for file in self.storage_dir.glob("*.jsonl"):
            try:
                file_date = datetime.strptime(file.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    file.unlink()
                except Exception as exc:  # pragma: no cover - best effort cleanup
                    logger.warning("telemetry_retention_cleanup_failed", path=str(file), error=str(exc))

    def _iter_records(self, *, token_hash: Optional[str], days: int) -> Iterator[Dict[str, Any]]:
        days = max(1, days)
        cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
        token_short = token_hash[:32] if token_hash else None

        files = sorted(self.storage_dir.glob("*.jsonl"), reverse=True)
        for path in files:
            try:
                file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff_date:
                continue

            try:
                with path.open("r", encoding="utf-8") as handle:
                    lines = handle.readlines()
            except FileNotFoundError:
                continue
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("telemetry_iter_error", path=str(path), error=str(exc))
                continue

            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("telemetry_record_decode_failed", path=str(path))
                    continue
                if token_short and record.get("token_hash") != token_short:
                    continue
                yield record

    def iter_events(
        self,
        *,
        token_hash: Optional[str] = None,
        days: int = 1,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Return recent telemetry events filtered by token hash."""

        limit = max(1, limit)

        events: List[Dict[str, Any]] = []
        for record in self._iter_records(token_hash=token_hash, days=days):
            events.append(record)
            if len(events) >= limit:
                break

        return sorted(events, key=lambda item: item.get("received_at", ""), reverse=True)

    def summarize(
        self,
        *,
        token_hash: Optional[str] = None,
        days: int = 7,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Summarize telemetry activity for the given token hash."""

        events = []
        for idx, record in enumerate(self._iter_records(token_hash=token_hash, days=days)):
            events.append(record)
            if idx + 1 >= limit:
                break
        total = len(events)
        per_event: Dict[str, int] = {}
        sessions: Set[str] = set()
        accounts: Set[str] = set()
        last_seen = None

        for record in events:
            event_name = record.get("event", "unknown")
            per_event[event_name] = per_event.get(event_name, 0) + 1
            session = record.get("session") or record.get("meta", {}).get("session")
            if session:
                sessions.add(str(session))
            account = record.get("account_id")
            if account:
                accounts.add(str(account))
            ts = record.get("received_at") or record.get("timestamp")
            if ts and (last_seen is None or ts > last_seen):
                last_seen = ts

        return {
            "total_events": total,
            "by_event": per_event,
            "unique_sessions": len(sessions),
            "unique_accounts": len(accounts),
            "last_seen": last_seen,
            "days": days,
            "inspected_at": datetime.now(timezone.utc).isoformat(),
        }

    def summarize_by_day(
        self,
        *,
        token_hash: Optional[str] = None,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Summarize telemetry counts per day for the requested window."""

        days = max(1, min(days, 30))
        token_short = token_hash[:32] if token_hash else None
        cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days - 1)

        aggregates: Dict[str, Dict[str, Any]] = {}

        files = sorted(self.storage_dir.glob("*.jsonl"))
        for path in files:
            try:
                file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff_date:
                continue

            date_key = file_date.isoformat()
            bucket = aggregates.setdefault(
                date_key,
                {
                    "date": date_key,
                    "total_events": 0,
                    "by_event": {},
                    "sessions": set(),
                    "accounts": set(),
                },
            )

            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning("telemetry_record_decode_failed", path=str(path))
                            continue
                        if token_short and record.get("token_hash") != token_short:
                            continue
                        event_name = record.get("event", "unknown")
                        bucket["total_events"] += 1
                        bucket["by_event"][event_name] = bucket["by_event"].get(event_name, 0) + 1
                        session = record.get("session") or record.get("meta", {}).get("session")
                        if session:
                            bucket["sessions"].add(str(session))
                        account = record.get("account_id")
                        if account:
                            bucket["accounts"].add(str(account))
            except FileNotFoundError:
                continue
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("telemetry_iter_error", path=str(path), error=str(exc))

        series: List[Dict[str, Any]] = []
        for offset in range(days - 1, -1, -1):
            day = (datetime.now(timezone.utc).date() - timedelta(days=offset)).isoformat()
            bucket = aggregates.get(
                day,
                {
                    "date": day,
                    "total_events": 0,
                    "by_event": {},
                    "sessions": set(),
                    "accounts": set(),
                },
            )
            series.append(
                {
                    "date": bucket["date"],
                    "total_events": bucket["total_events"],
                    "by_event": bucket["by_event"],
                    "unique_sessions": len(bucket["sessions"]),
                    "unique_accounts": len(bucket["accounts"]),
                }
            )

        return series


def _resolve_storage_dir() -> Path:
    root = os.getenv("NOCTURNAL_TELEMETRY_STORAGE", "data/telemetry")
    base = Path(root)
    try:
        return base.expanduser().resolve()
    except Exception:  # pragma: no cover - fallback when resolve fails
        return base.expanduser()


@lru_cache(maxsize=8)
def _ingestor_factory(storage_root: str) -> TelemetryIngestor:
    retention_raw = os.getenv("NOCTURNAL_TELEMETRY_RETENTION_DAYS", "30")
    try:
        retention_days = int(retention_raw)
    except ValueError:
        retention_days = 30
    return TelemetryIngestor(Path(storage_root), retention_days=retention_days)


def get_telemetry_ingestor() -> TelemetryIngestor:
    storage_dir = _resolve_storage_dir()
    return _ingestor_factory(str(storage_dir))


def reset_telemetry_ingestor_cache() -> None:
    _ingestor_factory.cache_clear()


def get_telemetry_authenticator() -> TelemetryAuthenticator:
    return TelemetryAuthenticator.from_environment()


__all__ = [
    "TelemetryAuthError",
    "TelemetryAuthenticator",
    "TelemetryIngestor",
    "get_telemetry_authenticator",
    "get_telemetry_ingestor",
    "reset_telemetry_ingestor_cache",
]
