# SafeConfirm architecture (paper core)

```text
Tool call
  ↓
Extract critical binding slots (registry)
  ↓
Provenance attribution → authorization gaps
  ↓
AuthorizationState + rule_v1 (or baseline ablations)
  ↓
ALLOW | REPAIR | SOURCE-AWARE / VAGUE CONFIRM | BLOCK | REPLAN
  ↓
InterventionExecutor (repair → re-analyze; confirm; block)
  ↓
TSR / ASR / SDR / CLR (evaluation)
```

## Module map

| Layer | Module |
|-------|--------|
| Adapter | `safeconfirm/benchmark/agentdojo_adapter.py` |
| Context | `safeconfirm/context/task_context.py` |
| Extraction | `safeconfirm/extraction/` |
| Provenance | `safeconfirm/provenance/` |
| Authorization | `safeconfirm/authorization/` (`action_auth`, `policy_core`, `analyzer`) |
| Trusted resolver | `safeconfirm/resolver/trusted_resolver.py` |
| Repair | `safeconfirm/execution/repair_engine.py` |
| Confirm | `safeconfirm/execution/confirmation.py`, confirmers |
| Executor | `safeconfirm/execution/intervention_executor.py` |
| Hook | `safeconfirm/pipeline/intervention_element.py` |
| Metrics | `safeconfirm/evaluation/metrics.py` |
| Bridge | `safeconfirm_bridge/` |

Case YAML is **evaluation-only** (UAR witnesses, mock resolver for repair). Provenance does not ingest YAML email sets. See [trusted_resolver_evaluation.md](./trusted_resolver_evaluation.md).

**Production path:** `SafeConfirmIntervention` → adapter (`TaskContext` + `RepairPreflight`) → analyze → `InterventionExecutor` (repair reads `user_instruction` / `trusted_resolver` only). Confirmer config still uses `extra_args`. Direct `SafeConfirmPipeline.analyze_tool_call` is for tests and post-repair re-analysis.

**Policy backends:** `rule_v1` (default); `baseline_allow` / `baseline_block` / `baseline_vague` for paper ablations.
