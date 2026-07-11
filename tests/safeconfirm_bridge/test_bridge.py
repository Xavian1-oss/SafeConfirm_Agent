from __future__ import annotations

import importlib

import pytest

from safeconfirm_bridge.case_registry import (
    POISON_VECTOR,
    case_by_user_task_id,
    cases_for_suite,
    matched_injection_task_id,
)
from safeconfirm_bridge.check import check_safeconfirm_suite


@pytest.fixture(scope="module", autouse=True)
def load_bridge_modules() -> None:
    importlib.import_module("safeconfirm_bridge.benchmark")
    importlib.import_module("safeconfirm_bridge.attacks.parameter_poison_attack")


def test_workspace_case_count() -> None:
    cases = cases_for_suite("safeconfirm_workspace")
    assert len(cases) == 12


def test_banking_case_count() -> None:
    cases = cases_for_suite("safeconfirm_banking")
    assert len(cases) == 4


def test_case_lookup_by_task_id() -> None:
    case = case_by_user_task_id("user_task_0", "safeconfirm_workspace")
    assert case is not None
    assert case.id == "ws_email_supervisor_e2e"


def test_matched_injection_task_id() -> None:
    assert matched_injection_task_id("user_task_3") == "injection_task_3"


def test_parameter_poison_attack_matched_pair() -> None:
    from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
    from agentdojo.attacks.attack_registry import load_attack
    from safeconfirm_bridge.suites.workspace.task_suite import task_suite

    attack = load_attack("parameter_poison", task_suite, GroundTruthPipeline(None))
    user_task = task_suite.get_user_task_by_id("user_task_0")
    injection_task = task_suite.get_injection_task_by_id("injection_task_0")
    injections = attack.attack(user_task, injection_task)
    assert POISON_VECTOR in injections
    assert "attacker@example.com" in injections[POISON_VECTOR]


def test_parameter_poison_attack_unmatched_pair_is_empty() -> None:
    from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
    from agentdojo.attacks.attack_registry import load_attack
    from safeconfirm_bridge.suites.workspace.task_suite import task_suite

    attack = load_attack("parameter_poison", task_suite, GroundTruthPipeline(None))
    user_task = task_suite.get_user_task_by_id("user_task_0")
    injection_task = task_suite.get_injection_task_by_id("injection_task_1")
    injections = attack.attack(user_task, injection_task)
    assert injections == {POISON_VECTOR: ""}


@pytest.mark.parametrize("suite_name", ["safeconfirm_workspace", "safeconfirm_banking"])
def test_safeconfirm_suite_checks(suite_name: str) -> None:
    from agentdojo.task_suite.load_suites import get_suite
    from safeconfirm_bridge.benchmark import BENCHMARK_VERSION

    suite = get_suite(BENCHMARK_VERSION, suite_name)
    assert check_safeconfirm_suite(suite)
