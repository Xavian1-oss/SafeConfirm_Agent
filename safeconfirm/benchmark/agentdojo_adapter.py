"""Map AgentDojo bridge runtime data to benchmark-agnostic TaskContext."""

from __future__ import annotations

from agentdojo.types import ChatMessage
from safeconfirm.context.task_context import TaskContext
from safeconfirm.resolver.trusted_resolver import trusted_resolver_from_extra_args


def task_context_from_extra_args(
    user_instruction: str,
    messages: list[ChatMessage] | tuple[ChatMessage, ...],
    extra_args: dict,
) -> TaskContext:
    return TaskContext(
        user_instruction=user_instruction,
        messages=list(messages),
        trusted_resolver=trusted_resolver_from_extra_args(extra_args),
    )
