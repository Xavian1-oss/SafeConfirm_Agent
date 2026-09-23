"""Pluggable provenance attribution (benchmark-specific implementations)."""

from __future__ import annotations

from typing import Protocol

from agentdojo.types import ChatMessage
from safeconfirm.analysis.trust_index import TrustIndex, build_trust_index
from safeconfirm.types.models import (
    CriticalSlotModel,
    SourceEvidenceModel,
    SourceTrust,
)


class ProvenanceProvider(Protocol):
    """Attributes binding values to trust classes from a trajectory."""

    def build_trust_index(
        self,
        messages: list[ChatMessage] | tuple[ChatMessage, ...],
        role_aliases: list[str],
    ) -> TrustIndex: ...

    def attribute_slot(
        self,
        slot: CriticalSlotModel,
        trust_index: TrustIndex,
        role_aliases: list[str],
        *,
        action_type_ok: bool,
        risk_threshold: float,
        resolver_attested_emails: set[str] | None = None,
        content_delegated: bool = False,
    ) -> tuple[SourceTrust, list[SourceEvidenceModel], bool, float]: ...


class AgentDojoProvenanceProvider:
    """Default provider: AgentDojo chat trajectory + post-repair resolver attestation."""

    def build_trust_index(
        self,
        messages: list[ChatMessage] | tuple[ChatMessage, ...],
        role_aliases: list[str],
    ) -> TrustIndex:
        return build_trust_index(messages, role_aliases)

    def attribute_slot(
        self,
        slot: CriticalSlotModel,
        trust_index: TrustIndex,
        role_aliases: list[str],
        *,
        action_type_ok: bool,
        risk_threshold: float,
        resolver_attested_emails: set[str] | None = None,
        content_delegated: bool = False,
    ) -> tuple[SourceTrust, list[SourceEvidenceModel], bool, float]:
        from safeconfirm.provenance.agentdojo_slot import attribute_binding_slot

        return attribute_binding_slot(
            slot,
            trust_index,
            role_aliases,
            action_type_ok=action_type_ok,
            risk_threshold=risk_threshold,
            resolver_attested_emails=resolver_attested_emails,
            content_delegated=content_delegated,
        )


DEFAULT_PROVENANCE_PROVIDER = AgentDojoProvenanceProvider()
