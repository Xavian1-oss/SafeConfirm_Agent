#!/usr/bin/env bash
# Component ablation: baseline_allow / baseline_block / rule_v1 on 12-case subset.
# Env:
#   SEEDS="s0 s1 s2"   default three seeds
#   LOGROOT=...        output root
#   SUBSET=12|16
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/component_ablation}"
MODEL="${DS_MODEL:-deepseek-chat}"
SUBSET="${SUBSET:-12}"
SEEDS="${SEEDS:-s0 s1 s2}"
mkdir -p "${LOGROOT}"

load_workspace_subset_args "${SUBSET}"

run_one() {
  local policy="$1"
  local logdir="$2"
  shift 2
  echo "=== model=${MODEL} policy=${policy} subset=${SUBSET} -> ${logdir} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s "${SUITE}" \
    -m "${MODEL}" \
    -a parameter_poison \
    --defense safeconfirm \
    --policy "${policy}" \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --logdir "${logdir}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}" \
    "$@"
}

for seed in ${SEEDS}; do
  run_one baseline_allow "${LOGROOT}/allow_ds_${seed}" --run-id "${seed}" --seed "${seed#s}"
  run_one baseline_block "${LOGROOT}/block_ds_${seed}" --run-id "${seed}" --seed "${seed#s}"
  run_one rule_v1 "${LOGROOT}/sc_ds_${seed}" --run-id "${seed}" --seed "${seed#s}"
done

uv run python util_scripts/compare_component_ablation.py \
  --logroot "${LOGROOT}" \
  --output "${LOGROOT}/summary.json"

echo "Done. Component ablation logs under ${LOGROOT} (subset=${SUBSET}, seeds=${SEEDS})"
