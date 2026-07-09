from pathlib import Path

from agentdojo.functions_runtime import FunctionCall
from safeconfirm.analysis.source_analyzer import analyze_sources
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.evaluation.metrics import executed_with_untrusted_binding
from safeconfirm.evaluation.run_case import _messages_from_case, run_benchmark_case
from safeconfirm.extraction.registry_loader import load_registry
from safeconfirm.extraction.slot_extractor import extract_critical_slots
from safeconfirm.learning.experience_store import ExperienceStore
from safeconfirm.policy.retrieval_policy import RetrievalPolicy
from safeconfirm.types.models import InterventionType

BENCHMARK_CASES_PATH = Path(__file__).resolve().parents[2] / "safeconfirm/data/benchmark_cases.yaml"


def test_benign_share_case_passes_under_allow_policy():
    config = SafeConfirmConfig.load()
    cases = load_benchmark_cases(BENCHMARK_CASES_PATH)
    case = next(item for item in cases if item.id == "ws_share_benign_explicit_v1")
    result = run_benchmark_case(case, "P1", config=config)
    assert result.utility is True
    assert result.security is True


def test_retrieval_does_not_block_no_gap_benign_transfer():
    config = SafeConfirmConfig.load()
    cases = load_benchmark_cases(BENCHMARK_CASES_PATH)
    case = next(item for item in cases if item.id == "bk_transfer_benign_explicit_v1")
    registry = load_registry(config.registry_path)
    messages = _messages_from_case(case)
    tool_call = FunctionCall(function=case.tool_name, args=case.tool_args, id="call")
    extraction = extract_critical_slots(tool_call.function, dict(tool_call.args), registry)
    analysis = analyze_sources(case.query, messages, extraction, registry)
    retrieval = RetrievalPolicy(ExperienceStore(config.experiences_path), top_k=config.retrieval_top_k)

    selected = retrieval.select_intervention(analysis, registry, case.tool_name, True, True)

    assert analysis.has_untrusted_binding is False
    assert selected == InterventionType.ALLOW


def test_p5_no_longer_leaks_advisor_email_case():
    config = SafeConfirmConfig.load()
    cases = load_benchmark_cases(BENCHMARK_CASES_PATH)
    case = next(item for item in cases if item.id == "ws_email_advisor_poison_v1")
    result = run_benchmark_case(case, "P5", config=config)
    record = result.safeconfirm.records[0]
    assert result.security is True
    assert executed_with_untrusted_binding(record) is False
    assert record.executed is False
    assert record.confirmation_response == "rejected"
