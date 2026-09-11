#!/usr/bin/env bash
# P0 on the 12-case workspace subset (user_task_0..11), three seeds.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
LOG_PREFIX="${LOG_PREFIX:-runs/bridge/e2e_p0_v3}"

load_workspace_subset_args 12

for seed in ${SEEDS}; do
  echo "=== P0 12-case seed=${seed} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_workspace \
    -m "${MODEL}" \
    -a parameter_poison \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${LOG_PREFIX}_${seed}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${LOG_PREFIX}_s[0-2]/safeconfirm_workspace/metrics.json" \
  --output "${LOG_PREFIX}_aggregate.json"

echo "Done. Aggregate: ${LOG_PREFIX}_aggregate.json"
