from __future__ import annotations

from agentdojo.functions_runtime import FunctionCall
from safeconfirm.context.repair_preflight import RepairPreflight
from safeconfirm.context.task_context import TaskContext
from safeconfirm.execution.repair_engine import RepairEngine
from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.types.models import InterventionRecordModel, SourceAnalysisResultModel


def compute_repair_resolvable(
    analysis: SourceAnalysisResultModel,
    tool_call: FunctionCall,
    *,
    enable_repair: bool,
    registry: ToolSlotRegistry,
    repair_engine: RepairEngine,
    context: TaskContext,
    preflight: RepairPreflight | None,
) -> bool:
    entry = get_tool_entry(registry, tool_call.function)
    repair_available = enable_repair and entry is not None and entry.repair is not None
    if not repair_available or not analysis.has_role_only_binding:
        return False

    if preflight is not None:
        stub = _analysis_record_stub(tool_call, analysis)
        return repair_engine.can_resolve(
            tool_call,
            stub,
            preflight.runtime,
            preflight.env,
            user_instruction=context.user_instruction,
            trusted_resolver=context.trusted_resolver,
        )

    role_label = _primary_role_label(analysis)
    if role_label is not None and context.trusted_resolver.can_resolve_role(role_label):
        return True
    return False


def _primary_role_label(analysis: SourceAnalysisResultModel) -> str | None:
    for record in analysis.slot_records:
        if record.slot.slot_class == "binding" and record.slot.role_label:
            return record.slot.role_label
    return None


def _analysis_record_stub(
    tool_call: FunctionCall,
    analysis: SourceAnalysisResultModel,
) -> InterventionRecordModel:
    return InterventionRecordModel(
        tool_call_id=tool_call.id,
        tool_name=tool_call.function,
        tool_args=dict(tool_call.args),
        critical_slots=[record.slot for record in analysis.slot_records],
        slot_records=analysis.slot_records,
        has_untrusted_binding=analysis.has_untrusted_binding,
        has_role_only_binding=analysis.has_role_only_binding,
        overall_risk=analysis.overall_risk,
        selected_intervention="",
        policy_backend="",
    )
