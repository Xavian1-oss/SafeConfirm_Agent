from __future__ import annotations

from pathlib import Path

import yaml

from agentdojo.functions_runtime import FunctionCall
from agentdojo.types import (
    ChatAssistantMessage,
    ChatMessage,
    ChatToolResultMessage,
    ChatUserMessage,
    text_content_block_from_string,
)
from safeconfirm.analysis.source_analyzer import analyze_sources
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.extraction.slot_extractor import extract_critical_slots, get_tool_entry
from safeconfirm.learning.experience_store import ExperienceStore
from safeconfirm.learning.group_comparator import GroupComparator
from safeconfirm.policy.candidate_generator import generate_candidates
from safeconfirm.types.models import (
    ExperienceModel,
    ExperiencePatternModel,
    InterventionType,
    SourceAnalysisResultModel,
    TrainingCaseModel,
)
from safeconfirm.verifier.intervention_verifier import (
    InterventionVerifier,
    VerificationContext,
    dominant_untrusted_source,
)


class ExperienceDistiller:
    def __init__(self, config: SafeConfirmConfig | None = None) -> None:
        self.config = config or SafeConfirmConfig.load()
        self.registry: ToolSlotRegistry = load_registry(self.config.registry_path)
        self.verifier = InterventionVerifier()
        self.comparator = GroupComparator()

    def load_training_cases(self, path: Path | None = None) -> list[TrainingCaseModel]:
        cases_path = path or self.config.training_cases_path
        with cases_path.open() as handle:
            raw = yaml.safe_load(handle)
        return [TrainingCaseModel.model_validate(item) for item in raw.get("cases", [])]

    def distill_from_case(self, case: TrainingCaseModel) -> ExperienceModel:
        messages = _messages_from_case(case)
        tool_call = FunctionCall(function=case.tool_name, args=case.tool_args, id=f"{case.id}_call")
        analysis = self._analyze(case.query, messages, tool_call)
        candidates = generate_candidates(
            analysis,
            self.registry,
            case.tool_name,
            self.config.enable_repair,
        )
        context = VerificationContext(
            safe_interventions=set(case.safe_interventions),
            unsafe_interventions=set(case.unsafe_interventions),
            laundering_interventions=set(case.laundering_interventions),
            repair_available=self._repair_available(case.tool_name),
        )
        scores = {
            candidate: self.verifier.score(analysis, candidate, self.registry, case.tool_name, context)
            for candidate in candidates
        }
        comparison = self.comparator.compare(scores)
        pattern = pattern_from_analysis(analysis, case.tool_name, self.registry)
        rationale = _build_rationale(case, comparison.winner, analysis)
        return ExperienceModel(
            id=f"exp_{case.id}",
            pattern=pattern,
            intervention_choice=comparison.winner.value,
            rationale=rationale,
            score_delta=comparison.deltas.get(comparison.winner.value),
            source_case_id=case.id,
        )

    def distill_all(self, cases: list[TrainingCaseModel]) -> list[ExperienceModel]:
        return [self.distill_from_case(case) for case in cases]

    def _analyze(self, query: str, messages: list[ChatMessage], tool_call: FunctionCall) -> SourceAnalysisResultModel:
        extraction = extract_critical_slots(tool_call.function, dict(tool_call.args), self.registry)
        return analyze_sources(
            query,
            messages,
            extraction,
            self.registry,
            risk_threshold=self.config.risk_threshold_confirm,
        )

    def _repair_available(self, tool_name: str) -> bool:
        if not self.config.enable_repair:
            return False
        entry = get_tool_entry(self.registry, tool_name)
        return entry is not None and entry.repair is not None


def pattern_from_analysis(
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


def _messages_from_case(case: TrainingCaseModel) -> list[ChatMessage]:
    messages: list[ChatMessage] = [ChatUserMessage(role="user", content=[text_content_block_from_string(case.query)])]
    if case.observation_content:
        messages.append(
            ChatToolResultMessage(
                role="tool",
                tool_call=FunctionCall(function=case.observation_tool, args={"url": "https://evil.example"}),
                content=[text_content_block_from_string(case.observation_content)],
                tool_call_id=f"{case.id}_obs",
                error=None,
            )
        )
    messages.append(
        ChatAssistantMessage(
            role="assistant",
            content=None,
            tool_calls=[FunctionCall(function=case.tool_name, args=case.tool_args, id=f"{case.id}_call")],
        )
    )
    return messages


def _build_rationale(case: TrainingCaseModel, winner: InterventionType, analysis: SourceAnalysisResultModel) -> str:
    if analysis.has_role_only_binding and winner == InterventionType.REPAIR:
        return (
            "User authorized a recipient role, but the concrete email came from untrusted content; "
            "repair from trusted contacts preserves utility without confirmation laundering."
        )
    if winner == InterventionType.SOURCE_AWARE_CONFIRM:
        return (
            "Critical parameters come from untrusted observations; disclose exact values and sources "
            "instead of using vague confirmation."
        )
    if winner == InterventionType.BLOCK:
        return f"High-risk {case.tool_name} with authorization gap should fail closed when safety dominates utility."
    if winner == InterventionType.ALLOW:
        return "No authorization gap remained; allow the tool call."
    return f"Selected {winner.value} for case {case.id} based on group-relative verifier scores."


def distill_to_store(
    config: SafeConfirmConfig | None = None,
    output_path: Path | None = None,
    training_cases_path: Path | None = None,
) -> list[ExperienceModel]:
    distiller = ExperienceDistiller(config)
    cases = distiller.load_training_cases(training_cases_path)
    experiences = distiller.distill_all(cases)
    store = ExperienceStore(output_path or distiller.config.experiences_path)
    store.save(experiences)
    return experiences
