"""Authorization state consumed by the intervention policy core."""

from __future__ import annotations

from pydantic import BaseModel


class AuthorizationState(BaseModel):
    """Compact decision state: benchmark-independent authorization summary."""

    action_authorized: bool
    binding_authorized: bool
    has_untrusted_binding: bool
    has_role_only_binding: bool
    repair_resolvable: bool = False
    overall_risk: float = 0.0
