#!/usr/bin/env python3
"""Patch Table 1 / Appendix table numbers in safeconfirm.tex from canonical JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANON = REPO / "6a9fb8173b16b4dea4fd1079" / "paper_metrics" / "canonical"
TEX = REPO / "6a9fb8173b16b4dea4fd1079" / "safeconfirm.tex"


def pct_mean(data: dict, key: str) -> float | None:
    mean_key = f"{key}_mean"
    if mean_key not in data or data[mean_key] is None:
        return None
    return round(float(data[mean_key]) * 100, 1)


def fmt_metric(data: dict, key: str) -> str:
    mean_key = f"{key}_mean"
    if data.get(mean_key) is None:
        if key == "clr" and data.get("approved_confirmations_total") == 0:
            return "---"
        if key == "clr":
            return "---"
        return "---"
    val = pct_mean(data, key)
    if val is None:
        return "---"
    return f"{val:.1f}"


def load(name: str) -> dict:
    return json.loads((CANON / name).read_text())


def patch_row(tex: str, setting_fragment: str, cells: list[str]) -> str:
    pattern = (
        rf"({re.escape(setting_fragment)}[^\n]*&\s*)"
        rf"[\d.\-]+(\s*&\s*)"
        rf"[\d.\-]+(\s*&\s*)"
        rf"[\d.\-|]+(\s*&\s*)"
        rf"[\d.\-|]+(\s*\\\\)"
    )
    repl = rf"\g<1>{cells[0]}\g<2>{cells[1]}\g<3>{cells[2]}\g<4>{cells[3]}\g<5>"
    new_tex, n = re.subn(pattern, repl, tex, count=1)
    if n != 1:
        raise SystemExit(f"Failed to patch row containing: {setting_fragment!r}")
    return new_tex


def patch_repair_row(tex: str, label: str, tsr: float, asr: float) -> str:
    pattern = rf"({re.escape(label)}[^\n]*&\s*)[\d.]+(\s*&\s*)[\d.]+(\s*\\\\)"
    repl = rf"\g<1>{tsr:.1f}\g<2>{asr:.1f}\g<3>"
    new_tex, n = re.subn(pattern, repl, tex, count=1)
    if n != 1:
        raise SystemExit(f"Failed to patch repair row: {label!r}")
    return new_tex


def patch_prov_flip(tex: str, rate_label: str, tsr: str, asr: str) -> str:
    pattern = rf"({re.escape(rate_label)}[^\n]*&\s*)[\d. $\pm\d.]+(\s*&\s*)[\d. $\pm\d.]+(\s*\\\\)"
    repl = rf"\g<1>{tsr}\g<2>{asr}\g<3>"
    new_tex, n = re.subn(pattern, repl, tex, count=1)
    if n != 1:
        raise SystemExit(f"Failed to patch prov-flip row: {rate_label!r}")
    return new_tex


def fmt_mean_std(data: dict, key: str) -> str:
    mean = pct_mean(data, key)
    std_key = f"{key}_std"
    if mean is None:
        return "---"
    std = round(float(data[std_key]) * 100, 1) if std_key in data and data[std_key] is not None else 0.0
    return f"{mean:.1f} $\\pm$ {std:.1f}"


def main() -> None:
    if not TEX.is_file():
        raise SystemExit(f"Missing {TEX}")
    tex = TEX.read_text()

    sa = load("confirm_sa_llm_poison_v2.json")
    vague = load("confirm_vague_llm_poison_v2.json")
    compliant = load("confirm_vague_compliant_llm.json")
    rule = load("provenance_rule_v1_aggregate.json")
    block = load("provenance_block_aggregate.json")
    pvague = load("provenance_vague_aggregate.json")
    repair_on = load("repair_full_on_poison_v2.json")
    repair_off = load("repair_full_off_poison_v2.json")

    tex = patch_row(
        tex,
        "Source-aware disclosure",
        [fmt_metric(sa, "tsr"), fmt_metric(sa, "asr"), fmt_metric(sa, "sdr"), fmt_metric(sa, "clr")],
    )
    tex = patch_row(
        tex,
        "Vague disclosure",
        [fmt_metric(vague, "tsr"), fmt_metric(vague, "asr"), fmt_metric(vague, "sdr"), fmt_metric(vague, "clr")],
    )
    tex = patch_row(
        tex,
        "Vague + compliant confirmer",
        [
            fmt_metric(compliant, "tsr"),
            fmt_metric(compliant, "asr"),
            fmt_metric(compliant, "sdr"),
            fmt_metric(compliant, "clr"),
        ],
    )
    tex = patch_row(
        tex,
        "SafeConfirm (\\texttt{rule\\_v1})",
        [fmt_metric(rule, "tsr"), fmt_metric(rule, "asr"), fmt_metric(rule, "sdr"), fmt_metric(rule, "clr")],
    )
    tex = patch_row(
        tex,
        "Contract-style provenance-block",
        [fmt_metric(block, "tsr"), fmt_metric(block, "asr"), "---", "---"],
    )
    tex = patch_row(
        tex,
        "Provenance-vague (\\texttt{baseline\\_vague})",
        [fmt_metric(pvague, "tsr"), fmt_metric(pvague, "asr"), fmt_metric(pvague, "sdr"), "---"],
    )

    def repair_tsr_asr(data: dict) -> tuple[float, float]:
        if "tsr_mean" in data:
            return pct_mean(data, "tsr") or 0.0, pct_mean(data, "asr") or 0.0
        return round(float(data["tsr"]) * 100, 1), round(float(data["asr"]) * 100, 1)

    on_tsr, on_asr = repair_tsr_asr(repair_on)
    off_tsr, off_asr = repair_tsr_asr(repair_off)
    tex = patch_repair_row(tex, "Repair on (12 cases)", on_tsr or 0.0, on_asr)
    tex = patch_repair_row(tex, "Repair off (12 cases)", off_tsr or 0.0, off_asr)

    for rate, fname in [
        ("0 (baseline labels)", "provenance_flip0_aggregate.json"),
        ("0.05", "provenance_flip005_aggregate.json"),
        ("0.10", "provenance_flip010_aggregate.json"),
        ("0.20", "provenance_flip020_aggregate.json"),
    ]:
        flip = load(fname)
        tex = patch_prov_flip(tex, rate, fmt_mean_std(flip, "tsr"), fmt_mean_std(flip, "asr"))

    TEX.write_text(tex)
    print(f"Updated {TEX} from {CANON}")


if __name__ == "__main__":
    main()
