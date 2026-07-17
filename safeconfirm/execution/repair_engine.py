from __future__ import annotations

import re
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
        extra_args: dict | None = None,
    ) -> RepairOutcome:
        entry = get_tool_entry(self.registry, tool_call.function)
        if entry is None or entry.repair is None:
            return RepairOutcome(success=False, reason="repair_not_configured")

        strategy = entry.repair.get("strategy")
        if strategy == "contact_lookup":
            return self._contact_lookup(tool_call, record, runtime, env, entry.repair, extra_args)
        if strategy == "trusted_account_lookup":
            return self._trusted_account_lookup(tool_call, record, env, entry.repair, extra_args)
        return RepairOutcome(success=False, reason=f"unsupported_strategy:{strategy}")

    def _contact_lookup(
        self,
        tool_call: FunctionCall,
        record: InterventionRecordModel,
        runtime: FunctionsRuntime,
        env: TaskEnvironment,
        repair_cfg: dict,
        extra_args: dict | None = None,
    ) -> RepairOutcome:
        role_slot = repair_cfg.get("role_slot")
        lookup_tool = repair_cfg.get("lookup_tool", "search_contacts_by_name")
        if not role_slot:
            return RepairOutcome(success=False, reason="missing_role_slot")

        role_label = _role_label_for_slot(record, role_slot)
        if role_label is None:
            return RepairOutcome(success=False, reason="missing_role_label")

        trusted_email: str | None = None
        if lookup_tool not in runtime.functions:
            return RepairOutcome(success=False, reason="lookup_tool_unavailable")
        trusted_email = _lookup_contact_email(
            runtime,
            env,
            lookup_tool,
            role_label,
            tool_call,
            role_slot,
        )
        if trusted_email is None:
            return RepairOutcome(success=False, reason="contact_not_found")

        new_args = dict(tool_call.args)
        new_args[role_slot] = _format_slot_value(new_args.get(role_slot), trusted_email)

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

    def _trusted_account_lookup(
        self,
        tool_call: FunctionCall,
        record: InterventionRecordModel,
        env: TaskEnvironment,
        repair_cfg: dict,
        extra_args: dict | None = None,
    ) -> RepairOutcome:
        role_slot = repair_cfg.get("role_slot", "recipient")
        role_label = _role_label_for_slot(record, role_slot)
        if role_label is None:
            role_label = _role_from_user_query(extra_args, repair_cfg.get("role_aliases", []))
        if role_label is None:
            return RepairOutcome(success=False, reason="missing_role_label")

        trusted_account = _trusted_account_from_filesystem(env, role_label)
        if trusted_account is None:
            return RepairOutcome(success=False, reason="trusted_account_not_found")

        new_args = dict(tool_call.args)
        new_args[role_slot] = _format_slot_value(new_args.get(role_slot), trusted_account)
        repaired_call = FunctionCall(
            function=tool_call.function,
            args=new_args,
            id=tool_call.id,
            placeholder_args=tool_call.placeholder_args,
        )
        return RepairOutcome(success=True, tool_call=repaired_call, trusted_emails={trusted_account})


def _role_label_for_slot(record: InterventionRecordModel, role_slot: str) -> str | None:
    for slot_record in record.slot_records:
        if slot_record.slot.name == role_slot and slot_record.slot.role_label:
            return slot_record.slot.role_label
    return None


def _format_slot_value(current_value: object, trusted_email: str) -> FunctionCallArgTypes:
    if isinstance(current_value, list):
        return [trusted_email]
    return trusted_email


def _lookup_contact_email(
    runtime: FunctionsRuntime,
    env: TaskEnvironment,
    lookup_tool: str,
    role_label: str,
    tool_call: FunctionCall,
    role_slot: str,
) -> str | None:
    contacts, error = runtime.run_function(env, lookup_tool, {"query": role_label})
    if error or not isinstance(contacts, list) or not contacts:
        return None

    excluded_values = _current_slot_values(tool_call, role_slot)
    for contact in contacts:
        if not isinstance(contact, EmailContact):
            continue
        email = str(contact.email).lower()
        if email in excluded_values:
            continue
        return email
    return None


def _current_slot_values(tool_call: FunctionCall, role_slot: str) -> set[str]:
    current = tool_call.args.get(role_slot)
    if current is None:
        return set()
    if isinstance(current, list):
        return {str(item).lower() for item in current}
    return {str(current).lower()}


def _role_from_user_query(extra_args: dict | None, role_aliases: list[str]) -> str | None:
    if not extra_args or not role_aliases:
        return None
    query = str(extra_args.get("safeconfirm", {}).get("user_query", "")).lower()
    for alias in role_aliases:
        if alias.lower() in query:
            return alias.lower()
    return None


def _trusted_account_from_filesystem(env: TaskEnvironment, role_label: str) -> str | None:
    filesystem = getattr(env, "filesystem", None)
    if filesystem is None:
        return None
    files = getattr(filesystem, "files", {})
    pattern = re.compile(
        rf"trusted\s+{re.escape(role_label)}\s+account:\s*(\S+)",
        re.IGNORECASE,
    )
    for content in files.values():
        match = pattern.search(str(content))
        if match:
            return match.group(1)
    return None
