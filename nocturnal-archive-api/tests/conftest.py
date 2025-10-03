"""Pytest fixtures for integration-style tests."""
from __future__ import annotations

import os
import socket
import threading
import time
from typing import Iterator

import pytest
import uvicorn

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("PYTEST_ENV", "1")

from src.main import app


def _wait_for_port(host: str, port: int, timeout: float = 5.0) -> None:
    """Wait until a TCP port starts accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            try:
                sock.connect((host, port))
            except OSError:
                time.sleep(0.1)
                continue
            else:
                return
    raise RuntimeError(f"Server on {host}:{port} did not start within {timeout} seconds")


@pytest.fixture(scope="session", autouse=True)
def start_test_server() -> Iterator[None]:
    """Start the FastAPI app in a background thread for httpx-based tests."""
    host = os.getenv("NA_TEST_HOST", "127.0.0.1")
    port = int(os.getenv("NA_TEST_PORT", "8000"))

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, name="uvicorn-test-server", daemon=True)
    thread.start()

    _wait_for_port(host, port)

    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=5)