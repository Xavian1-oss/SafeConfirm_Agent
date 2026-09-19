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

## Mechanism / appendix

| Script | Purpose |
|--------|---------|
| `run_component_ablation.sh` | Allow/block/rule_v1 (allow 19.4% row) |
| `run_repair_ablation.sh`, `run_repair_subset_ablation.sh` | Appendix repair |
| `run_retrieval_ablation.sh` | Appendix retrieval (trim in paper) |
| `run_ds_defense_sweep_v2.sh` | Prompt defenses appendix |
| `run_native_generalization.sh` | Native AgentDojo smoke |
| `run_banking_benign_check.sh` | Banking benign diagnostic |

## Optional / rebuttal

| Script | Purpose |
|--------|---------|
| `run_cross_model_signature.sh` | 12-case, 2 models (signature only) |
| `run_cross_model_validation.sh` | **Deprecated wrapper** → calls signature |
| `run_pilot_asr_check.sh` | Dev: verify P0 ASR before full paired rerun |
| `run_paired_security_rerun.sh` | 16-case paired (appendix / per-case) |
| `run_goal_c_all.sh` | Legacy one-shot Goal C bundle |

Analysis: `compare_confirm_ablation.py`, `compare_component_ablation.py`, `analyze_per_case.py`, `export_per_case_appendix.py`
