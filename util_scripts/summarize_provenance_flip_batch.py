#!/usr/bin/env python3
"""Print LaTeX rows for tab:prov-flip from run_provenance_sensitivity.sh aggregates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BATCH = REPO / "runs/bridge/provenance_sensitivity/prov_flip_20260919"

RATE_TAGS = [
    (0.0, "flip0"),
    (0.05, "flip005"),
    (0.10, "flip010"),
    (0.20, "flip020"),
]


def pct(x: float) -> str:
    return f"{x * 100:.1f}"


def load_agg(batch: Path, tag: str) -> dict | None:
    path = batch / f"{tag}_aggregate.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def main() -> int:
    batch = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BATCH
    if not batch.is_dir():
        print(f"Missing batch dir: {batch}", file=sys.stderr)
        return 1

    for rate, tag in RATE_TAGS:
        agg = load_agg(batch, tag)
        label = f"{rate:.2f}".rstrip("0").rstrip(".")
        if rate == 0.0:
            label = "0"
        if agg is None:
            print(f"    {label} & --- & --- \\\\  % missing {tag}")
            continue
        tsr_m = agg["tsr_mean"]
        tsr_s = agg.get("tsr_std", 0.0)
        asr_m = agg["asr_mean"]
        asr_s = agg.get("asr_std", 0.0)
        print(
            f"    {label} & {pct(tsr_m)} $\\pm$ {pct(tsr_s)} & {pct(asr_m)} $\\pm$ {pct(asr_s)} \\\\"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
