from __future__ import annotations

from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.extraction.slot_extractor import get_tool_entry
from safeconfirm.types.models import InterventionType, SourceAnalysisResultModel


def generate_candidates(
    analysis: SourceAnalysisResultModel,
    registry: ToolSlotRegistry,
    tool_name: str,
    enable_repair: bool,
) -> list[InterventionType]:
    if not analysis.has_untrusted_binding and analysis.overall_risk < 0.3:
        return [InterventionType.ALLOW]

    candidates = [
        InterventionType.ALLOW,
        InterventionType.VAGUE_CONFIRM,
        InterventionType.SOURCE_AWARE_CONFIRM,
        InterventionType.BLOCK,
    ]
    entry = get_tool_entry(registry, tool_name)
    if enable_repair and entry is not None and entry.repair is not None:
        candidates.append(InterventionType.REPAIR)
    if analysis.has_untrusted_binding and (entry is None or entry.repair is None):
        candidates.append(InterventionType.REPLAN)
    return candidates
