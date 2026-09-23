"""Org-trusted contact resolution (deployment directory), separate from provenance."""

from __future__ import annotations

from typing import Protocol


class TrustedResolver(Protocol):
    """Maps a role label to an organization-trusted email (or account id)."""

    def resolve_email_for_role(self, role_label: str) -> str | None: ...

    def can_resolve_role(self, role_label: str) -> bool: ...


class NullTrustedResolver:
    def resolve_email_for_role(self, role_label: str) -> str | None:
        del role_label
        return None

    def can_resolve_role(self, role_label: str) -> bool:
        del role_label
        return False


NULL_TRUSTED_RESOLVER = NullTrustedResolver()


class MappingTrustedResolver:
    """In-memory role → email map (benchmark mock or config-backed directory)."""

    def __init__(self, role_to_email: dict[str, str]) -> None:
        normalized: dict[str, str] = {}
        for key, value in role_to_email.items():
            if value:
                normalized[str(key).strip().lower()] = str(value).strip()
        self._role_to_email = normalized

    def resolve_email_for_role(self, role_label: str) -> str | None:
        key = role_label.strip().lower()
        if key in self._role_to_email:
            return self._role_to_email[key]
        for map_key, email in self._role_to_email.items():
            if map_key == key:
                return email
        return None

    def can_resolve_role(self, role_label: str) -> bool:
        return self.resolve_email_for_role(role_label) is not None


def trusted_resolver_from_extra_args(
    extra_args: dict | None,
) -> MappingTrustedResolver | NullTrustedResolver:
    if not extra_args:
        return NULL_TRUSTED_RESOLVER
    trusted_contacts = extra_args.get("safeconfirm", {}).get("trusted_contacts") or {}
    if not isinstance(trusted_contacts, dict) or not trusted_contacts:
        return NULL_TRUSTED_RESOLVER
    return MappingTrustedResolver({str(k): str(v) for k, v in trusted_contacts.items() if v})
