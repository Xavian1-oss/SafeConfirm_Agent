from __future__ import annotations

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.errors import AbortAgentError
from agentdojo.base_tasks import BaseInjectionTask, BaseUserTask
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.task_suite import TaskSuite, functions_stack_trace_from_messages, model_output_from_messages

from safeconfirm_bridge.case_registry import case_by_user_task_id


def run_matched_pair_with_case_metadata(
    suite: TaskSuite,
    agent_pipeline: BasePipelineElement,
    user_task: BaseUserTask,
    injection_task: BaseInjectionTask,
    injections: dict[str, str],
    suite_name: str,
) -> tuple[bool, bool]:
    """Run one matched pair and pass benchmark_case metadata to SafeConfirm (for Oracle)."""
    environment = suite.load_and_inject_default_environment(injections)
    task_environment = user_task.init_environment(environment)
    pre_environment = task_environment.model_copy(deep=True)
    prompt = user_task.PROMPT

    case = case_by_user_task_id(user_task.ID, suite_name)
    extra_args: dict = {}
    if case is not None:
        extra_args["safeconfirm"] = {
            "benchmark_case": {
                "id": case.id,
                "trusted_binding": case.trusted_binding,
                "corrupted_slots": case.corrupted_slots,
            }
        }

    runtime = FunctionsRuntime(suite.tools)
    model_output = None
    messages = []
    for _ in range(5):
        try:
            _, _, task_environment, messages, _ = agent_pipeline.query(
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
    security = suite._check_task_result(
        injection_task,
        model_output or [],
        pre_environment,
        task_environment,
        functions_stack_trace,
    )
    return utility, security
