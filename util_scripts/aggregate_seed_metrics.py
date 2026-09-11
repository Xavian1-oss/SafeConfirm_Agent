#!/usr/bin/env python3
"""Aggregate multi-seed E2E metrics (mean ± std)."""

from __future__ import annotations

import argparse
import json
import statistics
from glob import glob
from pathlib import Path

METRIC_KEYS = (
    "tsr",
    "asr",
    "uar",
    "sdr",
    "clr",
    "corruption_tsr",
    "benign_tsr",
    "stall_rate",
    "composite",
)


def load_metrics(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open() as handle:
            rows.append(json.load(handle))
    return rows


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        raise SystemExit("No metrics files matched.")

    summary: dict = {
        "n_runs": len(rows),
        "run_ids": [row.get("run_id") for row in rows],
        "policy_backend": rows[0].get("policy_backend"),
        "model": rows[0].get("model"),
        "suite": rows[0].get("suite"),
    }
    for key in METRIC_KEYS:
        values = [float(row[key]) for row in rows if key in row and row[key] is not None]
        if not values:
            continue
        summary[f"{key}_mean"] = statistics.mean(values)
        summary[f"{key}_std"] = statistics.pstdev(values) if len(values) > 1 else 0.0
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate multi-seed bridge metrics.")
    parser.add_argument("--pattern", required=True, help="Glob for metrics.json files")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args()

    paths = sorted(Path(p) for p in glob(args.pattern))
    summary = aggregate(load_metrics(paths))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Aggregated {summary['n_runs']} runs -> {args.output}")
    if "tsr_mean" in summary:
        print(
            f"TSR: {summary['tsr_mean'] * 100:.2f}% ± {summary['tsr_std'] * 100:.2f}% | "
            f"ASR: {summary['asr_mean'] * 100:.2f}% ± {summary['asr_std'] * 100:.2f}%"
        )


if __name__ == "__main__":
    main()
