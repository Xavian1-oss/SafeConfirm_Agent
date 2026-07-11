from __future__ import annotations

import datetime

import pytest

from agentdojo.default_suites.v1.tools.calendar_client import Calendar
from agentdojo.default_suites.v1.tools.cloud_drive_client import CloudDrive
from agentdojo.default_suites.v1.tools.email_client import Inbox
from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.evaluation.run_case import TargetedBenchmarkEnvironment
from safeconfirm_bridge.case_registry import DEFAULT_E2E_CASES_PATH, cases_for_suite
from safeconfirm_bridge.environment import prepare_environment


def _empty_workspace_environment() -> TargetedBenchmarkEnvironment:
    account_email = "agent.user@company.com"
    return TargetedBenchmarkEnvironment(
        inbox=Inbox(account_email=account_email, initial_emails=[], contact_list=[]),
        calendar=Calendar(
            current_day=datetime.date(2024, 5, 14),
            account_email=account_email,
            initial_events=[],
        ),
        cloud_drive=CloudDrive(account_email=account_email, initial_files=[]),
    )


def test_e2e_cases_load_and_validate() -> None:
    cases = load_benchmark_cases(DEFAULT_E2E_CASES_PATH)
    assert len(cases) == 16
    assert all(case.e2e is not None for case in cases)
    assert all(case.setup.injection_vector == "safeconfirm_poison" for case in cases)


def test_e2e_workspace_cases_have_required_observation() -> None:
    cases = cases_for_suite("safeconfirm_workspace")
    for case in cases:
        assert case.e2e is not None
        assert case.e2e.required_observation is not None


@pytest.mark.parametrize(
    ("case_id", "expected_subject"),
    [
        ("ws_email_supervisor_e2e", "Weekly report"),
        ("ws_calendar_invite_e2e", "Calendar invite"),
        ("ws_thread_summary_e2e", "Thread summary"),
    ],
)
def test_e2e_environment_includes_source_email(case_id: str, expected_subject: str) -> None:
    case = next(item for item in cases_for_suite("safeconfirm_workspace") if item.id == case_id)
    environment = _empty_workspace_environment()
    prepared = prepare_environment(environment, case)
    subjects = [email.subject for email in prepared.inbox.emails.values()]
    assert expected_subject in subjects
    assert "Contact reference" in subjects


def test_e2e_corruption_cases_use_trusted_contacts_only() -> None:
    case = next(item for item in cases_for_suite("safeconfirm_workspace") if item.id == "ws_email_supervisor_e2e")
    prepared = prepare_environment(_empty_workspace_environment(), case)
    emails = {contact.email.lower() for contact in prepared.inbox.contact_list}
    assert "supervisor@university.edu" in emails
    assert "attacker@example.com" not in emails


def test_e2e_delete_case_has_trusted_and_decoy_files() -> None:
    case = next(item for item in cases_for_suite("safeconfirm_workspace") if item.id == "ws_delete_backup_e2e")
    environment = _empty_workspace_environment()
    prepared = prepare_environment(environment, case)
    assert "file_backup_1" in prepared.cloud_drive.files
    assert "attacker_controlled_id" in prepared.cloud_drive.files
    assert case.trusted_binding["file_id"] == "file_backup_1"
