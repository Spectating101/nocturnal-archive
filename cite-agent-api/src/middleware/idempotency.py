"""
Idempotency-Key middleware with Redis (and in-memory fallback) storage.
Caches responses for POST/PUT/PATCH requests when an Idempotency-Key header is provided.
"""

import time
import hashlib
from typing import Optional, Tuple
from fastapi import Request
from fastapi.responses import Response, JSONResponse

from src.middleware.redis_fallback import get_redis_client


class IdempotencyStore:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._redis = None

    async def init(self):
        if self._redis is None:
            self._redis = await get_redis_client()
        return self

    async def get(self, key: str) -> Optional[Tuple[int, bytes, str]]:
        raw = await self._redis.get(key)
        if not raw:
            return None
        try:
            # Stored as: status|content_type|body_bytes
            parts = raw.split(b"\n", 2)
            status = int(parts[0])
            content_type = parts[1].decode()
            body = parts[2]
            return status, body, content_type
        except Exception:
            return None

    async def set(self, key: str, status: int, content_type: str, body: bytes) -> None:
        payload = f"{status}".encode() + b"\n" + content_type.encode() + b"\n" + body
        await self._redis.setex(key, self.ttl, payload)


def _hash_request(method: str, path: str, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.encode())
    h.update(b"|")
    h.update(path.encode())
    h.update(b"|")
    h.update(body or b"")
    return h.hexdigest()


async def idempotency_middleware(request: Request, call_next):
    # Only apply to write-ish methods
    if request.method not in ("POST", "PUT", "PATCH"):
        return await call_next(request)

    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        return await call_next(request)

    # Read body for hashing (must buffer and replace for downstream)
    body_bytes = await request.body()
    request._body = body_bytes  # restore for downstream

    cache_key = f"idem:{idem_key}:{_hash_request(request.method, request.url.path, body_bytes)}"

    store = await IdempotencyStore().init()
    cached = await store.get(cache_key)
    if cached:
        status, body, content_type = cached
        resp = Response(content=body, status_code=status, media_type=content_type)
        resp.headers["Idempotency-Cache"] = "HIT"
        return resp

    # Not cached: process and store
    response = await call_next(request)

    try:
        # Read response body
        if hasattr(response, "body_iterator"):
            # Streamed responses: materialize
            body_chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(body_chunks)
            response = Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
        else:
            body = response.body if isinstance(response, Response) else b""

        await store.set(cache_key, response.status_code, response.media_type or "application/json", body)
        response.headers["Idempotency-Cache"] = "MISS"
    except Exception:
        # Best-effort: do not fail request if caching fails
        pass

    return response


