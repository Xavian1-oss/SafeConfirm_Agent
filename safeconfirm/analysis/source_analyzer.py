from __future__ import annotations

from typing import Any

from agentdojo.types import ChatMessage

from safeconfirm.analysis.trust_index import TrustIndex, build_trust_index, collect_role_aliases
from safeconfirm.extraction.registry_loader import ToolRegistryEntry, ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.types.models import (
    CriticalSlotModel,
    SlotExtractionResultModel,
    SlotSourceRecordModel,
    SourceAnalysisResultModel,
    SourceEvidenceModel,
    SourceTrust,
)

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "exfiltration": ["send", "email", "forward", "share", "post", "message"],
    "deletion": ["delete", "remove", "drop"],
    "financial": ["pay", "transfer", "send money", "transaction", "schedule", "money"],
    "permission_change": ["share", "permission", "grant", "access"],
    "booking": ["reserve", "book", "schedule", "flight", "hotel"],
    "unknown": [],
}

SOURCE_MULTIPLIERS: dict[SourceTrust, float] = {
    SourceTrust.USER_EXPLICIT: 0.0,
    SourceTrust.TRUSTED_CONTACT: 0.1,
    SourceTrust.TRUSTED_ENV: 0.1,
    SourceTrust.USER_ROLE: 0.5,
    SourceTrust.UNKNOWN: 0.8,
    SourceTrust.AGENT_INFERRED: 0.9,
    SourceTrust.UNTRUSTED_OBSERVATION: 1.0,
}

RISK_GAP_THRESHOLD = 0.5


def analyze_sources(
    query: str,
    messages: list[ChatMessage] | tuple[ChatMessage, ...],
    extraction: SlotExtractionResultModel,
    registry: ToolSlotRegistry,
    risk_threshold: float = RISK_GAP_THRESHOLD,
    trusted_contact_emails: set[str] | None = None,
) -> SourceAnalysisResultModel:
    entry = get_tool_entry(registry, extraction.tool_name)
    role_aliases = collect_role_aliases(entry.critical_slots) if entry else []
    trust_index = build_trust_index(messages, role_aliases)
    action_type_ok = action_type_authorized(extraction.tool_name, query, registry)

    slot_records: list[SlotSourceRecordModel] = []
    for slot in extraction.critical_slots:
        spec = _find_slot_spec(entry, slot.name)
        role_aliases_for_slot = spec.role_aliases if spec else []
        record = _analyze_slot(
            slot,
            trust_index,
            role_aliases_for_slot,
            action_type_ok,
            risk_threshold,
            trusted_contact_emails,
        )
        slot_records.append(record)

    overall_risk = max((r.risk_score for r in slot_records), default=0.0)
    has_untrusted = any(
        r.source in {SourceTrust.UNTRUSTED_OBSERVATION, SourceTrust.AGENT_INFERRED, SourceTrust.UNKNOWN}
        and r.authorization_gap
        for r in slot_records
    )
    has_role_only = any(r.authorization_gap and r.slot.role_label is not None for r in slot_records)

    return SourceAnalysisResultModel(
        slot_records=slot_records,
        overall_risk=overall_risk,
        has_untrusted_binding=has_untrusted,
        has_role_only_binding=has_role_only,
        action_type_authorized=action_type_ok,
    )


def action_type_authorized(tool_name: str, query: str, registry: ToolSlotRegistry) -> bool:
    entry = registry.get(tool_name)
    if entry is None:
        return False
    keywords = CATEGORY_KEYWORDS.get(entry.action_category, [])
    if not keywords:
        return True
    lowered = query.lower()
    return any(keyword in lowered for keyword in keywords)


def _find_slot_spec(entry: ToolRegistryEntry | None, slot_name: str):
    if entry is None:
        return None
    for spec in entry.critical_slots:
        if spec.name == slot_name:
            return spec
    return None


def _analyze_slot(
    slot: CriticalSlotModel,
    trust_index: TrustIndex,
    role_aliases: list[str],
    action_type_ok: bool,
    risk_threshold: float,
    trusted_contact_emails: set[str] | None = None,
) -> SlotSourceRecordModel:
    values_to_check = _expand_values(slot)
    evidence: list[SourceEvidenceModel] = []
    source = SourceTrust.UNKNOWN

    if role_aliases:
        matched_roles = [alias for alias in role_aliases if alias in trust_index.user_roles]
        if matched_roles:
            slot.role_label = matched_roles[0]

    for value in values_to_check:
        if value and value in trust_index.user_text:
            source = SourceTrust.USER_EXPLICIT
            evidence.append(
                SourceEvidenceModel(
                    message_index=-1,
                    message_role="user",
                    snippet=value,
                    match_type="exact",
                    confidence=1.0,
                )
            )
            break

    if source != SourceTrust.USER_EXPLICIT and trusted_contact_emails:
        if any(value and value in trusted_contact_emails for value in values_to_check):
            source = SourceTrust.TRUSTED_CONTACT
            evidence.append(
                SourceEvidenceModel(
                    message_index=-1,
                    message_role="trusted_contact",
                    snippet=next(v for v in values_to_check if v in trusted_contact_emails),
                    match_type="contact_lookup",
                    confidence=1.0,
                )
            )

    if source not in {SourceTrust.USER_EXPLICIT, SourceTrust.TRUSTED_CONTACT}:
        for obs in trust_index.observations:
            if any(value and value in obs.text.lower() for value in values_to_check):
                source = SourceTrust.UNTRUSTED_OBSERVATION
                evidence.append(
                    SourceEvidenceModel(
                        message_index=obs.message_index,
                        message_role="tool",
                        snippet=obs.text[:120],
                        match_type="substring",
                        confidence=0.95,
                        observation_tool=obs.observation_tool,
                    )
                )
                break

    if source == SourceTrust.UNKNOWN and slot.role_label is not None:
        source = SourceTrust.USER_ROLE
        evidence.append(
            SourceEvidenceModel(
                message_index=-1,
                message_role="user",
                snippet=slot.role_label,
                match_type="role",
                confidence=0.7,
            )
        )

    if source == SourceTrust.UNKNOWN and values_to_check:
        source = SourceTrust.AGENT_INFERRED

    gap = (
        action_type_ok
        and source not in {SourceTrust.USER_EXPLICIT, SourceTrust.TRUSTED_CONTACT, SourceTrust.TRUSTED_ENV}
        and slot.risk_weight >= risk_threshold
    )
    multiplier = SOURCE_MULTIPLIERS[source]
    risk_score = slot.risk_weight * multiplier * (1.0 if gap else 0.0)

    return SlotSourceRecordModel(
        slot=slot,
        source=source,
        evidence=evidence,
        authorization_gap=gap,
        risk_score=risk_score,
    )


def _expand_values(slot: CriticalSlotModel) -> list[str]:
    if slot.slot_type == "email_list":
        if isinstance(slot.value, list):
            return [str(v).strip().lower() for v in slot.value]
        return [str(slot.value).strip().lower()]
    normalized = slot.value_normalized
    return [normalized] if normalized else []
