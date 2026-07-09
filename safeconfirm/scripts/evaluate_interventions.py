#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safeconfirm.evaluation.metrics import compute_metrics, load_targeted_runs


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SafeConfirm intervention metrics from targeted runs.")
    parser.add_argument("--logdir", type=Path, default=Path("runs/safeconfirm_l1"))
    parser.add_argument("--policy", default=None, help="Optional policy id filter, e.g. P4")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path for metrics table.")
    args = parser.parse_args()

    runs = load_targeted_runs(args.logdir)
    if args.policy:
        runs = [run for run in runs if run.policy_id == args.policy]

    if not runs:
        raise SystemExit(f"No targeted runs with safeconfirm logs found under {args.logdir}")

    grouped: dict[str, list] = {}
    for run in runs:
        grouped.setdefault(run.policy_id, []).append(run)

    rows: dict[str, dict[str, float | int]] = {}
    for policy_id, policy_runs in sorted(grouped.items()):
        metrics = compute_metrics(policy_runs)
        rows[policy_id] = metrics.model_dump()
        print(
            f"{policy_id}\tUAR={metrics.uar:.3f}\tCLR={metrics.clr:.3f}\tSDR={metrics.sdr:.3f}\t"
            f"TPR={metrics.tpr:.3f}\tFBR={metrics.fbr:.3f}\tRSR={metrics.rsr:.3f}\tComposite={metrics.composite:.3f}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as handle:
            json.dump(rows, handle, indent=2)
        print(f"Wrote metrics table to {args.output}")


if __name__ == "__main__":
    main()
