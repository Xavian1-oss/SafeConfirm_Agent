from safeconfirm.resolver.trusted_resolver import (
    MappingTrustedResolver,
    NullTrustedResolver,
    trusted_resolver_from_extra_args,
)


def test_mapping_resolver_normalizes_roles():
    resolver = MappingTrustedResolver({"Supervisor": "supervisor@university.edu"})
    assert resolver.resolve_email_for_role("supervisor") == "supervisor@university.edu"
    assert resolver.can_resolve_role("SUPERVISOR") is True


def test_null_resolver_never_resolves():
    resolver = NullTrustedResolver()
    assert resolver.resolve_email_for_role("supervisor") is None
    assert resolver.can_resolve_role("supervisor") is False


def test_extra_args_factory_builds_mapping():
    extra_args = {"safeconfirm": {"trusted_contacts": {"supervisor": "supervisor@university.edu"}}}
    resolver = trusted_resolver_from_extra_args(extra_args)
    assert resolver.resolve_email_for_role("supervisor") == "supervisor@university.edu"
