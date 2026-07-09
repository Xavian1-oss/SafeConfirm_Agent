from __future__ import annotations

from dataclasses import dataclass

from agentdojo.types import ChatMessage, get_text_content_as_str


@dataclass
class ObservationSpan:
    message_index: int
    text: str
    observation_tool: str | None


@dataclass
class TrustIndex:
    user_text: str
    user_roles: set[str]
    observations: list[ObservationSpan]


def build_trust_index(messages: list[ChatMessage] | tuple[ChatMessage, ...], role_aliases: list[str]) -> TrustIndex:
    user_parts: list[str] = []
    observations: list[ObservationSpan] = []
    user_roles: set[str] = set()

    for idx, message in enumerate(messages):
        role = message["role"]
        if role == "user":
            content = message["content"]
            if content is None:
                continue
            text = get_text_content_as_str(content).lower()
            user_parts.append(text)
            for alias in role_aliases:
                if alias.lower() in text:
                    user_roles.add(alias.lower())
        elif role == "tool":
            content = message["content"]
            if content is None:
                continue
            text = get_text_content_as_str(content)
            tool_name = None
            if "tool_call" in message and message["tool_call"] is not None:
                tool_name = message["tool_call"].function
            observations.append(ObservationSpan(message_index=idx, text=text, observation_tool=tool_name))

    return TrustIndex(
        user_text="\n".join(user_parts),
        user_roles=user_roles,
        observations=observations,
    )


def collect_role_aliases(registry_slots: list) -> list[str]:
    aliases: set[str] = set()
    for slot in registry_slots:
        for alias in slot.role_aliases:
            aliases.add(alias.lower())
    return sorted(aliases)
