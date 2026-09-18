#!/usr/bin/env bash
# E-P0-3: provenance-only baselines on 28-case (or SUBSET) suite.
# Paper names: provenance_block = baseline_block, provenance_vague = baseline_vague.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/provenance_baselines}"
MODEL="${MODEL:-deepseek-chat}"
SUBSET="${SUBSET:-12}"
SEEDS="${SEEDS:-s0 s1 s2}"
mkdir -p "${LOGROOT}"

load_workspace_subset_args "${SUBSET}"

run_policy() {
  local policy="$1"
  local seed="$2"
  local logdir="${LOGROOT}/${policy}_${seed}"
  echo "=== provenance baseline policy=${policy} seed=${seed} -> ${logdir} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s "${SUITE}" \
    -m "${MODEL}" \
    -a parameter_poison \
    --defense safeconfirm \
    --policy "${policy}" \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${logdir}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
}

for seed in ${SEEDS}; do
  run_policy baseline_block "${seed}"
  run_policy baseline_vague "${seed}"
  run_policy rule_v1 "${seed}"
done

echo "Compare SDR/CLR: block (utility↓) vs vague (CLR↑) vs rule_v1 (SDR↑, CLR↓)."
echo "Logs under ${LOGROOT}"
