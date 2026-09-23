from safeconfirm.authorization.policy_core import policy_from_state
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.types.models import InterventionType


def _state(
    *,
    action_authorized: bool = True,
    binding_authorized: bool = True,
    has_untrusted_binding: bool = False,
    has_role_only_binding: bool = False,
    repair_resolvable: bool = False,
    overall_risk: float = 0.0,
) -> AuthorizationState:
    return AuthorizationState(
        action_authorized=action_authorized,
        binding_authorized=binding_authorized,
        has_untrusted_binding=has_untrusted_binding,
        has_role_only_binding=has_role_only_binding,
        repair_resolvable=repair_resolvable,
        overall_risk=overall_risk,
    )


def test_policy_allow_when_no_untrusted_low_risk():
    assert policy_from_state(_state()) == InterventionType.ALLOW


def test_policy_replan_when_action_unauthorized_low_risk():
    assert (
        policy_from_state(_state(action_authorized=False, overall_risk=0.2))
        == InterventionType.REPLAN
    )


def test_policy_block_when_action_unauthorized_high_risk():
    assert (
        policy_from_state(_state(action_authorized=False, overall_risk=0.8))
        == InterventionType.BLOCK
    )


def test_policy_repair_when_role_only():
    assert (
        policy_from_state(
            _state(
                has_untrusted_binding=True,
                has_role_only_binding=True,
                repair_resolvable=True,
                overall_risk=0.8,
            )
        )
        == InterventionType.REPAIR
    )


def test_policy_confirm_when_role_only_gap_without_repair():
    assert (
        policy_from_state(
            _state(
                binding_authorized=False,
                has_role_only_binding=True,
                repair_resolvable=False,
                overall_risk=0.5,
            )
        )
        == InterventionType.SOURCE_AWARE_CONFIRM
    )


def test_policy_confirm_when_untrusted_binding():
    assert (
        policy_from_state(
            _state(has_untrusted_binding=True, has_role_only_binding=False, overall_risk=0.8)
        )
        == InterventionType.SOURCE_AWARE_CONFIRM
    )
