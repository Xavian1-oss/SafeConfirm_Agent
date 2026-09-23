"""Benchmark-agnostic execution context for authorization analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentdojo.types import ChatMessage
from safeconfirm.resolver.trusted_resolver import MappingTrustedResolver, NullTrustedResolver


class TaskContext(BaseModel):
    """Unified input to SafeConfirm core (no benchmark case IDs or suite names)."""

    user_instruction: str
    messages: list[ChatMessage] = Field(default_factory=list)
    resolver_attested_emails: set[str] = Field(
        default_factory=set,
        description="Emails bound by a trusted resolver this turn (e.g. post-repair), not benchmark YAML.",
    )
    trusted_resolver: MappingTrustedResolver | NullTrustedResolver = Field(
        default_factory=NullTrustedResolver,
        exclude=True,
        repr=False,
    )

    model_config = {"arbitrary_types_allowed": True}


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
