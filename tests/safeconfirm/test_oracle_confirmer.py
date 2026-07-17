from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.confirmation import build_confirmation_payload, load_templates
from safeconfirm.execution.oracle_confirmer import StrictOracleConfirmer
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionRecordModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceTrust,
)


def _record(
    *,
    intervention: str,
    source: SourceTrust,
    slot_class: str = "binding",
    authorization_gap: bool = True,
) -> InterventionRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value="attacker@example.com",
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
        slot_class=slot_class,  # type: ignore[arg-type]
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=source,
        evidence=[],
        authorization_gap=authorization_gap,
        risk_score=1.0,
    )
    return InterventionRecordModel(
        tool_call_id="call_1",
        tool_name="send_email",
        tool_args={"recipients": ["attacker@example.com"]},
        critical_slots=[slot],
        slot_records=[slot_record],
        has_untrusted_binding=True,
        has_role_only_binding=False,
        overall_risk=1.0,
        candidates_considered=[intervention],
        selected_intervention=intervention,
        policy_backend="test",
    )


def test_strict_oracle_rejects_vague_confirm():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    record = _record(intervention=InterventionType.VAGUE_CONFIRM.value, source=SourceTrust.UNTRUSTED_OBSERVATION)
    payload = build_confirmation_payload(record, InterventionType.VAGUE_CONFIRM, templates)
    response = StrictOracleConfirmer().respond(payload, record, {})
    assert response.outcome == "rejected"


def test_strict_oracle_rejects_untrusted_binding_gap():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    record = _record(intervention=InterventionType.SOURCE_AWARE_CONFIRM.value, source=SourceTrust.UNTRUSTED_OBSERVATION)
    payload = build_confirmation_payload(record, InterventionType.SOURCE_AWARE_CONFIRM, templates)
    response = StrictOracleConfirmer().respond(payload, record, {})
    assert response.outcome == "rejected"


def test_strict_oracle_approves_trusted_binding_gap():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    record = _record(intervention=InterventionType.SOURCE_AWARE_CONFIRM.value, source=SourceTrust.TRUSTED_CONTACT)
    payload = build_confirmation_payload(record, InterventionType.SOURCE_AWARE_CONFIRM, templates)
    response = StrictOracleConfirmer().respond(payload, record, {})
    assert response.outcome == "approved"
