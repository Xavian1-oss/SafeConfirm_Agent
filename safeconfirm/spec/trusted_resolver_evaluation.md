# Trusted resolver vs evaluation ground truth

## Deployment model

SafeConfirm separates **provenance** (where did this binding value come from?) from **trusted resolution** (map a role label to an org-trusted email at execution time).

| Mechanism | Purpose |
|-----------|---------|
| `ProvenanceProvider` | User text, tool observations, role mentions, post-repair attestation |
| `RepairEngine` + `TrustedResolver` (`safeconfirm/resolver/trusted_resolver.py`) | Replace role-only or poisoned bindings using org directory |
| Case YAML `trusted_binding` | **Evaluation only** — witness for UAR/scoring, not a deployment directory |

## AgentDojo bridge (benchmark)

- `trusted_contacts_for_repair(case)` → `extra_args["safeconfirm"]["trusted_contacts"]` → `MappingTrustedResolver` on `TaskContext` (repair only, not provenance).
- Policy selects **REPAIR** only when `RepairEngine.can_resolve` succeeds (runtime/env preflight + `TaskContext.user_instruction` / `trusted_resolver`).
- `RepairEngine` does not read `extra_args`; banking role fallback uses `user_instruction` only.
- Corruption E2E tasks **omit** role contacts from the inbox address book so poison appears only in untrusted observations; repair is the intended recovery path.
- `task_context_from_extra_args` does **not** copy YAML contacts into provenance hints.

## Provenance attestation after repair

`TaskContext.resolver_attested_emails` is populated **only** after a successful repair (emails bound by the resolver this turn). Provenance may mark those values as `TRUSTED_CONTACT`; benchmark YAML email sets must not bypass gap detection on the initial analyze pass.

## CLR / confirm (operational)

At approval time, **CLR** uses **binding authorization gap remaining** on critical binding slots (see `requirements.md` and `safeconfirm/evaluation/metrics.py`). SDR measures disclosure completeness; partial disclosure can yield low SDR while CLR still counts laundering if the user approves with a gap. Repair success followed by re-analyze clears gaps before allow-without-confirm; failed repair falls back to source-aware confirm.
