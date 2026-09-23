from __future__ import annotations

from agentdojo.types import ChatMessage
from safeconfirm.analysis.trust_index import collect_role_aliases
from safeconfirm.authorization.action_auth import DEFAULT_ACTION_AUTH_PROVIDER, ActionAuthorizationProvider
from safeconfirm.extraction.registry_loader import ToolRegistryEntry, ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.provenance.provider import DEFAULT_PROVENANCE_PROVIDER, ProvenanceProvider
from safeconfirm.types.models import (
    SlotExtractionResultModel,
    SlotSourceRecordModel,
    SourceAnalysisResultModel,
    SourceTrust,
)

RISK_GAP_THRESHOLD = 0.5

CONTENT_DELEGATION_PHRASES = (
    "forward",
    "send its contents",
    "send the contents",
    "relay",
    "summarize and send",
    "summary and send",
)


def binding_slot_records(records: list[SlotSourceRecordModel]) -> list[SlotSourceRecordModel]:
    return [record for record in records if record.slot.slot_class == "binding"]


def has_binding_authorization_gap(records: list[SlotSourceRecordModel]) -> bool:
    return any(record.authorization_gap for record in binding_slot_records(records))


def analyze_sources(
    query: str,
    messages: list[ChatMessage] | tuple[ChatMessage, ...],
    extraction: SlotExtractionResultModel,
    registry: ToolSlotRegistry,
    risk_threshold: float = RISK_GAP_THRESHOLD,
    resolver_attested_emails: set[str] | None = None,
    *,
    provenance_provider: ProvenanceProvider | None = None,
    action_auth_provider: ActionAuthorizationProvider | None = None,
) -> SourceAnalysisResultModel:
    provider = provenance_provider or DEFAULT_PROVENANCE_PROVIDER
    auth_provider = action_auth_provider or DEFAULT_ACTION_AUTH_PROVIDER
    entry = get_tool_entry(registry, extraction.tool_name)
    role_aliases = collect_role_aliases(entry.critical_slots) if entry else []
    trust_index = provider.build_trust_index(messages, role_aliases)
    action_type_ok = auth_provider.action_authorized(extraction.tool_name, query, registry)
    content_delegated = user_delegated_content(query)

    slot_records: list[SlotSourceRecordModel] = []
    for slot in extraction.critical_slots:
        spec = _find_slot_spec(entry, slot.name)
        role_aliases_for_slot = spec.role_aliases if spec else []
        source, evidence, gap, risk_score = provider.attribute_slot(
            slot,
            trust_index,
            role_aliases_for_slot,
            action_type_ok=action_type_ok,
            risk_threshold=risk_threshold,
            resolver_attested_emails=resolver_attested_emails,
            content_delegated=content_delegated,
        )
        slot_records.append(
            SlotSourceRecordModel(
                slot=slot,
                source=source,
                evidence=evidence,
                authorization_gap=gap,
                risk_score=risk_score,
            )
        )

    binding_records = binding_slot_records(slot_records)
    overall_risk = max((record.risk_score for record in binding_records), default=0.0)
    has_untrusted = any(
        record.source in {SourceTrust.UNTRUSTED_OBSERVATION, SourceTrust.AGENT_INFERRED, SourceTrust.UNKNOWN}
        and record.authorization_gap
        for record in binding_records
    )
    has_role_only = any(record.authorization_gap and record.slot.role_label is not None for record in binding_records)

    return SourceAnalysisResultModel(
        slot_records=slot_records,
        overall_risk=overall_risk,
        has_untrusted_binding=has_untrusted,
        has_role_only_binding=has_role_only,
        action_type_authorized=action_type_ok,
    )


def user_delegated_content(query: str) -> bool:
    lowered = query.lower()
    if any(phrase in lowered for phrase in CONTENT_DELEGATION_PHRASES):
        return True
    return "read" in lowered and "send" in lowered


def _find_slot_spec(entry: ToolRegistryEntry | None, slot_name: str):
    if entry is None:
        return None
    for spec in entry.critical_slots:
        if spec.name == slot_name:
            return spec
    return None
