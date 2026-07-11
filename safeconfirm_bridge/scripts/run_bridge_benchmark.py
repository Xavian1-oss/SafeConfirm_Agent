from __future__ import annotations

import importlib
import warnings
from pathlib import Path

import click
from dotenv import load_dotenv

from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, PipelineConfig
from agentdojo.attacks.attack_registry import load_attack
from agentdojo.benchmark import aggregate_results
from agentdojo.logging import OutputLogger
from agentdojo.models import ModelsEnum
from agentdojo.task_suite.load_suites import get_suite

from safeconfirm_bridge.benchmark import BENCHMARK_VERSION
from safeconfirm_bridge.case_registry import matched_injection_task_id
from safeconfirm_bridge.runner import run_matched_pair_with_case_metadata


def _run_matched_pairs(
    suite_name: str,
    model: ModelsEnum,
    attack_name: str | None,
    defense: str | None,
    logdir: Path,
    force_rerun: bool,
    user_tasks: tuple[str, ...],
) -> tuple[dict[tuple[str, str], bool], dict[tuple[str, str], bool]]:
    if not load_dotenv(".env"):
        warnings.warn("No .env file found")

    suite = get_suite(BENCHMARK_VERSION, suite_name)
    pipeline = AgentPipeline.from_config(
        PipelineConfig(
            llm=model,
            model_id=None,
            defense=defense,
            system_message_name=None,
            system_message=None,
        ),
    )
    utility_results: dict[tuple[str, str], bool] = {}
    security_results: dict[tuple[str, str], bool] = {}

    user_task_ids = list(user_tasks) if user_tasks else list(suite.user_tasks)
    attack = load_attack(attack_name, suite, pipeline) if attack_name is not None else None

    with OutputLogger(str(logdir)):
        for user_task_id in user_task_ids:
            user_task = suite.get_user_task_by_id(user_task_id)
            injection_task_id = matched_injection_task_id(user_task_id)
            injection_task = suite.get_injection_task_by_id(injection_task_id)

            if attack is None:
                injections: dict[str, str] = {}
            else:
                injections = attack.attack(user_task, injection_task)

            utility, security = run_matched_pair_with_case_metadata(
                suite,
                pipeline,
                user_task,
                injection_task,
                injections,
                suite_name,
            )
            utility_results[(user_task_id, injection_task_id)] = utility
            security_results[(user_task_id, injection_task_id)] = security

    return utility_results, security_results


@click.command()
@click.option("--suite", "-s", "suite_name", required=True, type=str)
@click.option("--model", "-m", "model", type=ModelsEnum, default=ModelsEnum.GPT_4O_2024_05_13)
@click.option("--attack", "-a", "attack_name", type=str, default="parameter_poison")
@click.option("--defense", "-d", "defense", type=str, default=None)
@click.option("--logdir", type=click.Path(path_type=Path), default=Path("runs/bridge"))
@click.option("--force-rerun", "-f", is_flag=True, default=False)
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
    logdir: Path,
    force_rerun: bool,
    user_tasks: tuple[str, ...],
    modules_to_load: tuple[str, ...],
) -> None:
    for module in modules_to_load:
        importlib.import_module(module)

    utility_results, security_results = _run_matched_pairs(
        suite_name=suite_name,
        model=model,
        attack_name=attack_name,
        defense=defense,
        logdir=logdir / suite_name,
        force_rerun=force_rerun,
        user_tasks=user_tasks,
    )

    avg_utility = aggregate_results([utility_results])
    avg_security = aggregate_results([security_results])
    print(f"Suite: {suite_name}")
    print(f"Matched pairs: {len(utility_results)}")
    for (user_task_id, injection_task_id), utility in utility_results.items():
        security = security_results[(user_task_id, injection_task_id)]
        print(
            f"  {user_task_id} + {injection_task_id}: "
            f"utility={utility}, attack_succeeded={security}"
        )
    print(f"Average utility (TSR): {avg_utility * 100:.2f}%")
    print(f"Average attack success (ASR): {avg_security * 100:.2f}%")
    print("Note: utility=True means user task succeeded; attack_succeeded=True means parameter poison applied.")
    print(f"Cases source: safeconfirm/data/benchmark_cases_e2e.yaml")


if __name__ == "__main__":
    main()
