from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionsRuntime
from agentdojo.logging import Logger
from agentdojo.types import ChatAssistantMessage, ChatMessage, MessageContentBlock, text_content_block_from_string
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.execution.intervention_executor import InterventionExecutor
from safeconfirm.pipeline.orchestrator import (
    SafeConfirmPipeline,
    build_log_payload,
    get_or_init_safeconfirm_state,
)


class SafeConfirmIntervention(BasePipelineElement):
    name = "safeconfirm"

    def __init__(
        self,
        mode: str | None = "log_only",
        policy_backend: str | None = None,
        config_path: str | None = None,
    ) -> None:
        config = SafeConfirmConfig.load(config_path)
        if mode is not None:
            config.mode = mode
        if policy_backend is not None:
            config.policy_backend = policy_backend
        self.config = config
        self.pipeline = SafeConfirmPipeline(config)
        self.executor = InterventionExecutor(config)

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        if len(messages) == 0:
            return query, runtime, env, messages, extra_args
        last_message = messages[-1]
        if last_message["role"] != "assistant":
            return query, runtime, env, messages, extra_args
        tool_calls = last_message.get("tool_calls") or []
        if len(tool_calls) == 0:
            return query, runtime, env, messages, extra_args

        state = get_or_init_safeconfirm_state(extra_args, self.config)
        records = [self.pipeline.analyze_tool_call(tool_call, query, list(messages)) for tool_call in tool_calls]

        if self.config.mode == "log_only":
            state["intervention_log"].extend(records)
            self._sync_trace_log(extra_args)
            return query, runtime, env, messages, extra_args

        outcome = self.executor.apply(
            query,
            runtime,
            env,
            list(messages),
            list(tool_calls),
            records,
            extra_args,
            self.pipeline,
        )
        state["intervention_log"].extend(outcome.records)

        updated_messages = list(outcome.messages)
        original_assistant_index = len(messages) - 1
        original_assistant = updated_messages[original_assistant_index]
        tool_calls = outcome.tool_calls or []
        content = original_assistant.get("content")
        if not tool_calls and content is None:
            content = [text_content_block_from_string("")]
        updated_messages[original_assistant_index] = ChatAssistantMessage(
            role="assistant",
            content=cast(list[MessageContentBlock] | None, content),
            tool_calls=tool_calls,
        )

        self._sync_trace_log(extra_args)
        return query, runtime, env, updated_messages, extra_args

    def _sync_trace_log(self, extra_args: dict) -> None:
        state = extra_args.get("safeconfirm", {})
        payload = build_log_payload(state)
        logger = Logger.get()
        logger.set_contextarg("safeconfirm", payload.model_dump(mode="json"))
