from __future__ import annotations

from safeconfirm.authorization.build_state import authorization_state_from_analysis
from safeconfirm.authorization.policy_core import baseline_policy_from_state, policy_from_state
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.extraction.registry_loader import ToolSlotRegistry
from safeconfirm.types.models import InterventionType, SourceAnalysisResultModel


def select_intervention_for_state(state: AuthorizationState, policy_backend: str) -> InterventionType:
    if policy_backend == "baseline_allow":
        return baseline_policy_from_state(state, "baseline_allow")
    if policy_backend == "baseline_block":
        return baseline_policy_from_state(state, "baseline_block")
    if policy_backend == "baseline_vague":
        return baseline_policy_from_state(state, "baseline_vague")
    if policy_backend != "rule_v1":
        raise ValueError(f"Unknown policy_backend: {policy_backend!r}")

    return policy_from_state(state)


def select_intervention(
    analysis: SourceAnalysisResultModel,
    registry: ToolSlotRegistry,
    tool_name: str,
    policy_backend: str,
    *,
    repair_resolvable: bool = False,
) -> InterventionType:
    state = authorization_state_from_analysis(
        analysis,
        tool_name=tool_name,
        registry=registry,
        repair_resolvable=repair_resolvable,
    )
    return select_intervention_for_state(state, policy_backend)
