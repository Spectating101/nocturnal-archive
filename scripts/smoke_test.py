"""Nocturnal Archive smoke test.

Boots the API locally, performs a health check, runs a sample agent query,
and reports the outcomes. Intended for quick verification during demos or CI.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

import requests

API_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{API_URL}/api/health"
SAMPLE_QUERY = "find papers about CRISPR base editing"


def start_api() -> subprocess.Popen:
    """Launch the FastAPI service in a background process."""
    repo_root = Path(__file__).resolve().parents[1]
    api_path = repo_root / "nocturnal-archive-api"
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    env = os.environ.copy()
    process = subprocess.Popen(
        command,
        cwd=str(api_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process


def wait_for_api(timeout: int = 45) -> Tuple[bool, float]:
    """Poll the health endpoint until the API responds or timeout occurs."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                return True, time.time() - start
        except requests.RequestException:
            pass
        time.sleep(1)
    return False, time.time() - start


def run_cli_query(query: str) -> subprocess.CompletedProcess:
    """Execute the enhanced agent CLI for a sample question."""
    command = [
        sys.executable,
        "-m",
        "nocturnal_archive.cli",
        query,
    ]
    return subprocess.run(command, capture_output=True, text=True, timeout=180)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Nocturnal Archive smoke test")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip the CLI portion (useful for API-only checks)",
    )
    args = parser.parse_args()

    print("🚀 Starting Nocturnal Archive smoke test...")
    api_process = start_api()
    try:
        print("⏳ Waiting for API to become ready...")
        api_ready, ready_time = wait_for_api()
        if not api_ready:
            print("❌ API did not respond to health check within timeout")
            return 1
        print(f"✅ API responded to health check in {ready_time:.1f}s")

        if args.skip_cli:
            print("➡️  CLI step skipped per flag")
            return 0

        print(f"🤖 Running sample agent query: '{SAMPLE_QUERY}'")
        cli_result = run_cli_query(SAMPLE_QUERY)
        if cli_result.returncode != 0:
            print("❌ Agent CLI returned a non-zero exit code")
            print(cli_result.stderr)
            return cli_result.returncode

        print("✅ Agent CLI completed")
        print("--- Agent Output ---")
        print(cli_result.stdout.strip())
        print("---------------------")
        return 0
    except Exception as exc:  # pragma: no cover - smoke script best effort
        print(f"❌ Smoke test encountered an error: {exc}")
        return 1
    finally:
        api_process.terminate()
        try:
            api_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            api_process.kill()


if __name__ == "__main__":
    sys.exit(main())
