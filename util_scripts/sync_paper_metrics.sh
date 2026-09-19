#!/usr/bin/env bash
# Copy aggregate metrics into paper_metrics/ for reproducibility (no full trajectories).
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="6a9fb8173b16b4dea4fd1079/paper_metrics"
CANON="${DEST}/canonical"
LEGACY="${DEST}/legacy"
mkdir -p "${CANON}" "${LEGACY}"

copy_if() {
  local src="$1"
  local dest="$2"
  if [[ -f "${src}" ]]; then
    cp "${src}" "${dest}"
    echo "  synced ${dest}"
  else
    echo "  skip (missing): ${src}"
  fi
}

echo "Syncing paper metrics -> ${DEST}"

UNIFIED="${UNIFIED_12CASE_BATCH:-}"
if [[ -n "${UNIFIED}" && -f "runs/bridge/${UNIFIED}/rule_v1_aggregate.json" ]]; then
  UB="runs/bridge/${UNIFIED}"
  echo "Using unified 12-case batch: ${UNIFIED}"
  copy_if "${UB}/rule_v1_aggregate.json" "${CANON}/confirm_sa_llm_poison_v2.json"
  copy_if "${UB}/rule_v1_aggregate.json" "${CANON}/provenance_rule_v1_aggregate.json"
  copy_if "${UB}/baseline_vague_aggregate.json" "${CANON}/confirm_vague_llm_poison_v2.json"
  copy_if "${UB}/baseline_vague_aggregate.json" "${CANON}/provenance_vague_aggregate.json"
  copy_if "${UB}/baseline_block_aggregate.json" "${CANON}/provenance_block_aggregate.json"
  copy_if "${UB}/vague_compliant_aggregate.json" "${CANON}/confirm_vague_compliant_llm.json"
  copy_if "${UB}/repair_on_aggregate.json" "${CANON}/repair_full_on_poison_v2.json"
  copy_if "${UB}/repair_off_aggregate.json" "${CANON}/repair_full_off_poison_v2.json"
  copy_if "${UB}/flip0_aggregate.json" "${CANON}/provenance_flip0_aggregate.json"
  copy_if "${UB}/flip005_aggregate.json" "${CANON}/provenance_flip005_aggregate.json"
  copy_if "${UB}/flip010_aggregate.json" "${CANON}/provenance_flip010_aggregate.json"
  copy_if "${UB}/flip020_aggregate.json" "${CANON}/provenance_flip020_aggregate.json"
fi

# --- Primary E2E (28-case + holdout) ---
copy_if runs/bridge/e2e_extended_extend_v1_20260911/safeconfirm_workspace_p0_aggregate.json "${CANON}/extended28_ws_p0.json"
copy_if runs/bridge/e2e_extended_extend_v1_20260911/safeconfirm_workspace_sc_aggregate.json "${CANON}/extended28_ws_sc.json"
copy_if runs/bridge/e2e_extended_extend_v1_20260911/safeconfirm_banking_p0_aggregate.json "${CANON}/extended28_banking_p0.json"
copy_if runs/bridge/e2e_extended_extend_v1_20260911/safeconfirm_banking_sc_aggregate.json "${CANON}/extended28_banking_sc.json"
copy_if runs/bridge/holdout_holdout_v1_20260911/safeconfirm_workspace_p0_aggregate.json "${CANON}/holdout_ws_p0.json"
copy_if runs/bridge/holdout_holdout_v1_20260911/safeconfirm_workspace_sc_aggregate.json "${CANON}/holdout_ws_sc.json"
copy_if runs/bridge/holdout_holdout_v1_20260911/safeconfirm_banking_p0_aggregate.json "${CANON}/holdout_banking_p0.json"
copy_if runs/bridge/holdout_holdout_v1_20260911/safeconfirm_banking_sc_aggregate.json "${CANON}/holdout_banking_sc.json"

# --- 12-case mechanism ablations (v0.4.2 poison-v2; skipped when UNIFIED_12CASE_BATCH set) ---
if [[ -z "${UNIFIED}" || ! -f "runs/bridge/${UNIFIED}/rule_v1_aggregate.json" ]]; then
copy_if runs/bridge/component_ablation_poison_v2_20260910/summary.json "${CANON}/component_12case_poison_v2.json"
copy_if runs/bridge/confirm_ablation_poison_v2_20260910/sa_llm_aggregate.json "${CANON}/confirm_sa_llm_poison_v2.json"
copy_if runs/bridge/confirm_ablation_poison_v2_20260910/vague_llm_aggregate.json "${CANON}/confirm_vague_llm_poison_v2.json"
copy_if runs/bridge/confirm_ablation_v4/vague_compliant_llm_aggregate.json "${CANON}/confirm_vague_compliant_llm.json"
copy_if runs/bridge/e2e_ds_poison_v2_20260910_defense_comparison.json "${CANON}/defense_sweep_12case_poison_v2.json"
copy_if runs/bridge/ablation_repair_poison_v2_20260910/on/safeconfirm_workspace/metrics.json "${CANON}/repair_full_on_poison_v2.json"
copy_if runs/bridge/ablation_repair_poison_v2_20260910/off/safeconfirm_workspace/metrics.json "${CANON}/repair_full_off_poison_v2.json"
fi
copy_if runs/bridge/ablation_repair_subset_poison_v2_20260910/on/safeconfirm_workspace/metrics.json "${CANON}/repair_subset_on_poison_v2.json"
copy_if runs/bridge/ablation_repair_subset_poison_v2_20260910/off/safeconfirm_workspace/metrics.json "${CANON}/repair_subset_off_poison_v2.json"
copy_if runs/bridge/e2e_retrieval_poison_v2_20260910/rule_v1/safeconfirm_workspace/metrics.json "${CANON}/retrieval_rule_v1_poison_v2.json"
copy_if runs/bridge/e2e_retrieval_poison_v2_20260910/retrieval/safeconfirm_workspace/metrics.json "${CANON}/retrieval_policy_poison_v2.json"

