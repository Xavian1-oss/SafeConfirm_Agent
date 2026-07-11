from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.types.models import BenchmarkCaseModel

DEFAULT_L1_CASES_PATH = Path(__file__).resolve().parents[1] / "safeconfirm/data/benchmark_cases.yaml"
DEFAULT_E2E_CASES_PATH = Path(__file__).resolve().parents[1] / "safeconfirm/data/benchmark_cases_e2e.yaml"
DEFAULT_CASES_PATH = DEFAULT_E2E_CASES_PATH
POISON_VECTOR = "safeconfirm_poison"
BRIDGE_SUITE_MAP = {
    "safeconfirm_workspace": "workspace",
    "safeconfirm_banking": "banking",
}


def canonical_suite_name(suite_name: str) -> str:
    return BRIDGE_SUITE_MAP.get(suite_name, suite_name)


@lru_cache
def load_all_cases(path: str | None = None) -> list[BenchmarkCaseModel]:
    cases_path = Path(path) if path is not None else DEFAULT_CASES_PATH
    return load_benchmark_cases(cases_path)


def cases_for_suite(suite_name: str, path: str | None = None) -> list[BenchmarkCaseModel]:
    canonical = canonical_suite_name(suite_name)
    return [case for case in load_all_cases(path) if case.suite == canonical]


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
