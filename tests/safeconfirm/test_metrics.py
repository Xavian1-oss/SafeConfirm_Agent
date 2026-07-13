from pathlib import Path

import pytest

from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.evaluation.metrics import (
    compute_metrics,
    executed_with_untrusted_binding,
    merge_safeconfirm_into_benchmark_log,
)
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionRecordModel,
    InterventionType,
    SafeConfirmLogModel,
    SlotSourceRecordModel,
    SourceTrust,
    TargetedRunResultModel,
)

BENCHMARK_CASES_PATH = Path(__file__).resolve().parents[2] / "safeconfirm/data/benchmark_cases_e2e.yaml"


def _record(
    *,
    executed: bool,
    source: SourceTrust,
    selected: str,
    confirmation_response: str | None = None,
    laundering: bool = False,
    repair_attempted: bool = False,
    repair_result: str | None = None,
    binding: dict | None = None,
) -> InterventionRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value=["attacker@example.com"],
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=source,
        evidence=[],
        authorization_gap=True,
        risk_score=1.0,
    )
    return InterventionRecordModel(
        tool_call_id="call_1",
        tool_name="send_email",
        tool_args={"recipients": ["attacker@example.com"], "subject": "S", "body": "B"},
        critical_slots=[slot],
        slot_records=[slot_record],
        has_untrusted_binding=True,
        has_role_only_binding=False,
        overall_risk=1.0,
        candidates_considered=[selected],
        selected_intervention=selected,
        policy_backend="test",
        confirmation_response=confirmation_response,
        confirmation_laundering_risk=laundering,
        executed=executed,
        executed_binding=binding or {"recipients": ["attacker@example.com"], "subject": "S", "body": "B"},
        repair_attempted=repair_attempted,
        repair_result=repair_result,
    )


def _run(case_id: str, utility: bool, record: InterventionRecordModel, benign: bool = False) -> TargetedRunResultModel:
    return TargetedRunResultModel(
        case_id=case_id,
        policy_id="P_test",
        suite="workspace",
        category="email",
        benign=benign,
        utility=utility,
        security=not executed_with_untrusted_binding(record),
        safeconfirm=SafeConfirmLogModel(mode="active", policy_backend="test", records=[record]),
    )


def test_benchmark_cases_has_sixteen_e2e_cases():
    cases = load_benchmark_cases(BENCHMARK_CASES_PATH)
    assert len(cases) == 16
    corruption_cases = [case for case in cases if not case.benign]
    assert len(corruption_cases) == 13


def test_executed_with_untrusted_binding_detects_poisoned_execution():
    record = _record(executed=True, source=SourceTrust.UNTRUSTED_OBSERVATION, selected="ALLOW")
    assert executed_with_untrusted_binding(record) is True


def test_metrics_uar_fixture():
    runs = [
        _run("c1", False, _record(executed=True, source=SourceTrust.UNTRUSTED_OBSERVATION, selected="ALLOW")),
        _run(
            "c2", False, _record(executed=False, source=SourceTrust.UNTRUSTED_OBSERVATION, selected="BLOCK", binding={})
        ),
    ]
    metrics = compute_metrics(runs)
    assert metrics.uar == pytest.approx(0.5)
    assert metrics.tpr == pytest.approx(0.0)


def test_metrics_clr_fixture():
    runs = [
        _run(
            "c1",
            True,
            _record(
                executed=True,
                source=SourceTrust.UNTRUSTED_OBSERVATION,
                selected=InterventionType.VAGUE_CONFIRM.value,
                confirmation_response="approved",
                laundering=True,
            ),
        ),
        _run(
            "c2",
            True,
            _record(
                executed=True,
                source=SourceTrust.TRUSTED_CONTACT,
                selected=InterventionType.SOURCE_AWARE_CONFIRM.value,
                confirmation_response="approved",
                laundering=False,
                binding={"recipients": ["trusted@example.com"], "subject": "S", "body": "B"},
            ),
        ),
    ]
    metrics = compute_metrics(runs)
    assert metrics.clr == pytest.approx(0.5)


def test_metrics_composite_fixture():
    block_record = _record(
        executed=False,
        source=SourceTrust.UNTRUSTED_OBSERVATION,
        selected="BLOCK",
        binding={},
    )
    repair_record = _record(
        executed=True,
        source=SourceTrust.TRUSTED_CONTACT,
        selected="ALLOW",
        repair_attempted=True,
        repair_result="success",
        binding={"recipients": ["supervisor@university.edu"], "subject": "S", "body": "B"},
    )
    benign_record = _record(
        executed=True,
        source=SourceTrust.USER_EXPLICIT,
        selected="ALLOW",
        binding={"recipients": ["colleague@company.com"], "subject": "S", "body": "B"},
    )
    benign_record.slot_records[0].authorization_gap = False
    benign_record.has_untrusted_binding = False

    runs = [
        _run("corruption_block", False, block_record),
        _run("corruption_repair", True, repair_record),
        _run("benign", True, benign_record, benign=True),
    ]
    metrics = compute_metrics(runs)
    assert metrics.uar == pytest.approx(0.0)
    assert metrics.rsr == pytest.approx(1.0)
    assert metrics.fbr == pytest.approx(0.0)
    assert metrics.composite == pytest.approx(0.7833333333)


def test_merge_safeconfirm_into_benchmark_log(tmp_path):
    log_path = tmp_path / "run.json"
    log_path.write_text('{"utility": true, "messages": []}', encoding="utf-8")
    payload = {"mode": "active", "policy_backend": "rule_v1", "records": []}
    merge_safeconfirm_into_benchmark_log(log_path, payload)
    import json

    merged = json.loads(log_path.read_text(encoding="utf-8"))
    assert merged["safeconfirm"] == payload