# --- 16-case paired batch (per-case table / tab:percase) ---
copy_if runs/bridge/paired_security_poison_v2_16case/p0_aggregate.json "${CANON}/paired_p0_16case_poison_v2.json"
copy_if runs/bridge/paired_security_poison_v2_16case/sc_aggregate.json "${CANON}/paired_sc_16case_poison_v2.json"
copy_if runs/bridge/paired_security_poison_v2_16case/paired_comparison.json "${CANON}/paired_comparison_16case_poison_v2.json"

# --- Native generalization ---
copy_if runs/native_gen/ds_10task_v1/summary.json "${CANON}/native_gen_10task_tool_knowledge.json"

# --- Evidence strength batch (Sep. 2026) ---
EVID="runs/bridge/evidence_20260916_1531"
EXT_V2="runs/bridge/external_v2_12case_20260919"
if [[ -f "${EXT_V2}/p0_aggregate.json" ]]; then
  copy_if "${EXT_V2}/p0_aggregate.json" "${CANON}/external_p0_aggregate.json"
  copy_if "${EXT_V2}/sc_aggregate.json" "${CANON}/external_sc_aggregate.json"
else
  copy_if "${EVID}/p0_aggregate.json" "${CANON}/external_p0_aggregate.json"
  copy_if "${EVID}/sc_aggregate.json" "${CANON}/external_sc_aggregate.json"
fi
copy_if "${EVID}/banking_paired/p0_aggregate.json" "${CANON}/banking_paired_p0_aggregate.json"
copy_if "${EVID}/banking_paired/sc_aggregate.json" "${CANON}/banking_paired_sc_aggregate.json"
if [[ -z "${UNIFIED}" || ! -f "runs/bridge/${UNIFIED}/rule_v1_aggregate.json" ]]; then
copy_if "${EVID}/provenance_baselines/baseline_block_aggregate.json" "${CANON}/provenance_block_aggregate.json"
copy_if "${EVID}/provenance_baselines/baseline_vague_aggregate.json" "${CANON}/provenance_vague_aggregate.json"
copy_if "${EVID}/provenance_baselines/rule_v1_aggregate.json" "${CANON}/provenance_rule_v1_aggregate.json"

PROV_FLIP="runs/bridge/provenance_sensitivity/prov_flip_20260919"
for tag in flip0 flip005 flip010 flip020; do
  copy_if "${PROV_FLIP}/${tag}_aggregate.json" "${CANON}/provenance_${tag}_aggregate.json"
done
fi

# --- Legacy (pre-28-case primary / superseded aggregates) ---
copy_if runs/bridge/e2e_deepseek_v4_workspace_aggregate.json "${LEGACY}/main_v4_workspace.json"
copy_if runs/bridge/e2e_banking_deepseek_v4/safeconfirm_banking/metrics.json "${LEGACY}/main_v4_banking.json"
copy_if runs/bridge/e2e_banking_p0_v1/safeconfirm_banking/metrics.json "${LEGACY}/banking_p0_v1.json"
copy_if runs/bridge/e2e_banking_p0_v1_aggregate.json "${LEGACY}/banking_p0_aggregate.json"
copy_if runs/bridge/e2e_deepseek_v3_aggregate.json "${LEGACY}/main_v3_12case.json"
copy_if runs/bridge/component_ablation/summary.json "${LEGACY}/component_12case.json"
copy_if runs/bridge/confirm_ablation_v4/sa_llm_aggregate.json "${LEGACY}/confirm_sa_llm.json"
copy_if runs/bridge/confirm_ablation_v4/vague_llm_aggregate.json "${LEGACY}/confirm_vague_llm.json"
copy_if runs/bridge/e2e_ds_v2_defense_comparison.json "${LEGACY}/defense_sweep_12case.json"
copy_if runs/bridge/e2e_p0_v4_workspace_aggregate.json "${LEGACY}/p0_v4_16case.json"
copy_if runs/bridge/e2e_p0_v3_aggregate.json "${LEGACY}/p0_v3_12case.json"
copy_if runs/bridge/paired_security_poison_v2_20260910/p0_aggregate.json "${LEGACY}/paired_p0_12case_poison_v2.json"
copy_if runs/bridge/paired_security_poison_v2_20260910/sc_aggregate.json "${LEGACY}/paired_sc_12case_poison_v2.json"
copy_if runs/bridge/paired_security_poison_v2_20260910/paired_comparison.json "${LEGACY}/paired_comparison_poison_v2.json"

echo "Regenerating RQ1 bar chart from canonical JSON..."
uv run python util_scripts/generate_rq1_bar_chart.py

echo "Done."
