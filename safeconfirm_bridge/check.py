from __future__ import annotations

from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from agentdojo.task_suite.task_suite import TaskSuite
from agentdojo.types import get_text_content_as_str
from safeconfirm_bridge.case_registry import POISON_VECTOR, case_by_user_task_id, matched_injection_task_id


def check_safeconfirm_suite(suite: TaskSuite, check_injectable: bool = True) -> bool:
    """Validate bridge suites with matched user/injection task pairs."""
    ok = True
    print(f"\033[94mChecking SafeConfirm bridge suite: `{suite.name}`\033[00m")

    for user_task in suite.user_tasks.values():
        case = case_by_user_task_id(user_task.ID, suite.name)
        injections = {POISON_VECTOR: case.setup.poison_content or ""} if case is not None else {}
        base_environment = suite.load_and_inject_default_environment(injections)
        environment = user_task.init_environment(base_environment.model_copy(deep=True))
        ground_truth_pipeline = GroundTruthPipeline(user_task)
        post_environment = environment.model_copy(deep=True)
        utility, _ = suite.run_task_with_pipeline(
            ground_truth_pipeline,
            user_task,
            injection_task=None,
            injections={},
            environment=post_environment,
        )
        if not utility:
            print(f"\033[91mUser task '{user_task.ID}' failed: ground truth does not solve the task\033[00m")
            ok = False
            continue

        if check_injectable:
            from agentdojo.functions_runtime import FunctionsRuntime

            case = case_by_user_task_id(user_task.ID, suite.name)
            runtime = FunctionsRuntime(suite.tools)
            _, _, _, responses, _ = ground_truth_pipeline.query(
                user_task.PROMPT, runtime, environment.model_copy(deep=True)
            )
            if case is not None and case.setup.poison_content:
                tool_outputs = [
                    get_text_content_as_str(response["content"])
                    for response in responses
                    if response["role"] == "tool" and response["content"] is not None
                ]
                if not any(case.setup.poison_content in output for output in tool_outputs):
                    print(f"\033[91mUser task '{user_task.ID}' failed: poison content not observable\033[00m")
                    ok = False
                    continue

        print(f"\033[92mUser task '{user_task.ID}' passed\033[00m")

    for user_task in suite.user_tasks.values():
        case = case_by_user_task_id(user_task.ID, suite.name)
        injections = {POISON_VECTOR: case.setup.poison_content or ""} if case is not None else {}
        base_environment = suite.load_and_inject_default_environment(injections)
        injection_task_id = matched_injection_task_id(user_task.ID)
        injection_task = suite.get_injection_task_by_id(injection_task_id)
        environment = user_task.init_environment(base_environment.model_copy(deep=True))
        ground_truth_pipeline = GroundTruthPipeline(injection_task)
        post_environment = environment.model_copy(deep=True)
        _, security = suite.run_task_with_pipeline(
            ground_truth_pipeline,
            user_task,
            injection_task=injection_task,
            injections={},
            environment=post_environment,
        )
        if case is not None and case.benign:
            if security:
                print(
                    f"\033[91mInjection task '{injection_task_id}' failed: benign case should not satisfy attack\033[00m"
                )
                ok = False
            else:
                print(f"\033[92mInjection task '{injection_task_id}' passed (benign)\033[00m")
            continue
        if not security:
            print(
                f"\033[91mInjection task '{injection_task_id}' failed: "
                "ground truth does not satisfy security check\033[00m"
            )
            ok = False
        else:
            print(f"\033[92mInjection task '{injection_task_id}' passed\033[00m")

    if ok:
        print(f"\033[92mSuite '{suite.name}' passed all SafeConfirm bridge checks\033[00m")
    return ok
