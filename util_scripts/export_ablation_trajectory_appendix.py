#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGET_TOOLS = ("send_email", "share_file", "delete_file", "send_money")
CONFIRM_TYPES = {"SOURCE_AWARE_CONFIRM", "VAGUE_CONFIRM"}

ROWS = [
    ("sa_llm", "rule_v1", "llm_user"),
    ("vague_llm", "baseline_vague", "llm_user"),
    ("sa_oracle", "rule_v1", "oracle_strict"),
    ("vague_oracle", "baseline_vague", "oracle_strict"),
]


def _load_runs(logdir: Path) -> list[dict]:
    runs: list[dict] = []
    for path in sorted(logdir.glob("user_task_*.json")):
        with path.open() as handle:
            runs.append(json.load(handle))
    return runs


def _target_records(records: list[dict]) -> list[dict]:
    return [record for record in records if record.get("tool_name") in TARGET_TOOLS]


def _binding_summary(record: dict) -> str:
    binding = record.get("executed_binding") or record.get("tool_args") or {}
    if record.get("tool_name") == "send_email":
        return str(binding.get("recipients"))
    if record.get("tool_name") == "share_file":
        email = binding.get("email")
        permission = binding.get("permission")
        return f"{email} ({permission})"
    if record.get("tool_name") == "delete_file":
        return str(binding.get("file_id"))
    if record.get("tool_name") == "send_money":
        return str(binding.get("recipient"))
    return str(binding)


def _trajectory_summary(run: dict) -> tuple[str, str, str]:
    safeconfirm = run.get("safeconfirm") or {}
    records = safeconfirm.get("records") or []
    target_records = _target_records(records)
    if not target_records:
        return "none", "—", "No target-tool intervention records"

    executed = [record for record in target_records if record.get("executed")]
    confirms = [record for record in target_records if record.get("selected_intervention") in CONFIRM_TYPES]
    rejected = [record for record in confirms if record.get("confirmation_response") == "rejected"]
    repairs = [record for record in target_records if record.get("selected_intervention") == "REPAIR"]

    interventions = [record.get("selected_intervention") for record in target_records]
    path = " → ".join(dict.fromkeys(interventions))

    if executed:
        last = executed[-1]
        outcome = f"executed {last.get('tool_name')} via {last.get('selected_intervention')} → {_binding_summary(last)}"
    elif rejected:
        last = rejected[-1]
        outcome = (
            f"stalled after {len(rejected)} rejected confirm(s); "
            f"last={last.get('selected_intervention')} args={_binding_summary(last)}"
        )
    elif repairs:
        outcome = f"repair path without successful execution ({len(repairs)} repair attempt(s))"
    else:
        last = target_records[-1]
        outcome = f"no execution; last={last.get('selected_intervention')} args={_binding_summary(last)}"

    return path, str(len(target_records)), outcome


def _is_issue(run: dict) -> bool:
    if run.get("benign"):
        return not run.get("utility")
    return not run.get("utility") or run.get("attack_succeeded")


def _format_table(rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._\n"

    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    lines: list[str] = []
    for row_index, row in enumerate(rows):
        line = " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        lines.append(f"| {line} |")
        if row_index == 0:
            lines.append("| " + " | ".join("-" * width for width in widths) + " |")
    return "\n".join(lines) + "\n"


def build_appendix(logroot: Path, suite: str) -> str:
    sections: list[str] = [
        "# Confirm Ablation Trajectory Appendix",
        "",
        f"Generated from `{logroot}` (`{suite}`).",
        "",
        "Issue cases: benign utility failure, corruption utility failure, or corruption attack success.",
        "",
    ]

    for row_id, policy, confirmer in ROWS:
        logdir = logroot / row_id / suite
        if not logdir.exists():
            sections.append(f"## {row_id} ({policy}, {confirmer})\n\n_Missing logdir: `{logdir}`_\n")
            continue

        runs = _load_runs(logdir)
        issue_runs = [run for run in runs if _is_issue(run)]
        ok_count = len(runs) - len(issue_runs)

        sections.append(f"## {row_id} ({policy}, {confirmer})")
        sections.append("")
        sections.append(f"Trajectory OK: **{ok_count}/{len(runs)}** | Issue cases: **{len(issue_runs)}**")
        sections.append("")

        if not issue_runs:
            sections.append("_No issue cases._")
            sections.append("")
            continue

        table_rows = [
            [
                "Case",
                "Benign",
                "Utility",
                "Attack",
                "Attempts",
                "Intervention path",
                "Outcome",
            ]
        ]
        for run in sorted(issue_runs, key=lambda item: item["case_id"]):
            path, attempts, outcome = _trajectory_summary(run)
            table_rows.append(
                [
                    run["case_id"],
                    "yes" if run.get("benign") else "no",
                    str(run.get("utility")),
                    str(run.get("attack_succeeded")),
                    attempts,
                    path,
                    outcome,
                ]
            )

        sections.append(_format_table(table_rows))

    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export confirm-ablation stall trajectory appendix.")
    parser.add_argument("--logroot", type=Path, default=Path("runs/bridge/confirm_ablation_v2"))
    parser.add_argument("--suite", type=str, default="safeconfirm_workspace")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output markdown path (default: <logroot>/trajectory_appendix.md).",
    )
    args = parser.parse_args()

    output = args.output or (args.logroot / "trajectory_appendix.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_appendix(args.logroot, args.suite), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
