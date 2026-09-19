#!/usr/bin/env python3
"""Spot-check paper Table 1/2 numbers against Overleaf canonical JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "6a9fb8173b16b4dea4fd1079" / "paper_metrics" / "canonical"


def pct(x: float) -> float:
    return round(float(x) * 100, 1)


def load(name: str) -> dict:
    return json.loads((CANONICAL / name).read_text())


def main() -> int:
    if not CANONICAL.is_dir():
        print(f"Missing {CANONICAL}", file=sys.stderr)
        return 1

    checks: list[tuple[str, float, float]] = []

    def expect(label: str, got: float, paper: float, tol: float = 0.15) -> None:
        ok = abs(got - paper) <= tol
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {label:36} json={got:5} paper={paper:5}")
        if not ok:
            checks.append((label, got, paper))

    for f, exp in [
        ("confirm_sa_llm_poison_v2.json", dict(tsr=55.6, asr=0, sdr=100, clr=0)),
        ("confirm_vague_llm_poison_v2.json", dict(tsr=22.2, asr=0, sdr=0, clr=0)),
    ]:
        d = load(f)
        for k, v in exp.items():
            expect(f"{f} {k}", pct(d[f"{k}_mean"]), v)

    d = load("confirm_vague_compliant_llm.json")
    expect("compliant tsr", pct(d["tsr_mean"]), 22.2)
    expect("compliant asr", pct(d["asr_mean"]), 6.7)
    expect("compliant clr", pct(d["clr_mean"]), 66.7)
    expect("compliant approval rate", pct(d["confirm_approval_rate_mean"]), 8.9, tol=0.2)

    for f, tsr in [
        ("provenance_rule_v1_aggregate.json", 75.0),
        ("provenance_block_aggregate.json", 22.2),
        ("provenance_vague_aggregate.json", 25.0),
    ]:
        d = load(f)
        expect(f" {f} tsr", pct(d["tsr_mean"]), tsr)
        expect(f" {f} asr", pct(d["asr_mean"]), 0.0)

    comp = load("component_12case_poison_v2.json")
    for row in comp["rows"]:
        if row["id"] == "allow_ds":
            expect("allow tsr", pct(row["tsr"]), 19.4)
            expect("allow asr", pct(row["asr"]), 46.7)

    for f, tsr, asr in [
        ("extended28_ws_sc.json", 39.4, 0.0),
        ("extended28_ws_p0.json", 27.3, 38.3),
        ("extended28_banking_sc.json", 0.0, 0.0),
        ("extended28_banking_p0.json", 0.0, 40.0),
    ]:
        d = load(f)
        expect(f"{f} tsr", pct(d["tsr_mean"]), tsr)
        expect(f"{f} asr", pct(d["asr_mean"]), asr)

    d = load("banking_paired_p0_aggregate.json")
    expect("paired banking p0 tsr", pct(d["tsr_mean"]), 5.6)

    for f, asr in [("external_p0_aggregate.json", 39.4), ("external_sc_aggregate.json", 0.0)]:
        d = load(f)
        expect(f"{f} asr", pct(d["asr_mean"]), asr)
    d = load("external_sc_aggregate.json")
    expect("external sc tsr", pct(d["tsr_mean"]), 2.8)
    d = load("external_p0_aggregate.json")
    expect("external p0 asr std (pp)", round(float(d["asr_std"]) * 100, 1), 4.3)

    for fname, exp in [("repair_full_on_poison_v2.json", 50.0), ("repair_full_off_poison_v2.json", 25.0)]:
        d = load(fname)
        expect(fname, pct(d["tsr"]), exp)

    sw = load("defense_sweep_12case_poison_v2.json")
    expect("spotlight stall", pct(sw["Spotlighting"]["stall_rate"]), 90.0)
    expect("spotlight tsr", pct(sw["Spotlighting"]["tsr"]), 25.0)
    expect("repeat asr", pct(sw["Repeat prompt"]["asr"]), 50.0)

    ng = load("native_gen_10task_tool_knowledge.json")
    expect("native security", pct(ng["p0"]["security_rate"]), 9.1)
    expect("native p0 utility", pct(ng["p0"]["utility_rate"]), 98.7)
    expect("native sc utility", pct(ng["safeconfirm_active"]["utility_rate"]), 87.0)

    ho = load("holdout_banking_p0.json")
    expect("holdout banking p0 asr", pct(ho["asr_mean"]), 50.0)

    if checks:
        print(f"\n{len(checks)} mismatch(es).", file=sys.stderr)
        return 1
    print("\nAll paper spot-checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
