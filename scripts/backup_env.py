#!/usr/bin/env python3
"""Safely back up local environment secrets for Nocturnal Archive.

This script copies the current project-level `.env.local` into the
user-specific configuration directory (`~/.nocturnal_archive/`).
It creates both a timestamped backup and an updated `config.env`
file that the agent already knows how to read via `NocturnalConfig`.

Run this before removing or overwriting the tracked `.env.local`
so your API keys stay preserved outside of git history.
"""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ENV = PROJECT_ROOT / ".env.local"
TARGET_DIR = Path.home() / ".nocturnal_archive"
TARGET_CURRENT = TARGET_DIR / "config.env"


def main() -> int:
    if not SOURCE_ENV.exists():
        print("❌ No .env.local found at project root. Aborting.")
        return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_path = TARGET_DIR / f"config.backup.{timestamp}.env"

    shutil.copy2(SOURCE_ENV, backup_path)
    shutil.copy2(SOURCE_ENV, TARGET_CURRENT)

    print("✅ Environment copied successfully")
    print(f"   Timestamped backup : {backup_path}")
    print(f"   Active config file : {TARGET_CURRENT}")
    print(
        "ℹ️  Your agent will keep working because it already loads "
        "~/.nocturnal_archive/config.env via NocturnalConfig."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
