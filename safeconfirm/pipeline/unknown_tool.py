from __future__ import annotations

from typing import Any

from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionRecordModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceTrust,
)


def _arg_slots(tool_name: str, tool_args: dict[str, Any]) -> list[SlotSourceRecordModel]:
    records: list[SlotSourceRecordModel] = []
    for name, value in tool_args.items():
        normalized = str(value).lower() if not isinstance(value, list) else ",".join(str(v).lower() for v in value)
        slot = CriticalSlotModel(
            name=name,
            value=value,
            value_normalized=normalized,
            slot_type="unknown_registry",
            risk_weight=1.0,
            slot_class="binding",
        )
        records.append(
            SlotSourceRecordModel(
                slot=slot,
                source=SourceTrust.UNKNOWN,
                evidence=[],
                authorization_gap=True,
                risk_score=1.0,
            )
        )
    if not records:
        slot = CriticalSlotModel(
            name="_tool_call",
            value=tool_name,
            value_normalized=tool_name.lower(),
            slot_type="unknown_registry",
            risk_weight=1.0,
            slot_class="binding",
        )
        records.append(
            SlotSourceRecordModel(
                slot=slot,
                source=SourceTrust.UNKNOWN,
                evidence=[],
                authorization_gap=True,
                risk_score=1.0,
            )
        )
    return records


def build_unknown_tool_record(
    *,
    tool_call_id: str | None,
    tool_name: str,
    tool_args: dict[str, Any],
    policy_backend: str,
    unknown_tool_policy: str,
) -> InterventionRecordModel:
    policy = unknown_tool_policy.strip().lower()
    slot_records = _arg_slots(tool_name, tool_args)
    critical_slots = [slot_record.slot for slot_record in slot_records]

    if policy == "block":
        return InterventionRecordModel(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_args=dict(tool_args),
            critical_slots=critical_slots,
            slot_records=slot_records,
            has_untrusted_binding=True,
            has_role_only_binding=False,
            overall_risk=1.0,
            selected_intervention=InterventionType.BLOCK.value,
            policy_backend=policy_backend,
            executed=False,
            executed_binding=None,
        )

    # conservative_confirm (default): defer execution until confirmation resolves registry gap
    return InterventionRecordModel(
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        tool_args=dict(tool_args),
        critical_slots=critical_slots,
        slot_records=slot_records,
        has_untrusted_binding=True,
        has_role_only_binding=False,
        overall_risk=1.0,
        selected_intervention=InterventionType.SOURCE_AWARE_CONFIRM.value,
        policy_backend=policy_backend,
        executed=False,
        executed_binding=None,
    )
