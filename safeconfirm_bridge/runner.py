from __future__ import annotations

from pathlib import Path

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.errors import AbortAgentError
from agentdojo.base_tasks import BaseInjectionTask, BaseUserTask
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.task_suite import TaskSuite, functions_stack_trace_from_messages, model_output_from_messages
from safeconfirm.pipeline.orchestrator import build_log_payload
from safeconfirm.types.models import SafeConfirmLogModel
from safeconfirm_bridge.case_registry import case_by_user_task_id
from safeconfirm_bridge.e2e_metrics import E2ERunResultModel, save_e2e_run, target_tool_called


def _build_extra_args(user_query: str, confirmer_model: str | None = None) -> dict:
    extra_args: dict = {"safeconfirm": {"user_query": user_query}}
    if confirmer_model is not None:
        extra_args["safeconfirm"]["confirmer_model"] = confirmer_model
    return extra_args


def run_matched_pair(
    suite: TaskSuite,
    agent_pipeline: BasePipelineElement,
    user_task: BaseUserTask,
    injection_task: BaseInjectionTask,
    injections: dict[str, str],
    suite_name: str,
    *,
    policy_backend: str | None = None,
    confirmer: str = "llm_user",
    confirmer_model: str | None = None,
    save_path: str | Path | None = None,
) -> E2ERunResultModel:
    environment = suite.load_and_inject_default_environment(injections)
    task_environment = user_task.init_environment(environment)
    pre_environment = task_environment.model_copy(deep=True)
    prompt = user_task.PROMPT

    case = case_by_user_task_id(user_task.ID, suite_name)
    extra_args = _build_extra_args(prompt, confirmer_model)

    runtime = FunctionsRuntime(suite.tools)
    model_output = None
    messages = []
    for _ in range(8):
        try:
            _, _, task_environment, messages, extra_args = agent_pipeline.query(
                prompt,
                runtime,
                task_environment,
                messages=messages,
                extra_args=extra_args,
            )
        except AbortAgentError as error:
            task_environment = error.task_environment
            messages = error.messages

        try:
            model_output = model_output_from_messages(messages)
        except ValueError:
            model_output = None
        if model_output is not None:
            break

    functions_stack_trace = functions_stack_trace_from_messages(messages)
    utility = suite._check_task_result(
        user_task,
        model_output or [],
        pre_environment,
        task_environment,
        functions_stack_trace,
    )
    attack_succeeded = suite._check_task_result(
        injection_task,
        model_output or [],
        pre_environment,
        task_environment,
        functions_stack_trace,
    )

    safeconfirm_payload = extra_args.get("safeconfirm", {})
    safeconfirm_log: SafeConfirmLogModel | None = None
    if safeconfirm_payload.get("intervention_log"):
        safeconfirm_log = build_log_payload(safeconfirm_payload)

    resolved_policy = policy_backend
    if resolved_policy is None and safeconfirm_log is not None:
        resolved_policy = safeconfirm_log.policy_backend

    result = E2ERunResultModel(
        case_id=case.id if case is not None else user_task.ID,
        user_task_id=user_task.ID,
        injection_task_id=injection_task.ID,
        suite=suite_name,
        category=case.category if case is not None else "unknown",
        benign=case.benign if case is not None else False,
        utility=utility,
        attack_succeeded=attack_succeeded,
        policy_backend=resolved_policy,
        confirmer=confirmer,
        confirmer_model=confirmer_model,
        target_tool_called=target_tool_called(
            list(functions_stack_trace),
            case.tool_name if case is not None else "",
        ),
        safeconfirm=safeconfirm_log,
    )
    if save_path is not None:
        save_e2e_run(save_path, result)
    return result
