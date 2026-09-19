#!/usr/bin/env python3
"""Spot-check paper Table 1/2 numbers against Overleaf canonical JSON."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "6a9fb8173b16b4dea4fd1079" / "paper_metrics" / "canonical"
TEX = REPO / "6a9fb8173b16b4dea4fd1079" / "safeconfirm.tex"


def pct(x: float | None) -> float | None:
    if x is None:
        return None
    return round(float(x) * 100, 1)


def load(name: str) -> dict:
    return json.loads((CANONICAL / name).read_text())


def mean_pct(data: dict, key: str) -> float | None:
    mean_key = f"{key}_mean"
    if mean_key in data:
        return pct(data.get(mean_key))
    if key in data:
        return pct(data.get(key))
    return None


def main() -> int:
    if not CANONICAL.is_dir():
        print(f"Missing {CANONICAL}", file=sys.stderr)
        return 1

    mismatches: list[str] = []

    def expect(label: str, got: float | None, paper: float, tol: float = 0.15) -> None:
        if got is None:
            print(f"FAIL {label:36} json missing paper={paper}")
            mismatches.append(label)
            return
        ok = abs(got - paper) <= tol
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {label:36} json={got:5} paper={paper:5}")
        if not ok:
            mismatches.append(label)

    for f, exp in [
        ("confirm_sa_llm_poison_v2.json", dict(tsr=55.6, asr=0, sdr=100, clr=0)),
        ("confirm_vague_llm_poison_v2.json", dict(tsr=22.2, asr=0, sdr=0)),
    ]:
        d = load(f)
        for k, v in exp.items():
            expect(f"{f} {k}", mean_pct(d, k), v)

    d = load("confirm_vague_llm_poison_v2.json")
    if d.get("clr_mean") is None or d.get("approved_confirmations_total") == 0:
        print("OK   vague clr undefined in JSON")
    else:
        print(f"FAIL vague should have undefined CLR, got {d.get('clr_mean')}")
        mismatches.append("vague clr")

    d = load("confirm_vague_compliant_llm.json")
    expect("compliant tsr", mean_pct(d, "tsr"), 22.2)
    expect("compliant asr", mean_pct(d, "asr"), 6.7)
    expect("compliant clr", mean_pct(d, "clr"), 66.7)

    for f, tsr in [
        ("provenance_rule_v1_aggregate.json", 75.0),
        ("provenance_block_aggregate.json", 22.2),
        ("provenance_vague_aggregate.json", 25.0),
    ]:
        d = load(f)
        expect(f" {f} tsr", mean_pct(d, "tsr"), tsr)
        expect(f" {f} asr", mean_pct(d, "asr"), 0.0)

    if TEX.is_file() and re.search(r"Vague disclosure[^\n]*&[^\n]*---", TEX.read_text()):
        print("OK   tex vague CLR row uses ---")
    else:
        print("FAIL tex vague CLR should be ---")
        mismatches.append("tex vague clr")

    for f, asr in [("external_p0_aggregate.json", 39.4), ("external_sc_aggregate.json", 0.0)]:
        d = load(f)
        expect(f" {f} asr", mean_pct(d, "asr"), asr)

    if mismatches:
        print(f"\n{len(mismatches)} mismatch(es).", file=sys.stderr)
        return 1
    print("\nAll paper spot-checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
