#!/usr/bin/env bash
# P0 (no defense) baseline on the 16-case workspace suite — fills the main-table gap.
# Optional but recommended for rebuttal: compares undefended utility on the expanded suite.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
LOG_PREFIX="${LOG_PREFIX:-runs/bridge/e2e_p0_v4}"

for seed in ${SEEDS}; do
  echo "=== P0 workspace 16-case seed=${seed} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_workspace \
    -m "${MODEL}" \
    -a parameter_poison \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${LOG_PREFIX}_${seed}"
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${LOG_PREFIX}_s[0-2]/safeconfirm_workspace/metrics.json" \
  --output "${LOG_PREFIX}_workspace_aggregate.json"

echo "Done. Aggregate: ${LOG_PREFIX}_workspace_aggregate.json"
