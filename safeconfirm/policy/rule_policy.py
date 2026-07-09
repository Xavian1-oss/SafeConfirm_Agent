from __future__ import annotations

from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.types.models import InterventionType, SourceAnalysisResultModel


def select_intervention(
    analysis: SourceAnalysisResultModel,
    registry: ToolSlotRegistry,
    tool_name: str,
    policy_backend: str,
    enable_repair: bool,
    never_allow_on_untrusted: bool,
    retrieval_policy: object | None = None,
) -> InterventionType:
    if policy_backend == "baseline_allow":
        return InterventionType.ALLOW
    if policy_backend == "baseline_block":
        if any(r.authorization_gap for r in analysis.slot_records):
            return InterventionType.BLOCK
        return InterventionType.ALLOW
    if policy_backend == "baseline_vague":
        if any(r.authorization_gap for r in analysis.slot_records):
            return InterventionType.VAGUE_CONFIRM
        return InterventionType.ALLOW
    if policy_backend == "retrieval":
        if retrieval_policy is None:
            return rule_v1_select(analysis, registry, tool_name, enable_repair, never_allow_on_untrusted)
        return retrieval_policy.select_intervention(
            analysis,
            registry,
            tool_name,
            enable_repair,
            never_allow_on_untrusted,
        )

    return rule_v1_select(analysis, registry, tool_name, enable_repair, never_allow_on_untrusted)


def rule_v1_select(
    analysis: SourceAnalysisResultModel,
    registry: ToolSlotRegistry,
    tool_name: str,
    enable_repair: bool,
    never_allow_on_untrusted: bool,
) -> InterventionType:
    if not analysis.action_type_authorized:
        if analysis.overall_risk >= 0.7:
            return InterventionType.BLOCK
        return InterventionType.REPLAN

    if not analysis.has_untrusted_binding and analysis.overall_risk < 0.3:
        return InterventionType.ALLOW

    entry = get_tool_entry(registry, tool_name)
    repair_available = enable_repair and entry is not None and entry.repair is not None
    if analysis.has_role_only_binding and repair_available:
        return InterventionType.REPAIR

    if analysis.has_untrusted_binding:
        if never_allow_on_untrusted:
            return InterventionType.SOURCE_AWARE_CONFIRM
        return InterventionType.SOURCE_AWARE_CONFIRM

    return InterventionType.ALLOW
