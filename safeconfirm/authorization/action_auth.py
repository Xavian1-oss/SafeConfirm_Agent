"""Pluggable action-type authorization (user intent vs tool category)."""

from __future__ import annotations

from typing import Protocol

from safeconfirm.extraction.registry_loader import ToolSlotRegistry

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "exfiltration": ["send", "email", "forward", "share", "post", "message"],
    "deletion": ["delete", "remove", "drop"],
    "financial": ["pay", "transfer", "send money", "transaction", "schedule", "money"],
    "permission_change": ["share", "permission", "grant", "access"],
    "file_write": ["save", "create", "export", "archive", "file"],
    "scheduling": ["schedule", "calendar", "event", "invite", "meeting"],
    "booking": ["reserve", "book", "schedule", "flight", "hotel"],
    "unknown": [],
}


class ActionAuthorizationProvider(Protocol):
    def action_authorized(
        self,
        tool_name: str,
        user_instruction: str,
        registry: ToolSlotRegistry,
    ) -> bool: ...


class KeywordActionAuthorizationProvider:
    """Default: registry action_category keywords must appear in the user instruction."""

    def action_authorized(
        self,
        tool_name: str,
        user_instruction: str,
        registry: ToolSlotRegistry,
    ) -> bool:
        entry = registry.get(tool_name)
        if entry is None:
            return False
        keywords = CATEGORY_KEYWORDS.get(entry.action_category, [])
        if not keywords:
            return True
        lowered = user_instruction.lower()
        return any(keyword in lowered for keyword in keywords)


DEFAULT_ACTION_AUTH_PROVIDER = KeywordActionAuthorizationProvider()


def action_type_authorized(tool_name: str, query: str, registry: ToolSlotRegistry) -> bool:
    return DEFAULT_ACTION_AUTH_PROVIDER.action_authorized(tool_name, query, registry)
