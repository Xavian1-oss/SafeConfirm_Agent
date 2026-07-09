from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CriticalSlotSpec:
    name: str
    slot_type: str
    risk_weight: float
    role_aliases: list[str] = field(default_factory=list)
    required: bool = True


@dataclass
class ToolRegistryEntry:
    risk_tier: str
    action_category: str
    critical_slots: list[CriticalSlotSpec]
    repair: dict[str, Any] | None = None


@dataclass
class ToolSlotRegistry:
    version: str
    tools: dict[str, ToolRegistryEntry]

    def get(self, tool_name: str) -> ToolRegistryEntry | None:
        return self.tools.get(tool_name)


def load_registry(registry_path: Path) -> ToolSlotRegistry:
    with registry_path.open() as f:
        raw = yaml.safe_load(f)
    tools: dict[str, ToolRegistryEntry] = {}
    for _suite_name, suite_data in raw.get("suites", {}).items():
        for tool_name, tool_data in suite_data.get("tools", {}).items():
            slots = [
                CriticalSlotSpec(
                    name=slot["name"],
                    slot_type=slot["slot_type"],
                    risk_weight=float(slot["risk_weight"]),
                    role_aliases=list(slot.get("role_aliases", [])),
                    required=bool(slot.get("required", True)),
                )
                for slot in tool_data.get("critical_slots", [])
            ]
            tools[tool_name] = ToolRegistryEntry(
                risk_tier=tool_data.get("risk_tier", "HIGH"),
                action_category=tool_data.get("action_category", "unknown"),
                critical_slots=slots,
                repair=tool_data.get("repair"),
            )
    return ToolSlotRegistry(version=str(raw.get("version", "0.0.0")), tools=tools)
