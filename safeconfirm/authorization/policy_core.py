"""Benchmark-independent authorization policy (frozen rule_v1 semantics)."""

from __future__ import annotations

from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.types.models import InterventionType


def policy_from_state(state: AuthorizationState) -> InterventionType:
    """Authorization state machine: allow → repair → source-aware confirm → block/replan."""

    if not state.action_authorized:
        if state.overall_risk >= 0.7:
            return InterventionType.BLOCK
        return InterventionType.REPLAN

    if not state.has_untrusted_binding and state.overall_risk < 0.3:
        return InterventionType.ALLOW

    if state.repair_resolvable:
        return InterventionType.REPAIR

    if state.has_untrusted_binding or not state.binding_authorized:
        return InterventionType.SOURCE_AWARE_CONFIRM

    return InterventionType.ALLOW


def baseline_policy_from_state(state: AuthorizationState, policy_backend: str) -> InterventionType:
    if policy_backend == "baseline_allow":
        return InterventionType.ALLOW
    if policy_backend == "baseline_block":
        return InterventionType.BLOCK if not state.binding_authorized else InterventionType.ALLOW
    if policy_backend == "baseline_vague":
        return InterventionType.VAGUE_CONFIRM if not state.binding_authorized else InterventionType.ALLOW
    raise ValueError(f"Not a baseline backend: {policy_backend}")
