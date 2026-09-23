"""Benchmark-agnostic execution context for authorization analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentdojo.types import ChatMessage
from safeconfirm.resolver.trusted_resolver import MappingTrustedResolver, NullTrustedResolver


@dataclass
class TaskContext:
    """Unified input to SafeConfirm core (no benchmark case IDs or suite names)."""

    user_instruction: str
    messages: list[ChatMessage] = field(default_factory=list)
    resolver_attested_emails: set[str] = field(default_factory=set)
    trusted_resolver: MappingTrustedResolver | NullTrustedResolver = field(
        default_factory=NullTrustedResolver,
        repr=False,
    )


def task_context_from_parts(
    user_instruction: str,
    messages: list[ChatMessage] | tuple[ChatMessage, ...],
    *,
    resolver_attested_emails: set[str] | None = None,
) -> TaskContext:
    return TaskContext(
        user_instruction=user_instruction,
        messages=list(messages),
        resolver_attested_emails=resolver_attested_emails or set(),
    )
