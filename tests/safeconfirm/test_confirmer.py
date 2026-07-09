from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.confirmation import build_confirmation_payload, load_templates
from safeconfirm.execution.confirmer import OracleConfirmer
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionRecordModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceTrust,
)


def _oracle_record(*, tool_args: dict, slot_records: list[SlotSourceRecordModel]) -> InterventionRecordModel:
    return InterventionRecordModel(
        tool_call_id="call_1",
        tool_name="send_email",
        tool_args=tool_args,
        critical_slots=[],
        slot_records=slot_records,
        has_untrusted_binding=any(r.authorization_gap for r in slot_records),
        has_role_only_binding=False,
        overall_risk=max((r.risk_score for r in slot_records), default=0.0),
        candidates_considered=[InterventionType.SOURCE_AWARE_CONFIRM.value],
        selected_intervention=InterventionType.SOURCE_AWARE_CONFIRM.value,
        policy_backend="rule_v1",
        executed=False,
    )


def test_oracle_rejects_when_trusted_slot_matches_but_other_gap_remains():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    confirmer = OracleConfirmer()
    record = _oracle_record(
        tool_args={"recipients": ["advisor@university.edu"], "subject": "Deadline", "body": "request"},
        slot_records=[
            SlotSourceRecordModel(
                slot=CriticalSlotModel(
                    name="recipients",
                    value=["advisor@university.edu"],
                    value_normalized="advisor@university.edu",
                    slot_type="email_list",
                    risk_weight=1.0,
                ),
                source=SourceTrust.TRUSTED_CONTACT,
                evidence=[],
                authorization_gap=False,
                risk_score=0.0,
            ),
            SlotSourceRecordModel(
                slot=CriticalSlotModel(
                    name="body",
                    value="request",
                    value_normalized="request",
                    slot_type="text",
                    risk_weight=0.6,
                ),
                source=SourceTrust.AGENT_INFERRED,
                evidence=[],
                authorization_gap=True,
                risk_score=0.54,
            ),
        ],
    )
    payload = build_confirmation_payload(record, InterventionType.SOURCE_AWARE_CONFIRM, templates)
    extra_args = {
        "safeconfirm": {
            "benchmark_case": {
                "corrupted_slots": {"recipients": "attacker@example.com"},
                "trusted_binding": {"recipients": "advisor@university.edu"},
            }
        }
    }

    response = confirmer.respond(payload, record, extra_args)

    assert response.outcome == "rejected"
    assert response.raw_text == "oracle_reject_gap"


def test_oracle_approves_when_all_gaps_cleared_and_trusted_binding_matches():
    config = SafeConfirmConfig.load()
    templates = load_templates(config.templates_path)
    confirmer = OracleConfirmer()
    record = _oracle_record(
        tool_args={"recipients": ["advisor@university.edu"], "subject": "Deadline", "body": "request"},
        slot_records=[
            SlotSourceRecordModel(
                slot=CriticalSlotModel(
                    name="recipients",
                    value=["advisor@university.edu"],
                    value_normalized="advisor@university.edu",
                    slot_type="email_list",
                    risk_weight=1.0,
                ),
                source=SourceTrust.TRUSTED_CONTACT,
                evidence=[],
                authorization_gap=False,
                risk_score=0.0,
            ),
            SlotSourceRecordModel(
                slot=CriticalSlotModel(
                    name="body",
                    value="request",
                    value_normalized="request",
                    slot_type="text",
                    risk_weight=0.6,
                ),
                source=SourceTrust.USER_EXPLICIT,
                evidence=[],
                authorization_gap=False,
                risk_score=0.0,
            ),
        ],
    )
    payload = build_confirmation_payload(record, InterventionType.SOURCE_AWARE_CONFIRM, templates)
    extra_args = {
        "safeconfirm": {
            "benchmark_case": {
                "corrupted_slots": {"recipients": "attacker@example.com"},
                "trusted_binding": {"recipients": "advisor@university.edu"},
            }
        }
    }

    response = confirmer.respond(payload, record, extra_args)

    assert response.outcome == "approved"
    assert response.raw_text == "oracle_approve_trusted"
