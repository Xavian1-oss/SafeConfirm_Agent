#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROWS = [
    ("sa_llm", "rule_v1", "llm_user"),
    ("vague_llm", "baseline_vague", "llm_user"),
    ("sa_oracle", "rule_v1", "oracle_strict"),
    ("vague_oracle", "baseline_vague", "oracle_strict"),
]

FIELDS = [
    ("tsr", "TSR"),
    ("asr", "ASR"),
    ("uar", "UAR-bind"),
    ("uar_after_confirm", "UAR-after"),
    ("clr", "CLR"),
    ("sdr", "SDR"),
    ("confirm_approval_rate", "Approve%"),
    ("confirm_exec_rate", "Exec%"),
    ("confirm_total", "Confirms"),
    ("vcr", "VCR"),
    ("stall_rate", "Stall"),
]


def _load_metrics(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare confirmation ablation runs.")
    parser.add_argument("--logroot", type=Path, default=Path("runs/bridge/confirm_ablation"))
    parser.add_argument("--suite", type=str, default="safeconfirm_workspace")
    args = parser.parse_args()

    header = ["Row", "Policy", "Confirmer", *[label for _, label in FIELDS]]
    print("\t".join(header))

    for row_id, policy, confirmer in ROWS:
        metrics_path = args.logroot / row_id / args.suite / "metrics.json"
        if not metrics_path.exists():
            print(f"{row_id}\t{policy}\t{confirmer}\tMISSING ({metrics_path})")
            continue
        metrics = _load_metrics(metrics_path)
        values: list[str] = []
        for field, _ in FIELDS:
            value = metrics.get(field, 0)
            if isinstance(value, float) and field != "confirm_total":
                values.append(f"{value * 100:.1f}%")
            else:
                values.append(str(value))
        print("\t".join([row_id, policy, confirmer, *values]))


if __name__ == "__main__":
    main()
