#!/usr/bin/env python3
"""Compare paired P0 vs SafeConfirm security rerun aggregates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare paired P0 vs SC security rerun.")
    parser.add_argument("--p0", type=Path, required=True, help="P0 aggregate JSON")
    parser.add_argument("--sc", type=Path, required=True, help="SafeConfirm aggregate JSON")
    parser.add_argument("--meta", type=Path, default=None, help="Optional batch_meta.json")
    parser.add_argument("--output", type=Path, required=True, help="Output comparison JSON")
    args = parser.parse_args()

    p0 = _load(args.p0)
    sc = _load(args.sc)
    meta = _load(args.meta) if args.meta and args.meta.exists() else {}

    comparison = {
        "batch": meta,
        "p0": {
            "n_runs": p0.get("n_runs"),
            "tsr_mean": p0.get("tsr_mean"),
            "tsr_std": p0.get("tsr_std"),
            "asr_mean": p0.get("asr_mean"),
            "asr_std": p0.get("asr_std"),
            "stall_rate_mean": p0.get("stall_rate_mean"),
            "stall_rate_std": p0.get("stall_rate_std"),
        },
        "sc": {
            "n_runs": sc.get("n_runs"),
            "tsr_mean": sc.get("tsr_mean"),
            "tsr_std": sc.get("tsr_std"),
            "asr_mean": sc.get("asr_mean"),
            "asr_std": sc.get("asr_std"),
            "stall_rate_mean": sc.get("stall_rate_mean"),
            "stall_rate_std": sc.get("stall_rate_std"),
        },
        "delta_sc_minus_p0": {
            "tsr_pp": (sc.get("tsr_mean", 0) - p0.get("tsr_mean", 0)) * 100,
            "asr_pp": (sc.get("asr_mean", 0) - p0.get("asr_mean", 0)) * 100,
            "stall_pp": (sc.get("stall_rate_mean", 0) - p0.get("stall_rate_mean", 0)) * 100,
        },
        "reviewer_ready": bool(
            (p0.get("asr_mean") or 0) > 0
            and (sc.get("asr_mean") or 0) == 0
            and (sc.get("tsr_mean") or 0) >= (p0.get("tsr_mean") or 0)
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(comparison, indent=2) + "\n")

    print("Paired security rerun comparison")
    if meta:
        print(f"  batch_id: {meta.get('batch_id')} | subset: {meta.get('subset')} | temperature: {meta.get('temperature')}")
    print(f"  P0: TSR={_pct(p0.get('tsr_mean'))} ± {_pct(p0.get('tsr_std'))} | ASR={_pct(p0.get('asr_mean'))} | Stall={_pct(p0.get('stall_rate_mean'))}")
    print(f"  SC: TSR={_pct(sc.get('tsr_mean'))} ± {_pct(sc.get('tsr_std'))} | ASR={_pct(sc.get('asr_mean'))} | Stall={_pct(sc.get('stall_rate_mean'))}")
    print(f"  Delta(SC-P0): TSR {comparison['delta_sc_minus_p0']['tsr_pp']:+.1f} pp | ASR {comparison['delta_sc_minus_p0']['asr_pp']:+.1f} pp")
    if comparison["reviewer_ready"]:
        print("  STATUS: reviewer-ready (P0 ASR>0, SC ASR=0, SC TSR≥P0)")
    else:
        print("  STATUS: NOT reviewer-ready — adjust temperature/subset or retry batch")


if __name__ == "__main__":
    main()
