#!/usr/bin/env bash
# Single API-window batch: all frozen 12-case workspace rows for Table 1 RQ1–RQ2,
# Appendix repair + provenance flip (p>0). Shared seeds and harness version.
#
# Usage:
#   ./util_scripts/run_unified_12case_batch.sh
#   BATCH_ID=unified_12case_20260919 ./util_scripts/run_unified_12case_batch.sh
#
# After completion:
#   ./util_scripts/sync_paper_metrics.sh
#   uv run python util_scripts/update_safeconfirm_tex_from_canonical.py
#   uv run python util_scripts/verify_paper_metrics.py
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
SEEDS="${SEEDS:-s0 s1 s2}"
BATCH_ID="${BATCH_ID:-unified_12case_$(date +%Y%m%d)}"
LOGROOT="runs/bridge/${BATCH_ID}"
FLIP_RATES="${FLIP_RATES:-0.05 0.10 0.20}"

mkdir -p "${LOGROOT}"
load_workspace_subset_args 12

run_benchmark() {
  local logdir="$1"
  shift
  echo "=== $(date -Iseconds) -> ${logdir} ==="
  mkdir -p "${logdir}"
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    --suite "${SUITE}" \
    --model "${MODEL}" \
    --attack parameter_poison \
    --defense safeconfirm \
    --logdir "${logdir}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}" \
    "$@"
}

aggregate_pattern() {
  local pattern="$1"
  local output="$2"
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${pattern}" \
    --output "${output}"
}

for seed in ${SEEDS}; do
  sid="${seed#s}"

  run_benchmark "${LOGROOT}/rule_v1/${seed}" \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${sid}"

  run_benchmark "${LOGROOT}/baseline_vague/${seed}" \
    --policy baseline_vague \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${sid}"

  run_benchmark "${LOGROOT}/baseline_block/${seed}" \
    --policy baseline_block \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${sid}"

  run_benchmark "${LOGROOT}/vague_compliant/${seed}" \
    --policy baseline_vague \
    --confirmer compliant_llm \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${sid}"

  run_benchmark "${LOGROOT}/repair_on/${seed}" \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${sid}"

  run_benchmark "${LOGROOT}/repair_off/${seed}" \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --no-repair \
    --run-id "${seed}" \
    --seed "${sid}"

  for rate in ${FLIP_RATES}; do
    tag="flip${rate//./}"
    SAFECONFIRM_PROVENANCE_FLIP_RATE="${rate}" \
    SAFECONFIRM_PROVENANCE_FLIP_SEED="${sid}" \
      run_benchmark "${LOGROOT}/${tag}/${seed}" \
        --policy rule_v1 \
        --confirmer llm_user \
        --confirmer-model "${MODEL}" \
        --run-id "${seed}" \
        --seed "${sid}" \
        --provenance-flip-rate "${rate}" \
        --provenance-flip-seed "${sid}"
  done
done

echo "Aggregating ${BATCH_ID}..."
aggregate_pattern "${LOGROOT}/rule_v1/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/rule_v1_aggregate.json"
aggregate_pattern "${LOGROOT}/baseline_vague/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/baseline_vague_aggregate.json"
aggregate_pattern "${LOGROOT}/baseline_block/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/baseline_block_aggregate.json"
aggregate_pattern "${LOGROOT}/vague_compliant/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/vague_compliant_aggregate.json"
aggregate_pattern "${LOGROOT}/repair_on/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/repair_on_aggregate.json"
aggregate_pattern "${LOGROOT}/repair_off/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/repair_off_aggregate.json"

for rate in ${FLIP_RATES}; do
  tag="flip${rate//./}"
  aggregate_pattern "${LOGROOT}/${tag}/s[0-9]/${SUITE}/metrics.json" "${LOGROOT}/${tag}_aggregate.json"
done

cp "${LOGROOT}/rule_v1_aggregate.json" "${LOGROOT}/flip0_aggregate.json"

printf '%s\n' \
  "{" \
  "  \"batch_id\": \"${BATCH_ID}\"," \
  "  \"model\": \"${MODEL}\"," \
  "  \"suite\": \"${SUITE}\"," \
  "  \"seeds\": \"${SEEDS}\"," \
  "  \"subset\": \"12-case frozen workspace prefix\"," \
  "  \"note\": \"flip0_aggregate.json aliases rule_v1_aggregate.json (p=0).\"" \
  "}" > "${LOGROOT}/batch_manifest.json"

echo "Unified batch complete: ${LOGROOT}"
echo "Set UNIFIED_12CASE_BATCH=${BATCH_ID} when running sync_paper_metrics.sh"
