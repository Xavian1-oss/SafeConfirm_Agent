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
    print(f"Policy: {metrics.policy_backend} | Confirmer: {metrics.confirmer}")
    if metrics.confirmer_model:
        print(f"Confirmer model: {metrics.confirmer_model}")
    print(f"TSR: {metrics.tsr * 100:.2f}% | ASR (corruption): {metrics.asr * 100:.2f}%")
    print(f"Corruption TSR: {metrics.corruption_tsr * 100:.2f}% | Benign TSR: {metrics.benign_tsr * 100:.2f}%")
    print(
        f"Defense success: {metrics.defense_success_rate * 100:.2f}% | "
        f"Action rate: {metrics.action_rate * 100:.2f}% | "
        f"Stall rate: {metrics.stall_rate * 100:.2f}%"
    )
    print("--- Intervention metrics ---")
    print(
        f"UAR (binding): {metrics.uar * 100:.2f}% | UAR-after-confirm: {metrics.uar_after_confirm * 100:.2f}% | "
        f"CLR: {metrics.clr * 100:.2f}% | SDR: {metrics.sdr * 100:.2f}%"
    )
    print(
        f"Confirm total: {metrics.confirm_total} | Approval rate: {metrics.confirm_approval_rate * 100:.2f}% | "
        f"Exec rate: {metrics.confirm_exec_rate * 100:.2f}%"
    )
    print(
        f"RSR: {metrics.rsr * 100:.2f}% | VCR: {metrics.vcr * 100:.2f}% | "
        f"FBR: {metrics.fbr * 100:.2f}% | Composite: {metrics.composite * 100:.2f}%"
    )
    counts = metrics.intervention_counts.model_dump()
    printed = ", ".join(f"{name}={value}" for name, value in counts.items() if value)
    if printed:
        print(f"Interventions: {printed}")


def _resolve_policy_backend(defense: str | None, policy: str | None) -> str | None:
    if policy is not None:
        return policy
    if defense == "safeconfirm_retrieval":
        return "retrieval"
    if defense == "safeconfirm":
        return "rule_v1"
    if defense == "safeconfirm_log_only":
        return "log_only"
    return None


def _run_matched_pairs(
    suite_name: str,
    model: ModelsEnum,
    attack_name: str | None,
    defense: str | None,
    logdir: Path,
    user_tasks: tuple[str, ...],
    policy_backend: str | None,
    confirmer: str,
    confirmer_model: str | None,
    enable_repair: bool | None,
):
    if not load_dotenv(".env"):
        warnings.warn("No .env file found")

    suite = get_suite(BENCHMARK_VERSION, suite_name)
    resolved_policy = _resolve_policy_backend(defense, policy_backend)
    pipeline = build_bridge_pipeline(
        model,
        defense,
        policy_backend=resolved_policy if defense and defense.startswith("safeconfirm") else policy_backend,
        confirmer=confirmer,
        confirmer_model=confirmer_model,
        enable_repair=enable_repair,
    )

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
            policy_backend=resolved_policy,
            confirmer=confirmer,
            confirmer_model=confirmer_model,
            save_path=save_path,
        )
        runs.append(result)

    return runs


@click.command()
@click.option("--suite", "-s", "suite_name", required=True, type=str)
@click.option("--model", "-m", "model", type=ModelsEnum, default=ModelsEnum("deepseek-chat"))
@click.option("--attack", "-a", "attack_name", type=str, default="parameter_poison")
@click.option("--defense", "-d", "defense", type=str, default=None)
@click.option(
    "--policy",
    type=click.Choice(["rule_v1", "baseline_vague", "retrieval"]),
    default=None,
    help="SafeConfirm policy backend (rule_v1=source-aware, baseline_vague=vague confirm).",
)
@click.option(
    "--confirmer",
    type=click.Choice(["llm_user", "oracle_strict"]),
    default="llm_user",
    help="Simulated user confirmer (llm_user or oracle_strict).",
)
@click.option(
    "--confirmer-model",
    type=str,
    default=None,
    help="LLM model for simulated user confirmation (default: gpt-4o-mini-2024-07-18).",
)
@click.option(
    "--no-repair",
    is_flag=True,
    default=False,
    help="Disable REPAIR (H2 ablation: rule_v1 without contact lookup repair).",
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
    policy: str | None,
    confirmer: str,
    confirmer_model: str | None,
    no_repair: bool,
    logdir: Path,
    user_tasks: tuple[str, ...],
    modules_to_load: tuple[str, ...],
) -> None:
    for module in modules_to_load:
        importlib.import_module(module)

    run_logdir = logdir / suite_name
    resolved_policy = _resolve_policy_backend(defense, policy)
    runs = _run_matched_pairs(
        suite_name=suite_name,
        model=model,
        attack_name=attack_name,
        defense=defense,
        logdir=run_logdir,
        user_tasks=user_tasks,
        policy_backend=resolved_policy,
        confirmer=confirmer,
        confirmer_model=confirmer_model,
        enable_repair=False if no_repair else None,
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
    print("Note: utility=True means user task succeeded; attack_succeeded=True means poison side effects applied.")


if __name__ == "__main__":
    main()
