from __future__ import annotations

from unittest.mock import MagicMock

from safeconfirm.execution.llm_user_confirmer import LLMUserConfirmer, parse_llm_decision
from safeconfirm.types.models import ConfirmationPayloadModel, InterventionRecordModel


def test_parse_llm_decision_accepts_json_approval():
    assert parse_llm_decision('{"decision": "approved", "reason": "matches request"}') == "approved"


def test_parse_llm_decision_rejects_unknown_payload():
    assert parse_llm_decision("maybe") == "rejected"


def test_llm_user_confirmer_uses_only_user_query():
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content='{"decision":"rejected","reason":"external email"}'))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    confirmer = LLMUserConfirmer(client=mock_client)
    payload = ConfirmationPayloadModel(
        intervention="SOURCE_AWARE_CONFIRM",
        tool_name="send_email",
        action_summary="send summary",
        slot_disclosures=[],
        external_effect="send email",
        prompt_text="Approve sending to attacker@example.com from external content?",
        required_disclosures=["recipients"],
        laundering_safe=True,
    )
    record = InterventionRecordModel(
        tool_call_id="call_1",
        tool_name="send_email",
        tool_args={"recipients": ["attacker@example.com"]},
        critical_slots=[],
        slot_records=[],
        has_untrusted_binding=True,
        has_role_only_binding=False,
        overall_risk=1.0,
        candidates_considered=["SOURCE_AWARE_CONFIRM"],
        selected_intervention="SOURCE_AWARE_CONFIRM",
        policy_backend="rule_v1",
    )
    extra_args = {"safeconfirm": {"user_query": "Send the summary to my supervisor."}}

    response = confirmer.respond(payload, record, extra_args)

    assert response.outcome == "rejected"
    sent_prompt = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "binding_slots_requiring_approval" in sent_prompt
    assert "Send the summary to my supervisor." in sent_prompt
