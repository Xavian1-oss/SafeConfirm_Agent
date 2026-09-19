#!/usr/bin/env python3
"""Recompute metrics.json from per-case E2E logs in a log directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from safeconfirm_bridge.e2e_metrics import compute_e2e_metrics, load_e2e_runs, save_e2e_metrics


def refresh_logdir(logdir: Path, *, run_id: str | None, seed: int | None) -> None:
    runs = load_e2e_runs(logdir)
    if not runs:
        raise SystemExit(f"No case logs under {logdir}")
    metrics = compute_e2e_metrics(
        runs,
        run_id=run_id,
        seed=seed,
        model=getattr(runs[0], "confirmer_model", None),
        suite=runs[0].suite,
        defense="safeconfirm",
    )
    if runs[0].policy_backend:
        metrics = metrics.model_copy(update={"policy_backend": runs[0].policy_backend})
    if runs[0].confirmer:
        metrics = metrics.model_copy(update={"confirmer": runs[0].confirmer})
    if runs[0].confirmer_model:
        metrics = metrics.model_copy(update={"confirmer_model": runs[0].confirmer_model})
    out = logdir / "metrics.json"
    save_e2e_metrics(out, metrics)
    print(f"Refreshed {out} (clr={metrics.clr!r}, approved={metrics.approved_confirmations})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh metrics.json from case logs.")
    parser.add_argument("logdir", type=Path, help="Directory containing case *.json logs")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    refresh_logdir(args.logdir.resolve(), run_id=args.run_id, seed=args.seed)


if __name__ == "__main__":
    main()
