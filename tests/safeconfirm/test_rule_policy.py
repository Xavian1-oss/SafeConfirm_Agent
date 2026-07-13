from safeconfirm.extraction.registry_loader import load_registry
from safeconfirm.policy.rule_policy import select_intervention
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceAnalysisResultModel,
    SourceTrust,
)


def _registry_path():
    from pathlib import Path

    return Path(__file__).resolve().parents[2] / "safeconfirm/data/tool_slot_registry.yaml"


def _analysis(has_gap: bool, role_only: bool = False) -> SourceAnalysisResultModel:
    slot = CriticalSlotModel(
        name="recipients",
        value="attacker@example.com",
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
        slot_class="binding",
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=SourceTrust.UNTRUSTED_OBSERVATION,
        evidence=[],
        authorization_gap=has_gap,
        risk_score=1.0 if has_gap else 0.0,
    )
    return SourceAnalysisResultModel(
        slot_records=[slot_record],
        overall_risk=0.8 if has_gap else 0.0,
        has_untrusted_binding=has_gap,
        has_role_only_binding=role_only,
        action_type_authorized=True,
    )


def test_baseline_allow():
    analysis = _analysis(has_gap=True)
    selected = select_intervention(
        analysis, load_registry(_registry_path()), "send_email", "baseline_allow", True, True
    )
    assert selected == InterventionType.ALLOW


def test_baseline_block():
    analysis = _analysis(has_gap=True)
    selected = select_intervention(
        analysis, load_registry(_registry_path()), "send_email", "baseline_block", True, True
    )
    assert selected == InterventionType.BLOCK


def test_baseline_vague():
    analysis = _analysis(has_gap=True)
    selected = select_intervention(
        analysis, load_registry(_registry_path()), "send_email", "baseline_vague", True, True
    )
    assert selected == InterventionType.VAGUE_CONFIRM


def test_rule_v1_role_binding_prefers_repair():
    analysis = _analysis(has_gap=True)
    analysis.has_role_only_binding = True
    analysis.slot_records[0].slot.role_label = "supervisor"
    selected = select_intervention(analysis, load_registry(_registry_path()), "send_email", "rule_v1", True, True)
    assert selected == InterventionType.REPAIR


def test_rule_v1_untrusted_without_role_uses_source_aware():
    analysis = _analysis(has_gap=True)
    selected = select_intervention(analysis, load_registry(_registry_path()), "send_email", "rule_v1", True, True)
    assert selected == InterventionType.SOURCE_AWARE_CONFIRM
