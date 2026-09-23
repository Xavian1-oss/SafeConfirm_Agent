"""Authorization analyzer: provenance + compact state (no intervention choice)."""

from __future__ import annotations

import random

from agentdojo.functions_runtime import FunctionCall
from safeconfirm.analysis.provenance_stress import apply_provenance_label_flip, flip_rng_seed
from safeconfirm.analysis.source_analyzer import analyze_sources
from safeconfirm.authorization.action_auth import DEFAULT_ACTION_AUTH_PROVIDER, ActionAuthorizationProvider
from safeconfirm.authorization.build_state import authorization_state_from_analysis
from safeconfirm.authorization.repair_feasibility import compute_repair_resolvable
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.context.repair_preflight import RepairPreflight
from safeconfirm.context.task_context import TaskContext
from safeconfirm.execution.repair_engine import RepairEngine
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.extraction.slot_extractor import extract_critical_slots, get_tool_entry
from safeconfirm.pipeline.unknown_tool import build_unknown_tool_record
from safeconfirm.provenance.provider import DEFAULT_PROVENANCE_PROVIDER, ProvenanceProvider
from safeconfirm.types.models import InterventionRecordModel, SourceAnalysisResultModel


class AuthorizationAnalyzer:
    """Produces provenance-enriched analysis and AuthorizationState for policy core."""

    def __init__(
        self,
        registry: ToolSlotRegistry,
        config: SafeConfirmConfig,
        provenance_provider: ProvenanceProvider | None = None,
        action_auth_provider: ActionAuthorizationProvider | None = None,
        repair_engine: RepairEngine | None = None,
    ) -> None:
        self.registry = registry
        self.config = config
        self.provenance_provider = provenance_provider or DEFAULT_PROVENANCE_PROVIDER
        self.action_auth_provider = action_auth_provider or DEFAULT_ACTION_AUTH_PROVIDER
        self.repair_engine = repair_engine or RepairEngine(config, registry)

    @classmethod
    def from_config(cls, config: SafeConfirmConfig | None = None) -> AuthorizationAnalyzer:
        config = config or SafeConfirmConfig.load()
        registry = load_registry(config.registry_path)
        return cls(registry, config, repair_engine=RepairEngine(config, registry))

    def analyze_tool_call(
        self,
        tool_call: FunctionCall,
        context: TaskContext,
        repair_preflight: RepairPreflight | None = None,
    ) -> tuple[SourceAnalysisResultModel, AuthorizationState]:
        if get_tool_entry(self.registry, tool_call.function) is None:
            raise UnknownToolError(
                build_unknown_tool_record(
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.function,
                    tool_args=dict(tool_call.args),
                    policy_backend=self.config.policy_backend,
                    unknown_tool_policy=self.config.unknown_tool_policy,
                )
            )

        extraction = extract_critical_slots(tool_call.function, dict(tool_call.args), self.registry)
        analysis = analyze_sources(
            context.user_instruction,
            context.messages,
            extraction,
            self.registry,
            risk_threshold=self.config.risk_threshold_confirm,
            resolver_attested_emails=context.resolver_attested_emails or None,
            provenance_provider=self.provenance_provider,
            action_auth_provider=self.action_auth_provider,
        )
        if self.config.provenance_flip_rate > 0.0:
            seed = flip_rng_seed(self.config.provenance_flip_seed, tool_call.id)
            apply_provenance_label_flip(
                analysis,
                self.config.provenance_flip_rate,
                random.Random(seed),
            )
        repair_resolvable = compute_repair_resolvable(
            analysis,
            tool_call,
            enable_repair=self.config.enable_repair,
            registry=self.registry,
            repair_engine=self.repair_engine,
            context=context,
            preflight=repair_preflight,
        )
        state = authorization_state_from_analysis(
            analysis,
            tool_name=tool_call.function,
            registry=self.registry,
            repair_resolvable=repair_resolvable,
        )
        return analysis, state


class UnknownToolError(Exception):
    def __init__(self, record: InterventionRecordModel) -> None:
        self.record = record
        super().__init__(f"Unknown tool: {record.tool_name}")
