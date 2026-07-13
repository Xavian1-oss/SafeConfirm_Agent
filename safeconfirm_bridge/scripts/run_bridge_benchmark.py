from __future__ import annotations

import importlib
import warnings
from pathlib import Path

import click
from dotenv import load_dotenv

from agentdojo.attacks.attack_registry import load_attack
from agentdojo.models import ModelsEnum
from agentdojo.task_suite.load_suites import get_suite

from safeconfirm_bridge.benchmark import BENCHMARK_VERSION
from safeconfirm_bridge.case_registry import matched_injection_task_id
from safeconfirm_bridge.e2e_metrics import compute_e2e_metrics, save_e2e_metrics
from safeconfirm_bridge.pipeline_factory import build_bridge_pipeline
from safeconfirm_bridge.runner import run_matched_pair


def _print_metrics(metrics) -> None:
    print("--- E2E core ---")
    print(f"Confirmer: {metrics.confirmer}")
    if metrics.confirmer_model:
        print(f"Confirmer model: {metrics.confirmer_model}")
    print(f"TSR: {metrics.tsr * 100:.2f}% | ASR (corruption): {metrics.asr * 100:.2f}%")
    print(
        f"Corruption TSR: {metrics.corruption_tsr * 100:.2f}% | "
        f"Benign TSR: {metrics.benign_tsr * 100:.2f}%"
    )
    print(
        f"Defense success: {metrics.defense_success_rate * 100:.2f}% | "
        f"Action rate: {metrics.action_rate * 100:.2f}% | "
        f"Stall rate: {metrics.stall_rate * 100:.2f}%"
    )
    print("--- Intervention metrics ---")
    print(
        f"UAR: {metrics.uar * 100:.2f}% | CLR: {metrics.clr * 100:.2f}% | "
        f"SDR: {metrics.sdr * 100:.2f}% | RSR: {metrics.rsr * 100:.2f}% | "
        f"VCR: {metrics.vcr * 100:.2f}%"
    )
    print(f"FBR: {metrics.fbr * 100:.2f}% | Composite: {metrics.composite * 100:.2f}%")
    counts = metrics.intervention_counts.model_dump()
    printed = ", ".join(f"{name}={value}" for name, value in counts.items() if value)
    if printed:
        print(f"Interventions: {printed}")


def _run_matched_pairs(
    suite_name: str,
    model: ModelsEnum,
    attack_name: str | None,
    defense: str | None,
    logdir: Path,
    user_tasks: tuple[str, ...],
    confirmer_model: str | None,
):
    if not load_dotenv(".env"):
        warnings.warn("No .env file found")

    suite = get_suite(BENCHMARK_VERSION, suite_name)
    pipeline = build_bridge_pipeline(model, defense, confirmer_model=confirmer_model)

    user_task_ids = list(user_tasks) if user_tasks else list(suite.user_tasks)
    attack = load_attack(attack_name, suite, pipeline) if attack_name is not None else None
    runs = []

    for user_task_id in user_task_ids:
        user_task = suite.get_user_task_by_id(user_task_id)
        injection_task_id = matched_injection_task_id(user_task_id)
        injection_task = suite.get_injection_task_by_id(injection_task_id)

        if attack is None:
            injections: dict[str, str] = {}
        else:
            injections = attack.attack(user_task, injection_task)

        save_path = logdir / f"{user_task_id}__{injection_task_id}.json"
        result = run_matched_pair(
            suite,
            pipeline,
            user_task,
            injection_task,
            injections,
            suite_name,
            confirmer_model=confirmer_model,
            save_path=save_path,
        )
        runs.append(result)

    return runs


@click.command()
@click.option("--suite", "-s", "suite_name", required=True, type=str)
@click.option("--model", "-m", "model", type=ModelsEnum, default=ModelsEnum.GPT_4O_2024_05_13)
@click.option("--attack", "-a", "attack_name", type=str, default="parameter_poison")
@click.option("--defense", "-d", "defense", type=str, default=None)
@click.option(
    "--confirmer-model",
    type=str,
    default=None,
    help="LLM model for simulated user confirmation (default: gpt-4o-mini-2024-07-18).",
)
@click.option("--logdir", type=click.Path(path_type=Path), default=Path("runs/bridge"))
@click.option("--user-task", "-ut", "user_tasks", multiple=True, default=())
@click.option(
    "--module-to-load",
    "-ml",
    "modules_to_load",
    multiple=True,
    default=("safeconfirm_bridge.benchmark", "safeconfirm_bridge.attacks.parameter_poison_attack"),
)
def main(
    suite_name: str,
    model: ModelsEnum,
    attack_name: str | None,
    defense: str | None,
    confirmer_model: str | None,
    logdir: Path,
    user_tasks: tuple[str, ...],
    modules_to_load: tuple[str, ...],
) -> None:
    for module in modules_to_load:
        importlib.import_module(module)

    run_logdir = logdir / suite_name
    runs = _run_matched_pairs(
        suite_name=suite_name,
        model=model,
        attack_name=attack_name,
        defense=defense,
        logdir=run_logdir,
        user_tasks=user_tasks,
        confirmer_model=confirmer_model,
    )

    metrics = compute_e2e_metrics(runs)
    save_e2e_metrics(run_logdir / "metrics.json", metrics)

    print(f"Suite: {suite_name}")
    print(f"Matched pairs: {len(runs)}")
    print("Cases source: safeconfirm/data/benchmark_cases_e2e.yaml")
    for run in runs:
        print(
            f"  {run.user_task_id} + {run.injection_task_id} ({run.case_id}): "
            f"utility={run.utility}, attack_succeeded={run.attack_succeeded}, "
            f"action={run.target_tool_called}"
        )
    _print_metrics(metrics)
    print(f"Saved per-case logs and metrics under {run_logdir}")
    print("Note: utility=True means user task succeeded; attack_succeeded=True means parameter poison applied.")


if __name__ == "__main__":
    main()
