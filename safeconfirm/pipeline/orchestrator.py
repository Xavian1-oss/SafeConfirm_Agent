from __future__ import annotations

from typing import Any

from agentdojo.functions_runtime import FunctionCall
from agentdojo.types import ChatMessage
from safeconfirm.authorization.analyzer import AuthorizationAnalyzer, UnknownToolError
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.context.repair_preflight import RepairPreflight
from safeconfirm.context.task_context import TaskContext, task_context_from_parts
from safeconfirm.execution.repair_engine import RepairEngine
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.policy.rule_policy import select_intervention_for_state
from safeconfirm.types.models import InterventionRecordModel, SafeConfirmLogModel, SourceAnalysisResultModel


class SafeConfirmPipeline:
    def __init__(self, config: SafeConfirmConfig | None = None) -> None:
        self.config = config or SafeConfirmConfig.load()
        self.registry: ToolSlotRegistry = load_registry(self.config.registry_path)
        self.repair_engine = RepairEngine(self.config, self.registry)
        self.analyzer = AuthorizationAnalyzer(
            self.registry,
            self.config,
            repair_engine=self.repair_engine,
        )

    def analyze_tool_call(
        self,
        tool_call: FunctionCall,
        query: str | TaskContext,
        messages: list[ChatMessage] | tuple[ChatMessage, ...] | None = None,
        resolver_attested_emails: set[str] | None = None,
        repair_preflight: RepairPreflight | None = None,
    ) -> InterventionRecordModel:
        """Analyze one tool call. Production runs use SafeConfirmIntervention (supplies repair_preflight)."""
        task_context = _resolve_task_context(query, messages, resolver_attested_emails)
        try:
            analysis, auth_state = self.analyzer.analyze_tool_call(
                tool_call,
                task_context,
                repair_preflight,
            )
        except UnknownToolError as exc:
            return exc.record
        return self._build_intervention_record(tool_call, analysis, auth_state)

    def _build_intervention_record(
        self,
        tool_call: FunctionCall,
        analysis: SourceAnalysisResultModel,
        auth_state: AuthorizationState,
    ) -> InterventionRecordModel:
        selected = select_intervention_for_state(auth_state, self.config.policy_backend)
        critical_slots = [record.slot for record in analysis.slot_records]
        return InterventionRecordModel(
            tool_call_id=tool_call.id,
            tool_name=tool_call.function,
            tool_args=dict(tool_call.args),
            critical_slots=critical_slots,
            slot_records=analysis.slot_records,
            has_untrusted_binding=analysis.has_untrusted_binding,
            has_role_only_binding=analysis.has_role_only_binding,
            overall_risk=analysis.overall_risk,
            selected_intervention=selected.value,
            policy_backend=self.config.policy_backend,
            executed=True,
            executed_binding=dict(tool_call.args),
        )


def _resolve_task_context(
    query: str | TaskContext,
    messages: list[ChatMessage] | tuple[ChatMessage, ...] | None,
    resolver_attested_emails: set[str] | None,
) -> TaskContext:
    if isinstance(query, TaskContext):
        return query
    return task_context_from_parts(
        query,
        messages or [],
        resolver_attested_emails=resolver_attested_emails,
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
