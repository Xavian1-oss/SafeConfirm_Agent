from __future__ import annotations

from safeconfirm.analysis.source_analyzer import has_binding_authorization_gap
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.types.models import SourceAnalysisResultModel


def authorization_state_from_analysis(
    analysis: SourceAnalysisResultModel,
    *,
    tool_name: str,
    registry: ToolSlotRegistry,
    repair_resolvable: bool = False,
) -> AuthorizationState:
    del tool_name, registry  # Kept for call-site clarity (tool-scoped analysis already applied).
    binding_authorized = not has_binding_authorization_gap(analysis.slot_records)
    return AuthorizationState(
        action_authorized=analysis.action_type_authorized,
        binding_authorized=binding_authorized,
        has_untrusted_binding=analysis.has_untrusted_binding,
        has_role_only_binding=analysis.has_role_only_binding,
        repair_resolvable=repair_resolvable,
        overall_risk=analysis.overall_risk,
    )
