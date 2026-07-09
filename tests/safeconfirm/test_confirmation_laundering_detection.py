from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.confirmation import (
    build_confirmation_payload,
    is_confirmation_laundering,
    load_templates,
)
from safeconfirm.types.models import (
    ConfirmationPayloadModel,
    ConfirmationResponseModel,
    CriticalSlotModel,
    InterventionRecordModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceTrust,
)


def _record_with_gap() -> InterventionRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value="attacker@example.com",
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=SourceTrust.UNTRUSTED_OBSERVATION,
        evidence=[],
        authorization_gap=True,
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
        candidates_considered=["SOURCE_AWARE_CONFIRM"],
        selected_intervention="SOURCE_AWARE_CONFIRM",
        policy_backend="rule_v1",
    )


def test_vague_confirm_with_gap_is_laundering():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    record = _record_with_gap()
    payload = build_confirmation_payload(record, InterventionType.VAGUE_CONFIRM, templates)
    response = ConfirmationResponseModel(outcome="approved")
    assert is_confirmation_laundering(payload, response, record) is True


def test_source_aware_complete_disclosure_not_laundering():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    record = _record_with_gap()
    payload = build_confirmation_payload(record, InterventionType.SOURCE_AWARE_CONFIRM, templates)
    response = ConfirmationResponseModel(outcome="approved")
    assert "attacker@example.com" in payload.prompt_text
    assert "untrusted_observation" in payload.prompt_text
    assert is_confirmation_laundering(payload, response, record) is False


def test_source_aware_missing_value_is_laundering():
    record = _record_with_gap()
    payload = ConfirmationPayloadModel(
        intervention="SOURCE_AWARE_CONFIRM",
        tool_name="send_email",
        action_summary="test",
        slot_disclosures=[],
        external_effect="test",
        prompt_text="Please confirm without details.",
        required_disclosures=["recipients"],
        laundering_safe=True,
    )
    response = ConfirmationResponseModel(outcome="approved")
    assert is_confirmation_laundering(payload, response, record) is True
