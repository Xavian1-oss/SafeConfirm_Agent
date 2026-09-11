#!/usr/bin/env bash
# Goal C E1 + E6: multi-seed main results and confirm ablation (12-case subset by default).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
SUBSET="${SUBSET:-12}"
SEEDS="${SEEDS:-s0 s1 s2}"

load_workspace_subset_args "${SUBSET}"

for seed in ${SEEDS}; do
  echo "=== E1 main result seed=${seed} subset=${SUBSET} ==="
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
    --logdir "runs/bridge/e2e_deepseek_v3_${seed}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "runs/bridge/e2e_deepseek_v3_s*/safeconfirm_workspace/metrics.json" \
  --output runs/bridge/e2e_deepseek_v3_aggregate.json

CONFIRM_ROOT="runs/bridge/confirm_ablation_v4"
for seed in ${SEEDS}; do
  LOGROOT="${CONFIRM_ROOT}/${seed}"
  mkdir -p "${LOGROOT}"
  for row in "rule_v1 llm_user sa_llm" "baseline_vague llm_user vague_llm"; do
    read -r policy confirmer subdir <<< "${row}"
    echo "=== E6 confirm seed=${seed} ${subdir} ==="
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" \
      -m "${MODEL}" \
      -a parameter_poison \
      --defense safeconfirm \
      --policy "${policy}" \
      --confirmer "${confirmer}" \
      --confirmer-model "${MODEL}" \
      --run-id "${seed}" \
      --logdir "${LOGROOT}/${subdir}" \
      "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
  done
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${CONFIRM_ROOT}/s*/sa_llm/safeconfirm_workspace/metrics.json" \
  --output "${CONFIRM_ROOT}/sa_llm_aggregate.json"
uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${CONFIRM_ROOT}/s*/vague_llm/safeconfirm_workspace/metrics.json" \
  --output "${CONFIRM_ROOT}/vague_llm_aggregate.json"

echo "Done. Multi-seed logs under e2e_deepseek_v3_s* and ${CONFIRM_ROOT}"
