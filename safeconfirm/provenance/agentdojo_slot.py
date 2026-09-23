"""AgentDojo-specific slot provenance attribution."""

from __future__ import annotations

from safeconfirm.analysis.trust_index import TrustIndex
from safeconfirm.types.models import CriticalSlotModel, SourceEvidenceModel, SourceTrust

SOURCE_MULTIPLIERS: dict[SourceTrust, float] = {
    SourceTrust.USER_EXPLICIT: 0.0,
    SourceTrust.TRUSTED_CONTACT: 0.1,
    SourceTrust.TRUSTED_ENV: 0.1,
    SourceTrust.USER_ROLE: 0.5,
    SourceTrust.UNKNOWN: 0.8,
    SourceTrust.AGENT_INFERRED: 0.9,
    SourceTrust.UNTRUSTED_OBSERVATION: 1.0,
}


def attribute_binding_slot(
    slot: CriticalSlotModel,
    trust_index: TrustIndex,
    role_aliases: list[str],
    *,
    action_type_ok: bool,
    risk_threshold: float,
    resolver_attested_emails: set[str] | None = None,
    content_delegated: bool = False,
) -> tuple[SourceTrust, list[SourceEvidenceModel], bool, float]:
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

    if source != SourceTrust.USER_EXPLICIT and resolver_attested_emails:
        if any(value and value in resolver_attested_emails for value in values_to_check):
            source = SourceTrust.TRUSTED_CONTACT
            evidence.append(
                SourceEvidenceModel(
                    message_index=-1,
                    message_role="trusted_resolver",
                    snippet=next(v for v in values_to_check if v in resolver_attested_emails),
                    match_type="resolver_attestation",
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
        slot.slot_class == "binding"
        and action_type_ok
        and source not in {SourceTrust.USER_EXPLICIT, SourceTrust.TRUSTED_CONTACT, SourceTrust.TRUSTED_ENV}
        and slot.risk_weight >= risk_threshold
    )
    if slot.slot_class == "content" and content_delegated and action_type_ok:
        gap = False

    multiplier = SOURCE_MULTIPLIERS[source]
    risk_score = slot.risk_weight * multiplier * (1.0 if gap else 0.0)
    return source, evidence, gap, risk_score


def _expand_values(slot: CriticalSlotModel) -> list[str]:
    if slot.slot_type == "email_list":
        if isinstance(slot.value, list):
            return [str(v).strip().lower() for v in slot.value]
        return [str(slot.value).strip().lower()]
    normalized = slot.value_normalized
    return [normalized] if normalized else []
