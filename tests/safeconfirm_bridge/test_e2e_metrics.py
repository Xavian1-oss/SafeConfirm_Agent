from __future__ import annotations

from safeconfirm.types.models import SafeConfirmLogModel
from safeconfirm_bridge.e2e_metrics import E2ERunResultModel, compute_e2e_metrics


def test_compute_e2e_metrics_reports_core_and_l1_fields():
    runs = [
        E2ERunResultModel(
            case_id="corruption",
            user_task_id="user_task_0",
            injection_task_id="injection_task_0",
            suite="safeconfirm_workspace",
            category="email",
            benign=False,
            utility=True,
            attack_succeeded=False,
            target_tool_called=True,
            safeconfirm=SafeConfirmLogModel(mode="active", policy_backend="rule_v1", records=[]),
        ),
        E2ERunResultModel(
            case_id="benign",
            user_task_id="user_task_10",
            injection_task_id="injection_task_10",
            suite="safeconfirm_workspace",
            category="email",
            benign=True,
            utility=False,
            attack_succeeded=False,
            target_tool_called=False,
            safeconfirm=SafeConfirmLogModel(mode="active", policy_backend="rule_v1", records=[]),
        ),
    ]

    metrics = compute_e2e_metrics(runs)
    assert metrics.total_cases == 2
    assert metrics.corruption_cases == 1
    assert metrics.benign_cases == 1
    assert metrics.tsr == 0.5
    assert metrics.asr == 0.0
    assert metrics.corruption_tsr == 1.0
    assert metrics.benign_tsr == 0.0
    assert metrics.defense_success_rate == 1.0
    assert metrics.action_rate == 0.5
    assert metrics.stall_rate == 0.0
    assert metrics.fbr == 1.0
    assert metrics.confirmer == "llm_user"


def test_compute_e2e_metrics_handles_missing_safeconfirm_log():
    runs = [
        E2ERunResultModel(
            case_id="p0",
            user_task_id="user_task_0",
            injection_task_id="injection_task_0",
            suite="safeconfirm_workspace",
            category="email",
            benign=False,
            utility=False,
            attack_succeeded=True,
            target_tool_called=True,
            safeconfirm=None,
        )
    ]

    metrics = compute_e2e_metrics(runs)
    assert metrics.total_cases == 1
    assert metrics.asr == 1.0
    assert metrics.uar == 0.0
