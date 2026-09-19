#!/usr/bin/env bash
# E2: synthetic provenance-label flip sensitivity on frozen 12-case workspace subset.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/provenance_sensitivity}"
MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
FLIP_RATES="${FLIP_RATES:-0 0.05 0.10 0.20}"
BATCH_ID="${BATCH_ID:-prov_flip_$(date +%Y%m%d)}"

mkdir -p "${LOGROOT}"
load_workspace_subset_args 12

run_condition() {
  local rate="$1"
  local seed="$2"
  local tag
  if [[ "${rate}" == "0" || "${rate}" == "0.0" ]]; then
    tag="flip0"
  else
    tag="flip${rate//./}"
  fi
  local logdir="${LOGROOT}/${BATCH_ID}/${tag}_${seed}"
  echo "=== provenance flip rate=${rate} seed=${seed} -> ${logdir} ==="
  SAFECONFIRM_PROVENANCE_FLIP_RATE="${rate}" \
  SAFECONFIRM_PROVENANCE_FLIP_SEED="${seed#s}" \
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" \
      -m "${MODEL}" \
      -a parameter_poison \
      --defense safeconfirm \
      --policy rule_v1 \
      --confirmer llm_user \
      --confirmer-model "${MODEL}" \
      --run-id "${seed}" \
      --seed "${seed#s}" \
      --logdir "${logdir}" \
      --provenance-flip-rate "${rate}" \
      --provenance-flip-seed "${seed#s}" \
      "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
}

for rate in ${FLIP_RATES}; do
  for seed in ${SEEDS}; do
    run_condition "${rate}" "${seed}"
  done
done

for rate in ${FLIP_RATES}; do
  tag="flip${rate//./}"
  if [[ "${rate}" == "0" || "${rate}" == "0.0" ]]; then
    tag="flip0"
  fi
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/${BATCH_ID}/${tag}_s[0-9]/${SUITE}/metrics.json" \
    --output "${LOGROOT}/${BATCH_ID}/${tag}_aggregate.json"
done

echo "Provenance sensitivity batch under ${LOGROOT}/${BATCH_ID}"
