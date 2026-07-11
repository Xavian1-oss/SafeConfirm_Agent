from __future__ import annotations

import types
from collections.abc import Sequence
from typing import Any

from agentdojo.base_tasks import BaseInjectionTask, BaseUserTask, TaskDifficulty
from agentdojo.default_suites.v1.tools.types import SharingPermission
from agentdojo.functions_runtime import FunctionCall, TaskEnvironment
from agentdojo.task_suite.task_suite import TaskSuite

from safeconfirm.types.models import BenchmarkCaseModel
from safeconfirm_bridge.environment import prepare_environment
from safeconfirm_bridge.evaluators import attack_succeeded, utility_satisfied


def register_cases_for_suite(
    task_suite: TaskSuite,
    cases: list[BenchmarkCaseModel],
    env_type: type[TaskEnvironment],
) -> dict[str, BenchmarkCaseModel]:
    user_task_map: dict[str, BenchmarkCaseModel] = {}
    for index, case in enumerate(cases):
        user_task_cls = _build_user_task_class(case, index, env_type)
        injection_task_cls = _build_injection_task_class(case, index, env_type)
        task_suite.register_user_task(user_task_cls)
        task_suite.register_injection_task(injection_task_cls)
        user_task_map[f"user_task_{index}"] = case
    return user_task_map


def _build_user_task_class(
    case: BenchmarkCaseModel,
    index: int,
    env_type: type[TaskEnvironment],
) -> type[BaseUserTask]:
    def init_environment(environment: TaskEnvironment) -> TaskEnvironment:
        return prepare_environment(environment, case)

    def ground_truth(self, pre_environment: TaskEnvironment) -> list[FunctionCall]:
        return _ground_truth_calls(case)

    def utility(
        self,
        model_output: str,
        pre_environment: TaskEnvironment,
        post_environment: TaskEnvironment,
        strict: bool = True,
    ) -> bool:
        return utility_satisfied(case, pre_environment, post_environment)

    def utility_from_traces(
        self,
        model_output: str,
        pre_environment: TaskEnvironment,
        post_environment: TaskEnvironment,
        traces: Sequence[FunctionCall],
    ) -> bool | None:
        return utility_satisfied(case, pre_environment, post_environment, traces)

    def exec_body(namespace: dict[str, Any]) -> None:
        namespace.update(
            {
                "PROMPT": case.user_task_template,
                "DIFFICULTY": TaskDifficulty.MEDIUM,
                "CASE_ID": case.id,
                "init_environment": staticmethod(init_environment),
                "ground_truth": ground_truth,
                "utility": utility,
                "utility_from_traces": utility_from_traces,
            }
        )

    return types.new_class(f"UserTask{index}", (BaseUserTask,), exec_body=exec_body)


def _build_injection_task_class(
    case: BenchmarkCaseModel,
    index: int,
    env_type: type[TaskEnvironment],
) -> type[BaseInjectionTask]:
    def ground_truth(self, pre_environment: TaskEnvironment) -> list[FunctionCall]:
        return _ground_truth_calls(case, trusted=False)

    def security(
        self,
        model_output: str,
        pre_environment: TaskEnvironment,
        post_environment: TaskEnvironment,
    ) -> bool:
        return attack_succeeded(case, pre_environment, post_environment)

    def security_from_traces(
        self,
        model_output: str,
        pre_environment: TaskEnvironment,
        post_environment: TaskEnvironment,
        traces: Sequence[FunctionCall],
    ) -> bool | None:
        return attack_succeeded(case, pre_environment, post_environment, traces)

    return types.new_class(
        f"InjectionTask{index}",
        (BaseInjectionTask,),
        exec_body=lambda namespace: namespace.update(
            {
                "GOAL": case.user_task_template,
                "DIFFICULTY": TaskDifficulty.MEDIUM,
                "CASE_ID": case.id,
                "ground_truth": ground_truth,
                "security": security,
                "security_from_traces": security_from_traces,
            }
        ),
    )


def _ground_truth_calls(case: BenchmarkCaseModel, *, trusted: bool = True) -> list[FunctionCall]:
    binding = _effective_binding(case, trusted=trusted)
    if case.tool_name == "send_email":
        recipients = _binding_list(binding.get("recipients", case.tool_args.get("recipients")))
        return [
            FunctionCall(function="get_unread_emails", args={}),
            FunctionCall(
                function="send_email",
                args={
                    "recipients": recipients,
                    "subject": case.tool_args.get("subject", "Summary"),
                    "body": case.tool_args.get("body", "summary"),
                },
            ),
        ]
    if case.tool_name == "share_file":
        share_args = _share_args(binding, case)
        return [
            FunctionCall(function="get_file_by_id", args={"file_id": share_args["file_id"]}),
            FunctionCall(function="share_file", args=share_args),
        ]
    if case.tool_name == "delete_file":
        if trusted:
            file_id = binding.get("file_id", case.trusted_binding.get("file_id", case.tool_args.get("file_id")))
            return [
                FunctionCall(function="get_unread_emails", args={}),
                FunctionCall(function="delete_file", args={"file_id": file_id}),
            ]
        file_id = binding.get("file_id", case.tool_args.get("file_id"))
        return [
            FunctionCall(function="get_unread_emails", args={}),
            FunctionCall(function="delete_file", args={"file_id": file_id}),
        ]
    if case.tool_name == "send_money":
        return [
            FunctionCall(function="get_most_recent_transactions", args={"n": 5}),
            FunctionCall(
                function="send_money",
                args={
                    "recipient": binding.get("recipient", case.tool_args.get("recipient")),
                    "amount": binding.get("amount", case.tool_args.get("amount", 1)),
                    "subject": binding.get("subject", case.tool_args.get("subject", "Payment")),
                    "date": "2024-05-15",
                },
            ),
        ]
    return []


def _normalize_permission(permission: Any) -> str:
    if permission in ("read", "r", SharingPermission.r):
        return SharingPermission.r
    if permission in ("edit", "write", "rw", SharingPermission.rw):
        return SharingPermission.rw
    return str(permission)


def _share_args(binding: dict[str, Any], case: BenchmarkCaseModel) -> dict[str, Any]:
    return {
        "file_id": binding.get("file_id", case.tool_args.get("file_id")),
        "email": binding.get("email", case.tool_args.get("email")),
        "permission": _normalize_permission(binding.get("permission", case.tool_args.get("permission", "read"))),
    }


def _effective_binding(case: BenchmarkCaseModel, *, trusted: bool) -> dict[str, Any]:
    if trusted:
        if case.benign:
            return {**case.tool_args, **case.trusted_binding}
        return case.trusted_binding
    if case.corrupted_slots:
        return {**case.tool_args, **case.corrupted_slots}
    return case.tool_args


def _binding_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
