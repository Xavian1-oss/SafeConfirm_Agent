from __future__ import annotations

from typing import Any

from safeconfirm.extraction.registry_loader import ToolRegistryEntry, ToolSlotRegistry
from safeconfirm.types.models import CriticalSlotModel, SlotExtractionResultModel


def extract_critical_slots(
    tool_name: str,
    tool_args: dict[str, Any],
    registry: ToolSlotRegistry,
) -> SlotExtractionResultModel:
    entry = registry.get(tool_name)
    if entry is None:
        return _fallback_extraction(tool_name, tool_args)

    critical_slots: list[CriticalSlotModel] = []
    seen_names: set[str] = set()
    for spec in entry.critical_slots:
        if spec.name not in tool_args:
            continue
        value = tool_args[spec.name]
        critical_slots.append(
            CriticalSlotModel(
                name=spec.name,
                value=value,
                value_normalized=_normalize_for_compare(value, spec.slot_type),
                slot_type=spec.slot_type,
                risk_weight=spec.risk_weight,
                role_label=None,
                is_required=spec.required,
            )
        )
        seen_names.add(spec.name)

    non_critical = [name for name in tool_args if name not in seen_names]
    return SlotExtractionResultModel(
        tool_name=tool_name,
        critical_slots=critical_slots,
        non_critical_slots=non_critical,
        extraction_method="registry",
        warnings=[],
    )


def _fallback_extraction(tool_name: str, tool_args: dict[str, Any]) -> SlotExtractionResultModel:
    critical_slots: list[CriticalSlotModel] = []
    for name, value in tool_args.items():
        if not isinstance(value, (str, int, float, list, dict)):
            continue
        critical_slots.append(
            CriticalSlotModel(
                name=name,
                value=value,
                value_normalized=_normalize_for_compare(value, "text"),
                slot_type="text",
                risk_weight=0.7,
                is_required=True,
            )
        )
    return SlotExtractionResultModel(
        tool_name=tool_name,
        critical_slots=critical_slots,
        non_critical_slots=[],
        extraction_method="fallback",
        warnings=[f"Tool {tool_name} not in registry; using fallback extraction"],
    )


def get_tool_entry(registry: ToolSlotRegistry, tool_name: str) -> ToolRegistryEntry | None:
    return registry.get(tool_name)


def _normalize_for_compare(value: Any, slot_type: str) -> str:
    if slot_type in {"email", "account", "file_id", "permission", "path", "text"}:
        return str(value).strip().lower()
    if slot_type == "email_list":
        if not isinstance(value, list):
            value = [value]
        return ",".join(sorted(str(v).strip().lower() for v in value))
    if slot_type == "amount":
        return str(value).strip()
    if slot_type == "attachment_list":
        return str(value)
    return str(value)
