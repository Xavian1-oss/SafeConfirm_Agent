"""Aggregate native AgentDojo logdirs: utility/security + SDR/CLR + coverage."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from safeconfirm.evaluation.metrics import compute_metrics
from safeconfirm.evaluation.native_trajectory import (
    NativeRunModel,
    TrajectoryPrimaryLabel,
    discover_benchmark_logs,
    load_native_run_from_log,
)
from safeconfirm.types.models import TargetedRunResultModel


class CoverageSummaryModel(BaseModel):
    total_trajectories: int = 0
    binding_relevant: int = 0
    unsupported_tool: int = 0
    no_binding_side_effect: int = 0
    binding_trusted: int = 0
    no_tool_calls: int = 0
    goal_hijacking: int = 0
    other: int = 0
    corruption_trajectories: int = 0
    benign_trajectories: int = 0


class NativeDefenseMetricsModel(BaseModel):
    defense_label: str
    logdir: str
    coverage: CoverageSummaryModel
    utility_whole_suite: float
    security_whole_suite: float
    utility_binding_subset: float | None = None
    security_binding_subset: float | None = None
    tsr: float
    asr: float
    corruption_tsr: float
    corruption_asr: float
    benign_tsr: float
    sdr: float | None = None
    clr: float | None = None
    confirm_total: int = 0
    approved_confirmations: int = 0
    repair_attempts: int = 0
    uar: float = 0.0
    binding_subset_size: int = 0
    corruption_binding_subset_size: int = 0


class NativeComparisonModel(BaseModel):
    defenses: list[NativeDefenseMetricsModel] = Field(default_factory=list)


def _to_targeted_run(run: NativeRunModel) -> TargetedRunResultModel:
    return TargetedRunResultModel(
        case_id=run.trajectory_id,
        policy_id="native",
        suite=run.suite_name,
        category=run.coverage.primary.value,
        benign=run.benign,
        utility=run.utility,
        security=run.security,
        safeconfirm=run.safeconfirm,
    )


def _coverage_summary(runs: list[NativeRunModel]) -> CoverageSummaryModel:
    summary = CoverageSummaryModel(total_trajectories=len(runs))
    for run in runs:
        if run.benign:
            summary.benign_trajectories += 1
        else:
            summary.corruption_trajectories += 1
        if run.coverage.binding_relevant:
            summary.binding_relevant += 1
        if run.coverage.unsupported_tool:
            summary.unsupported_tool += 1
        if run.coverage.no_binding_side_effect:
            summary.no_binding_side_effect += 1
        if run.coverage.binding_trusted:
            summary.binding_trusted += 1
        if run.coverage.goal_hijacking:
            summary.goal_hijacking += 1
        primary = run.coverage.primary
        if primary == TrajectoryPrimaryLabel.NO_TOOL_CALLS:
            summary.no_tool_calls += 1
        elif primary == TrajectoryPrimaryLabel.OTHER:
            summary.other += 1
    return summary


def _rate(items: list[bool]) -> float:
    return sum(items) / len(items) if items else 0.0


def aggregate_logdir(logdir: Path, *, defense_label: str) -> NativeDefenseMetricsModel:
    runs: list[NativeRunModel] = []
    for path in discover_benchmark_logs(logdir):
        loaded = load_native_run_from_log(path)
        if loaded is not None:
            runs.append(loaded)

    coverage = _coverage_summary(runs)
    binding_runs = [run for run in runs if run.coverage.binding_relevant]
    corruption_binding = [run for run in binding_runs if not run.benign]

    targeted = [_to_targeted_run(run) for run in runs]
    intervention = compute_metrics(targeted, benchmark_cases_path=None)

    corruption_runs = [run for run in runs if not run.benign]
    benign_runs = [run for run in runs if run.benign]

    return NativeDefenseMetricsModel(
        defense_label=defense_label,
        logdir=str(logdir),
        coverage=coverage,
        utility_whole_suite=_rate([run.utility for run in runs]),
        security_whole_suite=_rate([run.security for run in runs]),
        utility_binding_subset=_rate([run.utility for run in binding_runs]) if binding_runs else None,
        security_binding_subset=_rate([run.security for run in corruption_binding]) if corruption_binding else None,
        tsr=intervention.tpr,
        asr=1.0 - _rate([run.security for run in corruption_runs]) if corruption_runs else 0.0,
        corruption_tsr=_rate([run.utility for run in corruption_runs]) if corruption_runs else 0.0,
        corruption_asr=1.0 - _rate([run.security for run in corruption_runs]) if corruption_runs else 0.0,
        benign_tsr=_rate([run.utility for run in benign_runs]) if benign_runs else 0.0,
        sdr=intervention.sdr,
        clr=intervention.clr,
        confirm_total=intervention.confirm_total,
        approved_confirmations=intervention.approved_confirmations,
        repair_attempts=intervention.repair_attempts,
        uar=intervention.uar,
        binding_subset_size=len(binding_runs),
        corruption_binding_subset_size=len(corruption_binding),
    )


def compare_native_logdirs(pairs: list[tuple[str, Path]]) -> NativeComparisonModel:
    return NativeComparisonModel(
        defenses=[aggregate_logdir(path, defense_label=label) for label, path in pairs],
    )


def save_comparison(model: NativeComparisonModel, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(model.model_dump(mode="json"), handle, indent=2)


def print_comparison_table(model: NativeComparisonModel) -> None:
    headers = [
        "Defense",
        "N",
        "Bind.",
        "Util%",
        "Sec%",
        "Bind util%",
        "Bind sec%",
        "SDR",
        "CLR",
        "#Confirm",
    ]
    rows: list[list[str]] = []
    for defense in model.defenses:
        cov = defense.coverage
        rows.append(
            [
                defense.defense_label,
                str(cov.total_trajectories),
                str(cov.binding_relevant),
                f"{defense.utility_whole_suite * 100:.1f}",
                f"{defense.security_whole_suite * 100:.1f}",
                "—" if defense.utility_binding_subset is None else f"{defense.utility_binding_subset * 100:.1f}",
                "—" if defense.security_binding_subset is None else f"{defense.security_binding_subset * 100:.1f}",
                "—" if defense.sdr is None else f"{defense.sdr * 100:.1f}",
                "—" if defense.clr is None else f"{defense.clr * 100:.1f}",
                str(defense.confirm_total),
            ]
        )

    widths = [max(len(headers[i]), *(len(row[i]) for row in rows), 6) for i in range(len(headers))]

    def fmt(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    print(fmt(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))

    print("\nCoverage (trajectory counts; binding_relevant may overlap flags on other axes):")
    cov_headers = ["Defense", "no_tool", "unsupported", "no_bind_fx", "bind_trusted", "goal_hijack", "other"]
    cov_rows: list[list[str]] = []
    for defense in model.defenses:
        c = defense.coverage
        cov_rows.append(
            [
                defense.defense_label,
                str(c.no_tool_calls),
                str(c.unsupported_tool),
                str(c.no_binding_side_effect),
                str(c.binding_trusted),
                str(c.goal_hijacking),
                str(c.other),
            ]
        )
    cov_widths = [max(len(cov_headers[i]), *(len(row[i]) for row in cov_rows), 6) for i in range(len(cov_headers))]

    def fmt_cov(cells: list[str]) -> str:
        return " | ".join(cell.ljust(cov_widths[i]) for i, cell in enumerate(cells))

    print(fmt_cov(cov_headers))
    print("-+-".join("-" * w for w in cov_widths))
    for row in cov_rows:
        print(fmt_cov(row))
