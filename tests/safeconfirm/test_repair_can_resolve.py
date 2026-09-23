import datetime

from agentdojo.default_suites.v1.tools.calendar_client import Calendar
from agentdojo.default_suites.v1.tools.cloud_drive_client import CloudDrive
from agentdojo.default_suites.v1.tools.email_client import EmailContact, Inbox, search_contacts_by_name
from agentdojo.functions_runtime import FunctionCall, FunctionsRuntime, TaskEnvironment
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.repair_engine import RepairEngine
from safeconfirm.resolver.trusted_resolver import MappingTrustedResolver
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionRecordModel,
    SlotSourceRecordModel,
    SourceTrust,
)


class _Env(TaskEnvironment):
    inbox: Inbox
    calendar: Calendar
    cloud_drive: CloudDrive


def _record_with_supervisor_role() -> InterventionRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value=["attacker@example.com"],
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
        slot_class="binding",
        role_label="supervisor",
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=SourceTrust.USER_ROLE,
        evidence=[],
        authorization_gap=True,
        risk_score=0.5,
    )
    return InterventionRecordModel(
        tool_call_id="c1",
        tool_name="send_email",
        tool_args={"recipients": ["attacker@example.com"], "subject": "s", "body": "b"},
        critical_slots=[slot],
        slot_records=[slot_record],
        has_untrusted_binding=False,
        has_role_only_binding=True,
        overall_risk=0.5,
        selected_intervention="REPAIR",
        policy_backend="rule_v1",
    )


def test_can_resolve_via_mock_resolver():
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "s", "body": "b"},
        id="c1",
    )
    runtime = FunctionsRuntime([])
    env = _Env(
        inbox=Inbox(account_email="u@example.com", initial_emails=[], contact_list=[]),
        calendar=Calendar(current_day=datetime.date(2024, 1, 1), account_email="u@example.com", initial_events=[]),
        cloud_drive=CloudDrive(account_email="u@example.com", initial_files=[]),
    )
    resolver = MappingTrustedResolver({"supervisor": "supervisor@university.edu"})
    assert engine.can_resolve(
        tool_call,
        _record_with_supervisor_role(),
        runtime,
        env,
        user_instruction="Send to my supervisor.",
        trusted_resolver=resolver,
    )


def test_can_resolve_via_search_contacts_when_tool_registered():
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "s", "body": "b"},
        id="c1",
    )
    runtime = FunctionsRuntime([])
    runtime.register_function(search_contacts_by_name)
    env = _Env(
        inbox=Inbox(
            account_email="u@example.com",
            initial_emails=[],
            contact_list=[EmailContact(name="Supervisor", email="supervisor@university.edu")],
        ),
        calendar=Calendar(current_day=datetime.date(2024, 1, 1), account_email="u@example.com", initial_events=[]),
        cloud_drive=CloudDrive(account_email="u@example.com", initial_files=[]),
    )
    assert engine.can_resolve(
        tool_call,
        _record_with_supervisor_role(),
        runtime,
        env,
        user_instruction="Send to my supervisor.",
    )


def test_cannot_resolve_without_resolver_or_lookup_tool():
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "s", "body": "b"},
        id="c1",
    )
    runtime = FunctionsRuntime([])
    env = _Env(
        inbox=Inbox(account_email="u@example.com", initial_emails=[], contact_list=[]),
        calendar=Calendar(current_day=datetime.date(2024, 1, 1), account_email="u@example.com", initial_events=[]),
        cloud_drive=CloudDrive(account_email="u@example.com", initial_files=[]),
    )
    assert not engine.can_resolve(
        tool_call,
        _record_with_supervisor_role(),
        runtime,
        env,
        user_instruction="Send to my supervisor.",
    )
