#!/usr/bin/env python3
"""Aggregate per-case E2E stats from SafeConfirm bridge run JSON files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _load_runs(logdir: Path) -> list[dict]:
    runs: list[dict] = []
    for path in sorted(logdir.glob("user_task_*__injection_task_*.json")):
        runs.append(json.loads(path.read_text()))
    return runs


def _summarize_run(run: dict) -> dict:
    records = (run.get("safeconfirm") or {}).get("records") or []
    interventions = Counter(r.get("selected_intervention") for r in records)
    repair_attempts = sum(1 for r in records if r.get("repair_attempted"))
    repair_success = sum(
        1 for r in records if r.get("repair_attempted") and r.get("repair_result") == "success"
    )
    confirms = [r for r in records if r.get("selected_intervention") == "SOURCE_AWARE_CONFIRM"]
    approved = sum(1 for r in confirms if r.get("confirmation_response") == "approved")
    return {
        "case_id": run.get("case_id"),
        "user_task_id": run.get("user_task_id"),
        "benign": run.get("benign", False),
        "utility": run.get("utility"),
        "attack_succeeded": run.get("attack_succeeded"),
        "interventions": dict(interventions),
        "repair_attempts": repair_attempts,
        "repair_success": repair_success,
        "confirm_total": len(confirms),
        "confirm_approved": approved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-case E2E intervention summary")
    parser.add_argument(
        "--logdir",
        type=Path,
        required=True,
        help="Directory containing user_task_*__injection_task_*.json files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON summary (default: <logdir>/per_case_summary.json)",
    )
    args = parser.parse_args()

    runs = _load_runs(args.logdir)
    if not runs:
        raise SystemExit(f"No run JSON files under {args.logdir}")

    rows = [_summarize_run(run) for run in runs]
    summary = {
        "logdir": str(args.logdir),
        "n_cases": len(rows),
        "tsr": sum(1 for r in rows if r["utility"]) / len(rows),
        "asr": sum(1 for r in rows if not r["benign"] and r["attack_succeeded"])
        / max(1, sum(1 for r in rows if not r["benign"])),
        "cases": rows,
    }
    output = args.output or (args.logdir / "per_case_summary.json")
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {output} ({len(rows)} cases, TSR={summary['tsr']*100:.1f}%)")


if __name__ == "__main__":
    main()
