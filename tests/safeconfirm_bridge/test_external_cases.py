from __future__ import annotations

import importlib

import pytest

from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm_bridge.case_registry import EXTERNAL_CASES_PATH, cases_for_suite


@pytest.fixture(scope="module", autouse=True)
def load_bridge_modules() -> None:
    importlib.import_module("safeconfirm_bridge.benchmark")
    importlib.import_module("safeconfirm_bridge.attacks.parameter_poison_attack")


def test_external_cases_load() -> None:
    cases = load_benchmark_cases(EXTERNAL_CASES_PATH)
    assert 12 <= len(cases) <= 16


def test_external_suite_registration() -> None:
    cases = cases_for_suite("safeconfirm_workspace_external")
    assert len(cases) == len(load_benchmark_cases(EXTERNAL_CASES_PATH))
    assert all(case.native_lineage for case in cases)
    assert all(case.e2e is not None for case in cases)


def test_external_ground_truth_labels() -> None:
    for case in cases_for_suite("safeconfirm_workspace_external"):
        gt = case.ground_truth
        assert gt.safe_interventions
        assert gt.unsafe_interventions
        assert gt.laundering_interventions
        if case.benign:
            assert "ALLOW" in gt.safe_interventions
        else:
            assert "ALLOW" in gt.unsafe_interventions
            assert "VAGUE_CONFIRM" in gt.laundering_interventions


def test_external_tool_and_slot_diversity() -> None:
    cases = load_benchmark_cases(EXTERNAL_CASES_PATH)
    tools = {case.tool_name for case in cases}
    slots = {next(iter(case.corrupted_slots.keys()), None) for case in cases if case.corrupted_slots}
    slots.discard(None)
    assert len(tools) >= 4
    assert len(slots) >= 5


def test_external_suite_checks() -> None:
    from agentdojo.task_suite.load_suites import get_suite
    from safeconfirm_bridge.benchmark import BENCHMARK_VERSION
    from safeconfirm_bridge.check import check_safeconfirm_suite

    suite = get_suite(BENCHMARK_VERSION, "safeconfirm_workspace_external")
    assert check_safeconfirm_suite(suite)
