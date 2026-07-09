from __future__ import annotations

from collections import Counter

from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.learning.experience_store import ExperienceStore
from safeconfirm.policy.rule_policy import rule_v1_select
from safeconfirm.types.models import (
    ExperiencePatternModel,
    InterventionType,
    SourceAnalysisResultModel,
)
from safeconfirm.verifier.intervention_verifier import dominant_untrusted_source


class RetrievalPolicy:
    def __init__(self, store: ExperienceStore, top_k: int = 5) -> None:
        self.store = store
        self.top_k = top_k
        self.experiences = store.load()

    def reload(self) -> None:
        self.experiences = self.store.load()

    def select_intervention(
        self,
        analysis: SourceAnalysisResultModel,
        registry: ToolSlotRegistry,
        tool_name: str,
        enable_repair: bool,
        never_allow_on_untrusted: bool,
    ) -> InterventionType:
        if not self.experiences:
            return rule_v1_select(analysis, registry, tool_name, enable_repair, never_allow_on_untrusted)

        pattern = _pattern_from_analysis(analysis, tool_name, registry)
        ranked = sorted(
            self.experiences,
            key=lambda experience: _pattern_similarity(pattern, experience.pattern),
            reverse=True,
        )
        top_matches = [
            experience for experience in ranked[: self.top_k] if _pattern_similarity(pattern, experience.pattern) > 0
        ]
        if not top_matches:
            return rule_v1_select(analysis, registry, tool_name, enable_repair, never_allow_on_untrusted)

        votes = Counter(experience.intervention_choice for experience in top_matches)
        winner_value, _ = votes.most_common(1)[0]
        winner = InterventionType(winner_value)
        return _apply_hard_constraints(winner, analysis, registry, tool_name, enable_repair)


def _pattern_from_analysis(
    analysis: SourceAnalysisResultModel,
    tool_name: str,
    registry: ToolSlotRegistry,
) -> ExperiencePatternModel:
    entry = get_tool_entry(registry, tool_name)
    gap_slots = [record.slot.name for record in analysis.slot_records if record.authorization_gap]
    return ExperiencePatternModel(
        tool_name=tool_name,
        user_role_binding=analysis.has_role_only_binding,
        untrusted_source=dominant_untrusted_source(analysis),
        critical_slots=gap_slots,
        action_category=entry.action_category if entry else None,
        action_type_authorized=analysis.action_type_authorized,
    )


def _pattern_similarity(left: ExperiencePatternModel, right: ExperiencePatternModel) -> float:
    score = 0.0
    if left.tool_name == right.tool_name:
        score += 3.0
    if left.user_role_binding == right.user_role_binding:
        score += 2.0
    if left.untrusted_source and left.untrusted_source == right.untrusted_source:
        score += 2.0
    if left.action_category and left.action_category == right.action_category:
        score += 1.5
    if left.action_type_authorized == right.action_type_authorized:
        score += 1.0
    overlap = set(left.critical_slots) & set(right.critical_slots)
    score += len(overlap)
    return score


def _apply_hard_constraints(
    winner: InterventionType,
    analysis: SourceAnalysisResultModel,
    registry: ToolSlotRegistry,
    tool_name: str,
    enable_repair: bool,
) -> InterventionType:
    has_gap = any(record.authorization_gap for record in analysis.slot_records)
    entry = get_tool_entry(registry, tool_name)
    repair_available = enable_repair and entry is not None and entry.repair is not None

    if not has_gap and winner != InterventionType.ALLOW:
        return InterventionType.ALLOW

    if has_gap and winner == InterventionType.ALLOW and analysis.has_untrusted_binding:
        return InterventionType.SOURCE_AWARE_CONFIRM
    if has_gap and winner == InterventionType.VAGUE_CONFIRM:
        return InterventionType.SOURCE_AWARE_CONFIRM
    if winner == InterventionType.REPAIR and (not repair_available or not analysis.has_role_only_binding):
        return rule_v1_select(analysis, registry, tool_name, enable_repair, True)
    return winner
