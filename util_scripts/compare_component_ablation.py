#!/usr/bin/env python3
"""Compare component ablation runs for paper Table tab:component (DeepSeek)."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

METRIC_KEYS = ("tsr", "asr", "uar", "stall_rate")
SEED_SUFFIXES = ("s0", "s1", "s2")


def load_metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open() as handle:
        return json.load(handle)


def aggregate_metrics(paths: list[Path]) -> dict | None:
    rows = [load_metrics(path) for path in paths]
    rows = [row for row in rows if row is not None]
    if not rows:
        return None
    summary: dict = {"n_runs": len(rows), "paths": [str(p) for p in paths]}
    for key in METRIC_KEYS:
        values = [float(row[key]) for row in rows if key in row and row[key] is not None]
        if not values:
            continue
        summary[key] = statistics.mean(values)
        summary[f"{key}_std"] = statistics.pstdev(values) if len(values) > 1 else 0.0
    return summary


def resolve_policy_metrics(logroot: Path, suite: str, policy_key: str) -> dict | None:
    dir_prefix = {
        "baseline_allow": "allow_ds",
        "baseline_block": "block_ds",
        "rule_v1": "sc_ds",
    }.get(policy_key)
    if dir_prefix is None:
        return None

    seed_paths = [
        logroot / f"{dir_prefix}_{seed}" / suite / "metrics.json"
        for seed in SEED_SUFFIXES
    ]
    agg = aggregate_metrics(seed_paths)
    if agg is not None:
        return agg

    legacy = logroot / dir_prefix.replace("_ds", "") / suite / "metrics.json"
    if legacy.exists():
        return load_metrics(legacy)
    single = logroot / f"{dir_prefix}_s0" / suite / "metrics.json"
    return load_metrics(single)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize component ablation for Table tab:component.")
    parser.add_argument("--logroot", type=Path, default=Path("runs/bridge/component_ablation"))
    parser.add_argument("--suite", type=str, default="safeconfirm_workspace")
    parser.add_argument("--output", type=Path, default=Path("runs/bridge/component_ablation/summary.json"))
    args = parser.parse_args()

    policies = (
        ("allow_ds", "baseline_allow"),
        ("block_ds", "baseline_block"),
        ("sc_ds", "rule_v1"),
    )
    rows: list[dict] = []
    for row_id, policy in policies:
        metrics = resolve_policy_metrics(args.logroot, args.suite, policy)
        if metrics is None:
            rows.append({"id": row_id, "policy": policy, "status": "missing"})
            continue
        rows.append(
            {
                "id": row_id,
                "policy": policy,
                "n_runs": metrics.get("n_runs", 1),
                "tsr": metrics.get("tsr"),
                "tsr_std": metrics.get("tsr_std"),
                "asr": metrics.get("asr"),
                "asr_std": metrics.get("asr_std"),
                "stall_rate": metrics.get("stall_rate"),
                "paths": metrics.get("paths"),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        json.dump({"rows": rows}, handle, indent=2)

    print(f"Component ablation summary -> {args.output}")
    print(f"{'id':<14} {'policy':<16} {'n':>3} {'TSR':>10} {'ASR':>10} {'Stall':>10}")
    for row in rows:
        if row.get("status") == "missing":
            print(f"{row['id']:<14} {row['policy']:<16} {'—':>3} {'—':>10} {'—':>10} {'—':>10}  (missing)")
            continue
        tsr = row["tsr"] * 100
        asr = row["asr"] * 100
        stall = row["stall_rate"] * 100
        tsr_std = (row.get("tsr_std") or 0.0) * 100
        asr_std = (row.get("asr_std") or 0.0) * 100
        n = row.get("n_runs", 1)
        print(
            f"{row['id']:<14} {row['policy']:<16} {n:>3} "
            f"{tsr:6.1f}±{tsr_std:4.1f}% {asr:6.1f}±{asr_std:4.1f}% {stall:6.1f}%"
        )


if __name__ == "__main__":
    main()
