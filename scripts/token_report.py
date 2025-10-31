#!/usr/bin/env python3
"""Aggregate token usage from telemetry and history logs for beta monitoring."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Optional


def _load_lines(path: Path) -> Iterable[Dict]:
    if not path.exists():
        return []
    results = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return results


def build_token_report(root: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    base = root or Path.home() / ".nocturnal_archive"
    telemetry_log = base / "logs" / "beta-telemetry.jsonl"
    history_log = base / "history" / "history.jsonl"

    aggregates: Dict[str, float] = defaultdict(float)

    for record in _load_lines(telemetry_log):
        user = record.get("user") or "unknown"
        tokens = record.get("tokens_used")
        if tokens is None:
            continue
        try:
            aggregates[user] += float(tokens)
        except (TypeError, ValueError):
            continue

    for record in _load_lines(history_log):
        metadata = record.get("metadata") or {}
        tokens = metadata.get("tokens_used")
        if tokens is None:
            continue
        user = record.get("user") or metadata.get("user") or "unknown"
        try:
            aggregates[user] += float(tokens)
        except (TypeError, ValueError):
            continue

    total = sum(aggregates.values())
    return {
        "per_user": dict(sorted(aggregates.items(), key=lambda item: item[0])),
        "total_tokens": total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise beta token usage")
    parser.add_argument(
        "--root",
        type=Path,
        help="Override NOCTURNAL_HOME (defaults to ~/.nocturnal_archive)",
    )
    args = parser.parse_args()

    report = build_token_report(args.root)
    print("Token usage summary")
    print(f"  Total tokens : {report['total_tokens']:.0f}")
    print("  Per user (hashed id → tokens):")
    for user, tokens in report["per_user"].items():
        print(f"    {user}: {tokens:.0f}")


if __name__ == "__main__":
    main()
