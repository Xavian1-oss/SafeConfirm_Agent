from __future__ import annotations

from agentdojo.types import ChatAssistantMessage, ChatMessage


def as_assistant(message: ChatMessage) -> ChatAssistantMessage:
    if message["role"] != "assistant":
        raise TypeError(f"Expected assistant message, got {message['role']!r}")
    return message
