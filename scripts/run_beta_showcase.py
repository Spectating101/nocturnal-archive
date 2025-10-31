#!/usr/bin/env python3
"""Helper script to regenerate beta showcase artifacts and print summary."""

import argparse
import asyncio
import json
from pathlib import Path

from scripts.autonomy_harness import (
    execute_scenarios,
    _serialise_payload,
    _serialise_response,
)


def _make_json_safe(obj):
    if isinstance(obj, dict):
        return {key: _make_json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(value) for value in obj]
    if hasattr(obj, "response") and hasattr(obj, "tools_used"):
        return _serialise_response(obj)
    return obj


def _summarise(results):
    metrics = results.pop("_metrics", None)
    summary = {
        "scenarios": list(results.keys()),
        "metrics": metrics or {},
        "guardrail_checks": {
            name: payload.get("quality_checks")
            for name, payload in results.items()
            if isinstance(payload, dict) and payload.get("quality_checks")
        },
    }
    return summary


async def _main(args):
    results = await execute_scenarios(args.only)
    serialised = {}
    for key, value in results.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            converted = _serialise_payload(value)
        else:
            converted = value
        serialised[key] = _make_json_safe(converted)
    if results.get("_metrics"):
        serialised["_metrics"] = results["_metrics"]

    Path(args.output).write_text(json.dumps(serialised, indent=2))
    summary = _summarise(dict(serialised))
    print(f"Artifacts written to {args.output}")
    metrics = summary.get("metrics", {})
    if metrics:
        print("\nMetrics")
        print(f"  Scenarios      : {metrics.get('scenario_count')}")
        print(f"  Total elapsed  : {metrics.get('total_elapsed'):.3f}s")
        print(f"  Guardrail pass : {metrics.get('guardrail_pass_rate'):.2%}")
    if summary["guardrail_checks"]:
        print("\nGuardrail status:")
        for name, checks in summary["guardrail_checks"].items():
            status = "PASS" if all(checks.values()) else "CHECK"
            print(f"  {name}: {status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run beta showcase harness and summarise results")
    parser.add_argument("--output", default="artifacts_autonomy.json", help="Where to write the JSON artifact")
    parser.add_argument("--only", nargs="*", help="Run a subset of scenarios")
    asyncio.run(_main(parser.parse_args()))
