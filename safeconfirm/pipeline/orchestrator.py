from __future__ import annotations

from typing import Any

from agentdojo.functions_runtime import FunctionCall
from agentdojo.types import ChatMessage
from safeconfirm.analysis.source_analyzer import analyze_sources
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.extraction.slot_extractor import extract_critical_slots, get_tool_entry
from safeconfirm.learning.experience_store import ExperienceStore
from safeconfirm.policy.candidate_generator import generate_candidates
from safeconfirm.policy.retrieval_policy import RetrievalPolicy
from safeconfirm.policy.rule_policy import select_intervention
from safeconfirm.types.models import InterventionRecordModel, InterventionType, SafeConfirmLogModel


class SafeConfirmPipeline:
    def __init__(self, config: SafeConfirmConfig | None = None) -> None:
        self.config = config or SafeConfirmConfig.load()
        self.registry: ToolSlotRegistry = load_registry(self.config.registry_path)
        self.retrieval_policy: RetrievalPolicy | None = None
        if self.config.policy_backend == "retrieval":
            store = ExperienceStore(self.config.experiences_path)
            self.retrieval_policy = RetrievalPolicy(store, top_k=self.config.retrieval_top_k)

    def analyze_tool_call(
        self,
        tool_call: FunctionCall,
        query: str,
        messages: list[ChatMessage] | tuple[ChatMessage, ...],
        trusted_contact_emails: set[str] | None = None,
    ) -> InterventionRecordModel:
        if get_tool_entry(self.registry, tool_call.function) is None:
            return InterventionRecordModel(
                tool_call_id=tool_call.id,
                tool_name=tool_call.function,
                tool_args=dict(tool_call.args),
                critical_slots=[],
                slot_records=[],
                has_untrusted_binding=False,
                has_role_only_binding=False,
                overall_risk=0.0,
                candidates_considered=[InterventionType.ALLOW.value],
                selected_intervention=InterventionType.ALLOW.value,
                policy_backend=self.config.policy_backend,
                executed=True,
                executed_binding=dict(tool_call.args),
            )

        extraction = extract_critical_slots(tool_call.function, dict(tool_call.args), self.registry)
        analysis = analyze_sources(
            query,
            messages,
            extraction,
            self.registry,
            risk_threshold=self.config.risk_threshold_confirm,
            trusted_contact_emails=trusted_contact_emails,
        )
        candidates = generate_candidates(
            analysis,
            self.registry,
            tool_call.function,
            self.config.enable_repair,
        )
        selected = select_intervention(
            analysis,
            self.registry,
            tool_call.function,
            self.config.policy_backend,
            self.config.enable_repair,
            self.config.never_allow_on_untrusted,
            self.retrieval_policy,
        )

        return InterventionRecordModel(
            tool_call_id=tool_call.id,
            tool_name=tool_call.function,
            tool_args=dict(tool_call.args),
            critical_slots=extraction.critical_slots,
            slot_records=analysis.slot_records,
            has_untrusted_binding=analysis.has_untrusted_binding,
            has_role_only_binding=analysis.has_role_only_binding,
            overall_risk=analysis.overall_risk,
            candidates_considered=[c.value for c in candidates],
            selected_intervention=selected.value,
            policy_backend=self.config.policy_backend,
            executed=True,
            executed_binding=dict(tool_call.args),
        )


def get_or_init_safeconfirm_state(extra_args: dict[str, Any], config: SafeConfirmConfig) -> dict[str, Any]:
    if "safeconfirm" not in extra_args:
        extra_args["safeconfirm"] = {}
    state = extra_args["safeconfirm"]
    state.setdefault("mode", config.mode)
    state.setdefault("policy_backend", config.policy_backend)
    state.setdefault("intervention_log", [])
    return state


def build_log_payload(state: dict[str, Any]) -> SafeConfirmLogModel:
    records = state.get("intervention_log", [])
    if records and isinstance(records[0], InterventionRecordModel):
        record_models = records
    else:
        record_models = [InterventionRecordModel.model_validate(r) for r in records]
    return SafeConfirmLogModel(
        mode=state.get("mode", "log_only"),
        policy_backend=state.get("policy_backend", "rule_v1"),
        records=record_models,
    )
