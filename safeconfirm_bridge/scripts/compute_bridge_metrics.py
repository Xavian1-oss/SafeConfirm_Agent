from __future__ import annotations

from pathlib import Path

import click

from safeconfirm_bridge.e2e_metrics import compute_e2e_metrics, load_e2e_runs, save_e2e_metrics


def _print_metrics(metrics) -> None:
    print(f"Confirmer: {metrics.confirmer}")
    if metrics.confirmer_model:
        print(f"Confirmer model: {metrics.confirmer_model}")
    print(f"Cases: {metrics.total_cases} (corruption={metrics.corruption_cases}, benign={metrics.benign_cases})")
    print("--- E2E core ---")
    print(f"TSR: {metrics.tsr * 100:.2f}% | ASR: {metrics.asr * 100:.2f}%")
    print(f"Corruption TSR: {metrics.corruption_tsr * 100:.2f}% | Benign TSR: {metrics.benign_tsr * 100:.2f}%")
    print(f"Defense success: {metrics.defense_success_rate * 100:.2f}%")
    print(f"Action rate: {metrics.action_rate * 100:.2f}% | Stall rate: {metrics.stall_rate * 100:.2f}%")
    print("--- Intervention metrics ---")
    print(f"UAR: {metrics.uar * 100:.2f}% | CLR: {metrics.clr * 100:.2f}% | SDR: {metrics.sdr * 100:.2f}%")
    print(f"RSR: {metrics.rsr * 100:.2f}% | VCR: {metrics.vcr * 100:.2f}% | FBR: {metrics.fbr * 100:.2f}%")
    print(f"Composite: {metrics.composite * 100:.2f}%")


@click.command()
@click.option("--logdir", type=click.Path(path_type=Path), required=True)
@click.option("--output", type=click.Path(path_type=Path), default=None)
def main(logdir: Path, output: Path | None) -> None:
    runs = load_e2e_runs(logdir)
    if not runs:
        raise click.ClickException(f"No E2E run JSON files found under {logdir}")
    metrics = compute_e2e_metrics(runs)
    _print_metrics(metrics)
    output_path = output or (logdir / "metrics.json")
    save_e2e_metrics(output_path, metrics)
    print(f"Saved metrics to {output_path}")


if __name__ == "__main__":
    main()
