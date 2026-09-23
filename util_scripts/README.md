# SafeConfirm util scripts

## Primary (paper Table 1–2)

| Script | Output |
|--------|--------|
| `run_extended_28case.sh` | 28-case workspace+banking E2E → `extended28_*` |
| `run_external_eval.sh` | External lineage (12 cases) → `{BATCH_ID}/p0_aggregate.json` |
| `run_provenance_baselines.sh` | block / vague / rule_v1 → provenance_*_aggregate.json |
| `run_provenance_sensitivity.sh` | Label-flip stress 0/5/10/20% × 3 seeds (12-case) |
| `summarize_provenance_flip_batch.py` | LaTeX rows for appendix `tab:prov-flip` |
| `run_confirm_ablation.sh` | Confirm rows (SA / vague / compliant) |
| `run_holdout_paired.sh` | Holdout footnote |
| `sync_paper_metrics.sh` | Copy aggregates → `6a9fb8173b16b4dea4fd1079/paper_metrics/canonical/` |

Shared: `benchmark_subsets.sh`, `aggregate_seed_metrics.py`

**Regression:** `./util_scripts/sync_paper_metrics.sh` then `uv run python util_scripts/verify_paper_metrics.py`

**Architecture:** [safeconfirm/spec/architecture.md](../safeconfirm/spec/architecture.md)

### Canonical batch directories (paper numbers)

| Canonical JSON | Source under `runs/bridge/` |
|----------------|-------------------------------|
| `confirm_sa_llm_poison_v2.json`, `confirm_vague_llm_poison_v2.json` | `confirm_ablation_poison_v2_20260910/` |
| `confirm_vague_compliant_llm.json` | `confirm_ablation_v4/vague_compliant_llm_aggregate.json` |
| `provenance_*_aggregate.json` | `evidence_20260916_1531/provenance_baselines/` |
| `extended28_*` | `e2e_extended_extend_v1_20260911/` |
| `banking_paired_p0_aggregate.json` | `evidence_20260916_1531/banking_paired/` |
| `external_*` | `external_v2_12case_20260919/` (fallback: `evidence_20260916_1531/`) |
| `provenance_flip*_aggregate.json` | `provenance_sensitivity/prov_flip_20260919/` |
| `component_12case_poison_v2.json`, repair, defense sweep | `*_poison_v2_20260910*` paths in `sync_paper_metrics.sh` |

## Mechanism / appendix

| Script | Purpose |
|--------|---------|
| `run_component_ablation.sh` | Allow/block/rule_v1 (allow 19.4% row) |
| `run_repair_ablation.sh`, `run_repair_subset_ablation.sh` | Appendix repair |
| `run_ds_defense_sweep_v2.sh` | Prompt defenses appendix |
| `run_native_generalization.sh` | Native AgentDojo smoke |
| `run_banking_benign_check.sh` | Banking benign diagnostic |
| `run_paired_security_rerun.sh` | 16-case paired (per-case appendix) |

Analysis: `compare_confirm_ablation.py`, `compare_component_ablation.py`, `analyze_per_case.py`, `export_per_case_appendix.py`

## Optional

| Script | Purpose |
|--------|---------|
| `run_cross_model_signature.sh` | Cross-model 12-case (out of paper scope) |
| `run_pilot_asr_check.sh` | Dev: P0 ASR smoke before paired rerun |
