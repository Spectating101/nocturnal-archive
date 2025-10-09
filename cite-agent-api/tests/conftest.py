"""Pytest fixtures for lightweight, in-process API tests."""
from __future__ import annotations

import os
from typing import Iterator
from urllib.parse import urlparse, urlunparse

import anyio
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("PYTEST_ENV", "1")
os.environ.setdefault("BASE", "http://testserver")
os.environ.setdefault("API_KEY", "demo-key-123")

from src.main import app


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Expose the FastAPI application object for tests."""
    return app


@pytest.fixture(scope="session")
def client(test_app: FastAPI) -> Iterator[TestClient]:
    """Synchronous TestClient bound to the FastAPI app."""
    with TestClient(test_app) as test_client:
        yield test_client


class _SyncHttpxClient:
    """Sync facade over httpx.AsyncClient using ASGITransport."""

    def __init__(self, app: FastAPI, base_url: str) -> None:
        self._client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=base_url,
            follow_redirects=True,
        )

    def request(self, method: str, url: str, **kwargs):
        normalized = _normalize_url(url)
        async def _run_request():
            return await self._client.request(method, normalized, **kwargs)

        return anyio.run(_run_request)

    def close(self) -> None:
        anyio.run(self._client.aclose)

    def __getattr__(self, item: str):
        if item.lower() in {"get", "post", "put", "patch", "delete", "head", "options"}:
            def _call(url: str, **kwargs):
                return self.request(item.upper(), url, **kwargs)

            return _call
        raise AttributeError(item)


@pytest.fixture(scope="session")
def httpx_client(test_app: FastAPI) -> Iterator[_SyncHttpxClient]:
    """HTTPX client wired to the FastAPI app via ASGI transport."""
    client = _SyncHttpxClient(test_app, os.environ["BASE"])
    try:
        yield client
    finally:
        client.close()


def _normalize_url(url: str) -> str:
    """Strip scheme/host so httpx client uses its base URL."""
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return urlunparse(("", "", parsed.path or "/", "", parsed.query, parsed.fragment))
    return url


@pytest.fixture(autouse=True)
def _patch_httpx(monkeypatch, httpx_client: httpx.Client) -> Iterator[None]:
    """Route module-level httpx calls through the in-process client."""

    def _make_request(method: str):
        def _request(url: str, **kwargs):
            normalized = _normalize_url(url)
            return httpx_client.request(method, normalized, **kwargs)

        return _request

    for method in ("get", "post", "put", "patch", "delete", "head", "options"):
        monkeypatch.setattr(httpx, method, _make_request(method.upper()))

    def _request(method: str, url: str, **kwargs):
        normalized = _normalize_url(url)
        return httpx_client.request(method, normalized, **kwargs)

    monkeypatch.setattr(httpx, "request", _request)
    yield