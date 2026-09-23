#!/usr/bin/env python3
"""Spot-check paper tables against Overleaf canonical JSON."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "6a9fb8173b16b4dea4fd1079" / "paper_metrics" / "canonical"
TEX = REPO / "6a9fb8173b16b4dea4fd1079" / "safeconfirm.tex"


class Checker:
    def __init__(self) -> None:
        self.mismatches: list[str] = []
        self.ok_count = 0

    def expect(self, label: str, got: float | None, paper: float, tol: float = 0.15) -> None:
        if got is None:
            print(f"FAIL {label:42} json missing paper={paper}")
            self.mismatches.append(label)
            return
        ok = abs(got - paper) <= tol
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {label:42} json={got:5} paper={paper:5}")
        if ok:
            self.ok_count += 1
        else:
            self.mismatches.append(label)

    def expect_std_pct(self, label: str, data: dict, key: str, paper: float, tol: float = 0.15) -> None:
        std_key = f"{key}_std"
        if std_key not in data or data[std_key] is None:
            print(f"FAIL {label:42} json missing std paper={paper}")
            self.mismatches.append(label)
            return
        got = round(float(data[std_key]) * 100, 1)
        self.expect(label, got, paper, tol=tol)

    def ok(self, label: str) -> None:
        print(f"OK   {label}")
        self.ok_count += 1

    def fail(self, label: str, detail: str = "") -> None:
        print(f"FAIL {label}" + (f" ({detail})" if detail else ""))
        self.mismatches.append(label)


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


def component_row(data: dict, row_id: str) -> dict | None:
    for row in data.get("rows", []):
        if row.get("id") == row_id:
            return row
    return None


def main() -> int:
    if not CANONICAL.is_dir():
        print(f"Missing {CANONICAL}", file=sys.stderr)
        return 1

    c = Checker()

    for f, exp in [
        ("confirm_sa_llm_poison_v2.json", dict(tsr=55.6, asr=0, sdr=100, clr=0)),
        ("confirm_vague_llm_poison_v2.json", dict(tsr=22.2, asr=0, sdr=0)),
    ]:
        d = load(f)
        for k, v in exp.items():
            c.expect(f"{f} {k}", mean_pct(d, k), v)

    d = load("confirm_vague_llm_poison_v2.json")
    if d.get("clr_mean") is None or d.get("approved_confirmations_total") == 0:
        c.ok("vague clr undefined in JSON")
    else:
        c.fail("vague clr undefined", f"got clr_mean={d.get('clr_mean')}")

    d = load("confirm_vague_compliant_llm.json")
    c.expect("compliant tsr", mean_pct(d, "tsr"), 22.2)
    c.expect("compliant asr", mean_pct(d, "asr"), 6.7)
    c.expect("compliant clr", mean_pct(d, "clr"), 66.7)
    c.expect("compliant confirm_approval_rate", mean_pct(d, "confirm_approval_rate"), 8.9)

    for f, tsr in [
        ("provenance_rule_v1_aggregate.json", 75.0),
        ("provenance_block_aggregate.json", 22.2),
        ("provenance_vague_aggregate.json", 25.0),
    ]:
        d = load(f)
        c.expect(f"{f} tsr", mean_pct(d, "tsr"), tsr)
        c.expect(f"{f} asr", mean_pct(d, "asr"), 0.0)

    d = load("provenance_rule_v1_aggregate.json")
    c.expect("rule_v1 sdr", mean_pct(d, "sdr"), 100.0)
    c.expect("rule_v1 clr", mean_pct(d, "clr"), 0.0)

    d = load("provenance_vague_aggregate.json")
    if d.get("clr_mean") is None:
        c.ok("provenance vague clr undefined (table ---)")
    else:
        c.fail("provenance vague clr", f"clr_mean={d.get('clr_mean')}")

    comp = load("component_12case_poison_v2.json")
    allow = component_row(comp, "allow_ds")
    if allow is None:
        c.fail("component allow_ds row missing")
    else:
        c.expect("allow_ds tsr", pct(allow.get("tsr")), 19.4)
        c.expect("allow_ds asr", pct(allow.get("asr")), 46.7)

    for f, exp in [
        ("extended28_ws_sc.json", dict(tsr=39.4, asr=0.0)),
        ("extended28_ws_p0.json", dict(tsr=27.3, asr=38.3)),
        ("extended28_banking_sc.json", dict(tsr=0.0, asr=0.0)),
    ]:
        d = load(f)
        for k, v in exp.items():
            c.expect(f"{f} {k}", mean_pct(d, k), v)

    d = load("banking_paired_p0_aggregate.json")
    c.expect("banking_paired_p0 tsr", mean_pct(d, "tsr"), 5.6)
    c.expect("banking_paired_p0 asr", mean_pct(d, "asr"), 40.0)

    d = load("extended28_banking_p0.json")
    c.expect("extended28_banking_p0 asr", mean_pct(d, "asr"), 40.0)

    c.expect("repair_on tsr", mean_pct(load("repair_full_on_poison_v2.json"), "tsr"), 50.0)
    c.expect("repair_off tsr", mean_pct(load("repair_full_off_poison_v2.json"), "tsr"), 25.0)

    ds = load("defense_sweep_12case_poison_v2.json")
    for name, tsr, asr in [("Spotlighting", 25.0, 0.0), ("Repeat prompt", 25.0, 50.0)]:
        row = ds.get(name)
        if not isinstance(row, dict):
            c.fail(f"defense sweep {name} missing")
            continue
        c.expect(f"defense {name} tsr", pct(row.get("tsr")), tsr)
        c.expect(f"defense {name} asr", pct(row.get("asr")), asr)

    for f, asr in [("external_p0_aggregate.json", 39.4), ("external_sc_aggregate.json", 0.0)]:
        c.expect(f"{f} asr", mean_pct(load(f), "asr"), asr)
    c.expect("external_p0 tsr", mean_pct(load("external_p0_aggregate.json"), "tsr"), 0.0)
    c.expect("external_sc tsr", mean_pct(load("external_sc_aggregate.json"), "tsr"), 2.8)
    c.expect_std_pct("external_p0 asr std", load("external_p0_aggregate.json"), "asr", 4.3)
    c.expect_std_pct("external_sc tsr std", load("external_sc_aggregate.json"), "tsr", 3.9)

    flip_rows = [
        ("provenance_flip0_aggregate.json", 61.1, 0.0, 10.4, 0.0),
        ("provenance_flip005_aggregate.json", 47.2, 13.3, 3.9, 4.7),
        ("provenance_flip010_aggregate.json", 36.1, 13.3, 3.9, 4.7),
        ("provenance_flip020_aggregate.json", 25.0, 40.0, 6.8, 8.2),
    ]
    for fname, tsr, asr, tsr_std, asr_std in flip_rows:
        d = load(fname)
        c.expect(f"{fname} tsr", mean_pct(d, "tsr"), tsr)
        c.expect(f"{fname} asr", mean_pct(d, "asr"), asr)
        c.expect_std_pct(f"{fname} tsr std", d, "tsr", tsr_std)
        c.expect_std_pct(f"{fname} asr std", d, "asr", asr_std)

    d = load("holdout_banking_p0.json")
    c.expect("holdout_banking_p0 asr", mean_pct(d, "asr"), 50.0)

    if TEX.is_file():
        tex = TEX.read_text()
        if re.search(r"Vague disclosure[^\n]*&[^\n]*---", tex):
            c.ok("tex vague CLR row uses ---")
        else:
            c.fail("tex vague CLR should be ---")
    else:
        c.fail("safeconfirm.tex missing")

    if c.mismatches:
        print(f"\n{c.ok_count} passed, {len(c.mismatches)} mismatch(es).", file=sys.stderr)
        return 1
    print(f"\nAll {c.ok_count} paper spot-checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
