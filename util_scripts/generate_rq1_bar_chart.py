#!/usr/bin/env python3
"""Generate RQ1 grouped bar chart (ASR / SDR / CLR) from Overleaf canonical JSON."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "6a9fb8173b16b4dea4fd1079" / "paper_metrics" / "canonical"
OUT = REPO / "6a9fb8173b16b4dea4fd1079" / "figures" / "fig_rq1_confirmation_metrics.png"

POLICIES: list[tuple[str, str]] = [
    ("Source-aware", "confirm_sa_llm_poison_v2.json"),
    ("Vague", "confirm_vague_llm_poison_v2.json"),
    ("Vague +\ncompliant", "confirm_vague_compliant_llm.json"),
]
METRICS = ("asr", "sdr", "clr")
METRIC_LABELS = ("ASR", "SDR", "CLR")
COLORS = ("#4C72B0", "#55A868", "#C44E52")
HATCHES = ("", "//", "\\\\")


def pct(mean: float) -> float:
    return round(float(mean) * 100, 1)


def pct_std(std: float) -> float:
    return round(float(std) * 100, 1)


def load_policy(path: Path) -> dict[str, float | None]:
    data = json.loads(path.read_text())

    def metric(key: str) -> float | None:
        mean_key = f"{key}_mean"
        if mean_key not in data or data[mean_key] is None:
            if key == "clr" and data.get("approved_confirmations_total") == 0:
                return None
            return None
        return pct(data[mean_key])

    def err(key: str) -> float:
        std_key = f"{key}_std"
        if std_key not in data or data[std_key] is None:
            return 0.0
        return pct_std(data[std_key])

    return {
        "asr": metric("asr"),
        "sdr": metric("sdr"),
        "clr": metric("clr"),
        "asr_err": err("asr"),
        "sdr_err": err("sdr"),
        "clr_err": err("clr"),
    }


def main() -> None:
    rows = [load_policy(CANONICAL / fname) for _, fname in POLICIES]
    n_groups = len(rows)
    n_metrics = len(METRICS)
    x = np.arange(n_groups)
    width = 0.22

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
        }
    )

    fig, ax = plt.subplots(figsize=(3.4, 2.15), dpi=300, layout="constrained")
    for i, (metric, label, color, hatch) in enumerate(
        zip(METRICS, METRIC_LABELS, COLORS, HATCHES, strict=True)
    ):
        offset = (i - (n_metrics - 1) / 2) * width
        for g, row in enumerate(rows):
            val = row[metric]
            if val is None:
                continue
            err = row[f"{metric}_err"]
            bar = ax.bar(
                x[g] + offset,
                val,
                width,
                label=label if g == 0 else "_nolegend_",
                color=color,
                edgecolor="0.2",
                linewidth=0.4,
                hatch=hatch,
                yerr=err,
                capsize=2,
                error_kw={"elinewidth": 0.6, "capthick": 0.6},
            )
            if val >= 8:
                ax.text(
                    bar[0].get_x() + bar[0].get_width() / 2,
                    val - 4,
                    f"{val:.0f}",
                    ha="center",
                    va="top",
                    fontsize=6,
                    color="white" if val > 35 else "0.15",
                )

    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels([name for name, _ in POLICIES])
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles, strict=False))
    ax.legend(by_label.values(), by_label.keys(), loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.18))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
