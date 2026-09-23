#!/usr/bin/env python3
"""Aggregate native AgentDojo logdirs into coverage + utility/security + SDR/CLR tables."""

from __future__ import annotations

from pathlib import Path

import click

from safeconfirm.evaluation.native_aggregate import (
    compare_native_logdirs,
    print_comparison_table,
    save_comparison,
)


@click.command()
@click.option(
    "--run",
    "runs",
    multiple=True,
    required=True,
    help="Defense label and log directory as NAME:PATH.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write full JSON report (NativeComparisonModel).",
)
def main(runs: tuple[str, ...], output: Path | None) -> None:
    pairs: list[tuple[str, Path]] = []
    for item in runs:
        if ":" not in item:
            raise click.ClickException(f"Expected NAME:PATH, got {item!r}")
        label, raw_path = item.split(":", 1)
        logdir = Path(raw_path)
        if not logdir.is_dir():
            raise click.ClickException(f"Missing log directory: {logdir}")
        pairs.append((label, logdir))

    comparison = compare_native_logdirs(pairs)
    print_comparison_table(comparison)
    if output is not None:
        save_comparison(comparison, output)
        print(f"\nSaved report to {output}")


if __name__ == "__main__":
    main()
