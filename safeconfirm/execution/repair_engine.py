from __future__ import annotations

from dataclasses import dataclass

from agentdojo.default_suites.v1.tools.email_client import EmailContact
from agentdojo.functions_runtime import FunctionCall, FunctionCallArgTypes, FunctionsRuntime, TaskEnvironment
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.types.models import InterventionRecordModel


@dataclass
class RepairOutcome:
    success: bool
    tool_call: FunctionCall | None = None
    trusted_emails: set[str] | None = None
    reason: str | None = None


class RepairEngine:
    def __init__(self, config: SafeConfirmConfig, registry: ToolSlotRegistry | None = None) -> None:
        self.config = config
        self.registry = registry or load_registry(config.registry_path)

    def attempt_repair(
        self,
        tool_call: FunctionCall,
        record: InterventionRecordModel,
        runtime: FunctionsRuntime,
        env: TaskEnvironment,
    ) -> RepairOutcome:
        entry = get_tool_entry(self.registry, tool_call.function)
        if entry is None or entry.repair is None:
            return RepairOutcome(success=False, reason="repair_not_configured")

        strategy = entry.repair.get("strategy")
        if strategy == "contact_lookup":
            return self._contact_lookup(tool_call, record, runtime, env, entry.repair)
        return RepairOutcome(success=False, reason=f"unsupported_strategy:{strategy}")

    def _contact_lookup(
        self,
        tool_call: FunctionCall,
        record: InterventionRecordModel,
        runtime: FunctionsRuntime,
        env: TaskEnvironment,
        repair_cfg: dict,
    ) -> RepairOutcome:
        role_slot = repair_cfg.get("role_slot")
        lookup_tool = repair_cfg.get("lookup_tool", "search_contacts_by_name")
        if not role_slot:
            return RepairOutcome(success=False, reason="missing_role_slot")

        role_label = _role_label_for_slot(record, role_slot)
        if role_label is None:
            return RepairOutcome(success=False, reason="missing_role_label")

        if lookup_tool not in runtime.functions:
            return RepairOutcome(success=False, reason="lookup_tool_unavailable")

        contacts, error = runtime.run_function(env, lookup_tool, {"query": role_label})
        if error or not isinstance(contacts, list) or not contacts:
            return RepairOutcome(success=False, reason=error or "contact_not_found")

        contact = contacts[0]
        if not isinstance(contact, EmailContact):
            return RepairOutcome(success=False, reason="contact_not_found")
        trusted_email = str(contact.email).lower()
        new_args = dict(tool_call.args)
        new_args[role_slot] = _format_slot_value(new_args.get(role_slot), trusted_email)

        permission_cap = repair_cfg.get("permission_cap")
        if permission_cap and "permission" in new_args:
            new_args["permission"] = permission_cap

        repaired_call = FunctionCall(
            function=tool_call.function,
            args=new_args,
            id=tool_call.id,
            placeholder_args=tool_call.placeholder_args,
        )
        return RepairOutcome(
            success=True,
            tool_call=repaired_call,
            trusted_emails={trusted_email},
        )


def _role_label_for_slot(record: InterventionRecordModel, role_slot: str) -> str | None:
    for slot_record in record.slot_records:
        if slot_record.slot.name == role_slot and slot_record.slot.role_label:
            return slot_record.slot.role_label
    return None


def _format_slot_value(current_value: object, trusted_email: str) -> FunctionCallArgTypes:
    if isinstance(current_value, list):
        return [trusted_email]
    return trusted_email
