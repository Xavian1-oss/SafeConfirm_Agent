from __future__ import annotations

import json
from pathlib import Path

import click


CORE_FIELDS = [
    ("tsr", "TSR"),
    ("asr", "ASR"),
    ("corruption_tsr", "Corruption TSR"),
    ("benign_tsr", "Benign TSR"),
    ("defense_success_rate", "Defense success"),
    ("stall_rate", "Stall rate"),
    ("fbr", "FBR"),
]

INTERVENTION_FIELDS = [
    ("uar", "UAR"),
    ("composite", "Composite"),
]


def _load_metrics(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _pct(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}%"


def _intervention_summary(metrics: dict) -> str:
    counts = metrics.get("intervention_counts") or {}
    parts = [f"{name}={value}" for name, value in counts.items() if value]
    return ", ".join(parts) if parts else "—"


def _print_table(rows: list[tuple[str, dict]]) -> None:
    headers = ["Defense"] + [label for _, label in CORE_FIELDS] + ["Interventions"]
    widths = [max(len(headers[0]), *(len(name) for name, _ in rows), 12)]
    for col_index, (key, label) in enumerate(CORE_FIELDS, start=1):
        column_values = [_pct(metrics.get(key)) for _, metrics in rows]
        widths.append(max(len(label), *(len(value) for value in column_values), 10))
    intervention_values = [_intervention_summary(metrics) for _, metrics in rows]
    widths.append(max(len(headers[-1]), *(len(value) for value in intervention_values), 12))

    def _row(cells: list[str]) -> str:
        return " | ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True))

    print(_row(headers))
    print("-+-".join("-" * width for width in widths))
    for name, metrics in rows:
        cells = [name]
        for key, _ in CORE_FIELDS:
            cells.append(_pct(metrics.get(key)))
        cells.append(_intervention_summary(metrics))
        print(_row(cells))


@click.command()
@click.option(
    "--run",
    "runs",
    multiple=True,
    required=True,
    help="Defense label and metrics directory as NAME:PATH (reads PATH/metrics.json).",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to save the comparison table as JSON.",
)
def main(runs: tuple[str, ...], output: Path | None) -> None:
    """Compare E2E metrics across defense baselines."""
    parsed_rows: list[tuple[str, dict]] = []
    export: dict[str, dict] = {}

    for item in runs:
        if ":" not in item:
            raise click.ClickException(f"Expected NAME:PATH, got {item!r}")
        name, raw_path = item.split(":", 1)
        metrics_path = Path(raw_path) / "metrics.json"
        if not metrics_path.exists():
            raise click.ClickException(f"Missing metrics file: {metrics_path}")
        metrics = _load_metrics(metrics_path)
        parsed_rows.append((name, metrics))
        export[name] = metrics

    _print_table(parsed_rows)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            json.dump(export, handle, indent=2)
        print(f"\nSaved comparison JSON to {output}")


if __name__ == "__main__":
    main()
