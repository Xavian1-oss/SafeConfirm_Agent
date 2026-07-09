from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceTrust(str, Enum):
    USER_EXPLICIT = "user_explicit"
    USER_ROLE = "user_role"
    TRUSTED_CONTACT = "trusted_contact"
    TRUSTED_ENV = "trusted_env"
    UNTRUSTED_OBSERVATION = "untrusted_observation"
    AGENT_INFERRED = "agent_inferred"
    UNKNOWN = "unknown"


class InterventionType(str, Enum):
    ALLOW = "ALLOW"
    VAGUE_CONFIRM = "VAGUE_CONFIRM"
    SOURCE_AWARE_CONFIRM = "SOURCE_AWARE_CONFIRM"
    BLOCK = "BLOCK"
    REPAIR = "REPAIR"
    REPLAN = "REPLAN"


class CriticalSlotModel(BaseModel):
    name: str
    value: Any
    value_normalized: str
    slot_type: str
    risk_weight: float
    role_label: str | None = None
    is_required: bool = True


class SourceEvidenceModel(BaseModel):
    message_index: int
    message_role: str
    snippet: str
    match_type: str
    confidence: float
    observation_tool: str | None = None


class SlotSourceRecordModel(BaseModel):
    slot: CriticalSlotModel
    source: SourceTrust
    evidence: list[SourceEvidenceModel]
    authorization_gap: bool
    risk_score: float


class SlotExtractionResultModel(BaseModel):
    tool_name: str
    critical_slots: list[CriticalSlotModel]
    non_critical_slots: list[str]
    extraction_method: Literal["registry", "registry+llm", "fallback"]
    warnings: list[str] = Field(default_factory=list)


class SourceAnalysisResultModel(BaseModel):
    slot_records: list[SlotSourceRecordModel]
    overall_risk: float
    has_untrusted_binding: bool
    has_role_only_binding: bool
    action_type_authorized: bool


class SlotDisclosureModel(BaseModel):
    slot_name: str
    display_name: str
    value: str
    source: SourceTrust
    source_detail: str
    risk_note: str | None = None


class ConfirmationPayloadModel(BaseModel):
    intervention: Literal["VAGUE_CONFIRM", "SOURCE_AWARE_CONFIRM"]
    tool_name: str
    action_summary: str
    slot_disclosures: list[SlotDisclosureModel]
    external_effect: str
    prompt_text: str
    required_disclosures: list[str]
    laundering_safe: bool


class ConfirmationResponseModel(BaseModel):
    outcome: Literal["approved", "rejected", "corrected"]
    corrected_slots: dict[str, Any] | None = None
    raw_text: str | None = None


class InterventionRecordModel(BaseModel):
    tool_call_id: str | None
    tool_name: str
    tool_args: dict[str, Any]
    critical_slots: list[CriticalSlotModel]
    slot_records: list[SlotSourceRecordModel]
    has_untrusted_binding: bool
    has_role_only_binding: bool
    overall_risk: float
    candidates_considered: list[str]
    selected_intervention: str
    policy_backend: str
    confirmation_prompt: str | None = None
    confirmation_response: str | None = None
    confirmation_laundering_risk: bool = False
    executed: bool = True
    executed_binding: dict[str, Any] | None = None
    repair_attempted: bool = False
    repair_result: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SafeConfirmLogModel(BaseModel):
    version: str = "0.2.0"
    mode: Literal["log_only", "active", "learning"]
    policy_backend: str
    records: list[InterventionRecordModel] = Field(default_factory=list)


class ExperiencePatternModel(BaseModel):
    tool_name: str
    user_role_binding: bool = False
    untrusted_source: str | None = None
    critical_slots: list[str] = Field(default_factory=list)
    action_category: str | None = None
    action_type_authorized: bool = True


class ExperienceModel(BaseModel):
    id: str
    pattern: ExperiencePatternModel
    intervention_choice: str
    rationale: str
    score_delta: float | None = None
    source_case_id: str | None = None


class VerificationScoreModel(BaseModel):
    intervention: str
    safety: float
    utility: float
    benign: float
    disclosure: float
    transparency: float
    total: float
    disqualified: bool = False
    disqualify_reason: str | None = None


class TrainingCaseModel(BaseModel):
    id: str
    suite: str
    tool_name: str
    query: str
    tool_args: dict[str, Any]
    observation_content: str | None = None
    observation_tool: str = "get_webpage"
    trusted_binding: dict[str, Any] = Field(default_factory=dict)
    safe_interventions: list[str] = Field(default_factory=list)
    unsafe_interventions: list[str] = Field(default_factory=list)
    laundering_interventions: list[str] = Field(default_factory=list)


class BenchmarkGroundTruthModel(BaseModel):
    safe_interventions: list[str] = Field(default_factory=list)
    unsafe_interventions: list[str] = Field(default_factory=list)
    laundering_interventions: list[str] = Field(default_factory=list)


class BenchmarkSetupModel(BaseModel):
    injection_vector: str = "get_webpage"
    poison_content: str | None = None


class BenchmarkCaseModel(BaseModel):
    id: str
    suite: str
    category: str
    user_task_template: str
    tool_name: str
    tool_args: dict[str, Any]
    setup: BenchmarkSetupModel = Field(default_factory=BenchmarkSetupModel)
    corrupted_slots: dict[str, Any] = Field(default_factory=dict)
    trusted_binding: dict[str, Any] = Field(default_factory=dict)
    ground_truth: BenchmarkGroundTruthModel = Field(default_factory=BenchmarkGroundTruthModel)
    benign: bool = False

    @property
    def query(self) -> str:
        return self.user_task_template

    @property
    def observation_content(self) -> str | None:
        return self.setup.poison_content

    @property
    def observation_tool(self) -> str:
        return self.setup.injection_vector


class TargetedRunResultModel(BaseModel):
    case_id: str
    policy_id: str
    suite: str
    category: str
    benign: bool = False
    utility: bool
    security: bool
    safeconfirm: SafeConfirmLogModel
    benchmark_case: dict[str, Any] | None = None


class InterventionMetricsModel(BaseModel):
    uar: float
    clr: float
    sdr: float
    tpr: float
    fbr: float
    rsr: float
    vcr: float
    composite: float
    corruption_cases: int
    benign_cases: int
    approved_confirmations: int
    repair_attempts: int
