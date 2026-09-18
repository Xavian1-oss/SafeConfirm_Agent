from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.types.models import BenchmarkCaseModel

DEFAULT_CASES_PATH = Path(__file__).resolve().parents[1] / "safeconfirm/data/benchmark_cases_e2e.yaml"
EXTERNAL_CASES_PATH = Path(__file__).resolve().parents[1] / "safeconfirm/data/benchmark_cases_external.yaml"
POISON_VECTOR = "safeconfirm_poison"
BRIDGE_SUITE_MAP = {
    "safeconfirm_workspace": "workspace",
    "safeconfirm_banking": "banking",
    "safeconfirm_workspace_external": "workspace",
}


def cases_path_for_suite(suite_name: str) -> Path:
    if suite_name == "safeconfirm_workspace_external":
        return EXTERNAL_CASES_PATH
    return DEFAULT_CASES_PATH


def canonical_suite_name(suite_name: str) -> str:
    return BRIDGE_SUITE_MAP.get(suite_name, suite_name)


@lru_cache
def load_all_cases(path: str | None = None) -> list[BenchmarkCaseModel]:
    cases_path = Path(path) if path is not None else DEFAULT_CASES_PATH
    return load_benchmark_cases(cases_path)


def load_external_cases() -> list[BenchmarkCaseModel]:
    return load_benchmark_cases(EXTERNAL_CASES_PATH)


def cases_for_suite(suite_name: str, path: str | None = None) -> list[BenchmarkCaseModel]:
    canonical = canonical_suite_name(suite_name)
    cases_path = Path(path) if path is not None else cases_path_for_suite(suite_name)
    return [case for case in load_benchmark_cases(cases_path) if case.suite == canonical]


def case_by_user_task_id(task_id: str, suite_name: str, path: str | None = None) -> BenchmarkCaseModel | None:
    if not task_id.startswith("user_task_"):
        return None
    try:
        index = int(task_id.removeprefix("user_task_"))
    except ValueError:
        return None
    cases = cases_for_suite(suite_name, path)
    if index < 0 or index >= len(cases):
        return None
    return cases[index]


def matched_injection_task_id(user_task_id: str) -> str:
    return user_task_id.replace("user_task_", "injection_task_")


def holdout_cases_for_suite(suite_name: str, path: str | None = None) -> list[BenchmarkCaseModel]:
    return [case for case in cases_for_suite(suite_name, path) if case.holdout]


def holdout_user_task_ids(suite_name: str, path: str | None = None) -> list[str]:
    cases = cases_for_suite(suite_name, path)
    return [f"user_task_{index}" for index, case in enumerate(cases) if case.holdout]
