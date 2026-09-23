from safeconfirm.authorization.policy_core import policy_from_state
from safeconfirm.authorization.state import AuthorizationState
from safeconfirm.types.models import InterventionType


def _state(**kwargs: object) -> AuthorizationState:
    defaults = dict(
        action_authorized=True,
        binding_authorized=True,
        has_untrusted_binding=False,
        has_role_only_binding=False,
        overall_risk=0.0,
    )
    defaults.update(kwargs)
    return AuthorizationState(**defaults)  # type: ignore[arg-type]


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
