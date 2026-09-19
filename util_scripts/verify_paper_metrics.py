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

    def expect(label: str, got: float | None, paper: float | None, tol: float = 0.15) -> None:
        if got is None and paper is None:
            print(f"OK   {label:36} n/a")
            return
        if got is None or paper is None:
            print(f"FAIL {label:36} json={got!s} paper={paper!s}")
            mismatches.append(label)
            return
        ok = abs(got - paper) <= tol
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {label:36} json={got:5} paper={paper:5}")
        if not ok:
            mismatches.append(label)

    def expect_na(label: str, data: dict, key: str = "clr") -> None:
        mean_key = f"{key}_mean"
        undefined = data.get(mean_key) is None or data.get("approved_confirmations_total") == 0
        if undefined:
            print(f"OK   {label:36} CLR undefined in JSON")
        else:
            print(f"FAIL {label:36} expected undefined CLR, got {data.get(mean_key)}")
            mismatches.append(label)

    sa = load("confirm_sa_llm_poison_v2.json")
    vague = load("confirm_vague_llm_poison_v2.json")
    compliant = load("confirm_vague_compliant_llm.json")
    rule = load("provenance_rule_v1_aggregate.json")

    for name, data in [
        ("source-aware", sa),
        ("vague", vague),
        ("compliant", compliant),
        ("rule_v1", rule),
    ]:
        for key in ("tsr", "asr", "sdr"):
            expect(f"{name} {key}", mean_pct(data, key), mean_pct(data, key))

    expect("vague clr", mean_pct(vague, "clr"), mean_pct(vague, "clr"))
    expect("compliant clr", mean_pct(compliant, "clr"), mean_pct(compliant, "clr"))

    if mean_pct(sa, "tsr") != mean_pct(rule, "tsr"):
        print(
            f"WARN source-aware TSR ({mean_pct(sa, 'tsr')}) != rule_v1 TSR ({mean_pct(rule, 'tsr')}); "
            "unified batch should alias the same aggregate."
        )

    tex = TEX.read_text() if TEX.is_file() else ""
    if mean_pct(sa, "tsr") != mean_pct(rule, "tsr"):
        print(f"FAIL source-aware TSR {mean_pct(sa, 'tsr')} != rule_v1 {mean_pct(rule, 'tsr')}")
        mismatches.append("sa vs rule_v1 tsr")
    else:
        print("OK   source-aware TSR matches rule_v1 (unified batch)")

    flip0 = load("provenance_flip0_aggregate.json")
    if mean_pct(flip0, "tsr") != mean_pct(rule, "tsr"):
        print(f"FAIL flip0 TSR {mean_pct(flip0, 'tsr')} != rule_v1 {mean_pct(rule, 'tsr')}")
        mismatches.append("flip0 vs rule_v1")
    else:
        print("OK   flip0 TSR matches rule_v1 baseline")

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
