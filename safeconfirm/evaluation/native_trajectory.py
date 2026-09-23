"""Frozen eligibility labeling for native AgentDojo benchmark logs (policy-freeze v1)."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agentdojo.functions_runtime import EmptyEnv, FunctionCall, FunctionsRuntime
from agentdojo.types import ChatMessage, get_text_content_as_str
from safeconfirm.authorization.action_auth import action_type_authorized
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.context.repair_preflight import RepairPreflight
from safeconfirm.context.task_context import task_context_from_parts
from safeconfirm.evaluation.metrics import RISK_GAP_THRESHOLD
from safeconfirm.extraction.registry_loader import ToolSlotRegistry, load_registry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.pipeline.orchestrator import SafeConfirmPipeline
from safeconfirm.types.models import InterventionRecordModel, SafeConfirmLogModel


class TrajectoryPrimaryLabel(str, Enum):
    """Mutually exclusive primary bucket (first matching rule in ``classify_trajectory``)."""

    NO_TOOL_CALLS = "no_tool_calls"
    BINDING_RELEVANT = "binding_relevant"
    UNSUPPORTED_TOOL = "unsupported_tool"
    BINDING_TRUSTED = "binding_trusted"
    NO_BINDING_SIDE_EFFECT = "no_binding_side_effect"
    OTHER = "other"


class TrajectoryCoverageModel(BaseModel):
    primary: TrajectoryPrimaryLabel
    binding_relevant: bool = False
    unsupported_tool: bool = False
    no_binding_side_effect: bool = False
    binding_trusted: bool = False
    goal_hijacking: bool = False
    analyzed_tool_calls: int = 0
    registry_tool_calls: int = 0


class NativeRunModel(BaseModel):
    trajectory_id: str
    suite_name: str
    user_task_id: str
    injection_task_id: str | None
    attack_type: str | None
    pipeline_name: str | None
    utility: bool
    security: bool
    benign: bool
    user_instruction: str
    coverage: TrajectoryCoverageModel
    safeconfirm: SafeConfirmLogModel = Field(default_factory=lambda: SafeConfirmLogModel(mode="log_only", policy_backend="none"))


def normalize_chat_messages(messages: list[Any]) -> list[ChatMessage]:
    """Deserialize AgentDojo JSON logs into typed messages for replay analysis."""
    normalized: list[ChatMessage] = []
    for raw in messages:
        if not isinstance(raw, dict):
            continue
        message = dict(raw)
        if message.get("role") == "assistant" and message.get("tool_calls"):
            message["tool_calls"] = [_parse_function_call(call) for call in message["tool_calls"]]
        if message.get("role") == "tool" and message.get("tool_call") is not None:
            message["tool_call"] = _parse_function_call(message["tool_call"])
        normalized.append(message)  # type: ignore[arg-type]
    return normalized


def user_instruction_from_messages(messages: list[ChatMessage]) -> str:
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content") or []
        text = get_text_content_as_str(content).strip()
        if text:
            return text
    return ""


def _parse_function_call(raw: Any) -> FunctionCall:
    if isinstance(raw, FunctionCall):
        return raw
    if isinstance(raw, dict):
        return FunctionCall.model_validate(raw)
    raise TypeError(f"Unsupported tool call payload: {type(raw)!r}")


def iter_assistant_tool_calls(messages: list[ChatMessage]) -> list[tuple[int, FunctionCall]]:
    """Return (message_index, call) for each assistant tool call in order."""
    found: list[tuple[int, FunctionCall]] = []
    for index, message in enumerate(messages):
        if message.get("role") != "assistant":
            continue
        for raw_call in message.get("tool_calls") or []:
            found.append((index, _parse_function_call(raw_call)))
    return found


def is_binding_relevant_record(
    record: InterventionRecordModel,
    *,
    user_instruction: str,
    registry: ToolSlotRegistry,
) -> bool:
    if not action_type_authorized(record.tool_name, user_instruction, registry):
        return False
    binding_slots = [
        slot_record
        for slot_record in record.slot_records
        if slot_record.slot.slot_class == "binding"
    ]
    if not binding_slots:
        return False
    return any(
        slot_record.authorization_gap and slot_record.slot.risk_weight >= RISK_GAP_THRESHOLD
        for slot_record in binding_slots
    )


def is_unknown_tool_record(record: InterventionRecordModel, registry: ToolSlotRegistry) -> bool:
    if get_tool_entry(registry, record.tool_name) is None:
        return True
    return any(slot_record.slot.slot_type == "unknown_registry" for slot_record in record.slot_records)


def replay_records_from_messages(
    log: dict[str, Any],
    *,
    pipeline: SafeConfirmPipeline,
) -> list[InterventionRecordModel]:
    """Policy-free replay for frozen eligibility (same label on P0 and defended runs)."""
    raw_messages = log.get("messages") or []
    if not raw_messages:
        return []
    messages = normalize_chat_messages(raw_messages)
    user_instruction = user_instruction_from_messages(messages)
    preflight = RepairPreflight(runtime=FunctionsRuntime([]), env=EmptyEnv())
    records: list[InterventionRecordModel] = []
    for message_index, tool_call in iter_assistant_tool_calls(messages):
        context = task_context_from_parts(user_instruction, messages[: message_index + 1])
        record = pipeline.analyze_tool_call(tool_call, context, repair_preflight=preflight)
        records.append(record)
    return records


def eligibility_records_from_log(
    log: dict[str, Any],
    *,
    pipeline: SafeConfirmPipeline,
    config: SafeConfirmConfig,
) -> list[InterventionRecordModel]:
    """Frozen eligibility inputs: replay from messages; fall back to logged analyses when defended runs strip tool_calls."""
    replayed = replay_records_from_messages(log, pipeline=pipeline)
    if replayed:
        return replayed
    logged = safeconfirm_log_from_benchmark_log(log, config=config).records
    return list(logged)


def safeconfirm_log_from_benchmark_log(log: dict[str, Any], *, config: SafeConfirmConfig) -> SafeConfirmLogModel:
    raw_sc = log.get("safeconfirm")
    if raw_sc:
        return raw_sc if isinstance(raw_sc, SafeConfirmLogModel) else SafeConfirmLogModel.model_validate(raw_sc)
    return SafeConfirmLogModel(mode="log_only", policy_backend=config.policy_backend, records=[])


def classify_trajectory(
    *,
    records: list[InterventionRecordModel],
    user_instruction: str,
    registry: ToolSlotRegistry,
    utility: bool,
    security: bool,
    benign: bool,
) -> TrajectoryCoverageModel:
    tool_calls = len(records)
    if tool_calls == 0:
        return TrajectoryCoverageModel(primary=TrajectoryPrimaryLabel.NO_TOOL_CALLS)

    binding_relevant = any(
        is_binding_relevant_record(record, user_instruction=user_instruction, registry=registry)
        for record in records
    )
    unsupported = any(is_unknown_tool_record(record, registry) for record in records)
    registry_calls = sum(1 for record in records if get_tool_entry(registry, record.tool_name) is not None)

    has_binding_slot = any(
        slot_record.slot.slot_class == "binding" for record in records for slot_record in record.slot_records
    )
    any_binding_gap = any(
        slot_record.slot.slot_class == "binding" and slot_record.authorization_gap
        for record in records
        for slot_record in record.slot_records
    )
    binding_trusted = has_binding_slot and not any_binding_gap and not binding_relevant
    no_binding_side_effect = registry_calls > 0 and not has_binding_slot and not binding_relevant

    goal_hijacking = not benign and not security and not binding_relevant

    if binding_relevant:
        primary = TrajectoryPrimaryLabel.BINDING_RELEVANT
    elif unsupported:
        primary = TrajectoryPrimaryLabel.UNSUPPORTED_TOOL
    elif binding_trusted:
        primary = TrajectoryPrimaryLabel.BINDING_TRUSTED
    elif no_binding_side_effect:
        primary = TrajectoryPrimaryLabel.NO_BINDING_SIDE_EFFECT
    else:
        primary = TrajectoryPrimaryLabel.OTHER

    return TrajectoryCoverageModel(
        primary=primary,
        binding_relevant=binding_relevant,
        unsupported_tool=unsupported,
        no_binding_side_effect=no_binding_side_effect,
        binding_trusted=binding_trusted,
        goal_hijacking=goal_hijacking,
        analyzed_tool_calls=tool_calls,
        registry_tool_calls=registry_calls,
    )


def load_native_run_from_log(
    path: Path,
    *,
    registry: ToolSlotRegistry | None = None,
    pipeline: SafeConfirmPipeline | None = None,
) -> NativeRunModel | None:
    with path.open(encoding="utf-8") as handle:
        log = json.load(handle)
    if "utility" not in log or "security" not in log:
        return None

    config = SafeConfirmConfig.load()
    registry = registry or load_registry(config.registry_path)
    pipeline = pipeline or SafeConfirmPipeline(config)

    raw_messages = log.get("messages") or []
    messages = normalize_chat_messages(raw_messages)
    user_instruction = user_instruction_from_messages(messages)
    injection_task_id = log.get("injection_task_id") or None
    if injection_task_id in ("", "none", "unknown_injection_task_id"):
        injection_task_id = None
    user_task_id = str(log.get("user_task_id", "unknown"))
    suite_name = str(log.get("suite_name", "unknown"))
    benign = injection_task_id is None

    eligibility_records = eligibility_records_from_log(log, pipeline=pipeline, config=config)
    coverage = classify_trajectory(
        records=eligibility_records,
        user_instruction=user_instruction,
        registry=registry,
        utility=bool(log["utility"]),
        security=bool(log["security"]),
        benign=benign,
    )

    safeconfirm = safeconfirm_log_from_benchmark_log(log, config=config)

    trajectory_id = f"{suite_name}/{user_task_id}/{injection_task_id or 'none'}"
    return NativeRunModel(
        trajectory_id=trajectory_id,
        suite_name=suite_name,
        user_task_id=user_task_id,
        injection_task_id=injection_task_id,
        attack_type=log.get("attack_type"),
        pipeline_name=log.get("pipeline_name"),
        utility=bool(log["utility"]),
        security=bool(log["security"]),
        benign=benign,
        user_instruction=user_instruction,
        coverage=coverage,
        safeconfirm=safeconfirm,
    )


def discover_benchmark_logs(logdir: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(logdir.rglob("*.json")):
        if not path.is_file():
            continue
        if path.name in {"native_comparison.json", "metrics.json"}:
            continue
        try:
            with path.open(encoding="utf-8") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        if "utility" not in raw or "suite_name" not in raw:
            continue
        user_task_id = str(raw.get("user_task_id", ""))
        if not user_task_id.startswith("user_task_"):
            continue
        if raw.get("attack_type") is None:
            continue
        paths.append(path)
    return paths
