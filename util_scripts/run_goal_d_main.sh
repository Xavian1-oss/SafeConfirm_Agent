#!/usr/bin/env bash
# Goal D D2: 20-case main results (16 workspace + 4 banking), DeepSeek, 3 seeds
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
LOG_PREFIX="${LOG_PREFIX:-runs/bridge/e2e_deepseek_v4}"

for seed in ${SEEDS}; do
  echo "=== D2 workspace 16-case seed=${seed} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_workspace \
    -m "${MODEL}" \
    -a parameter_poison \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${LOG_PREFIX}_${seed}"
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${LOG_PREFIX}_s[0-2]/safeconfirm_workspace/metrics.json" \
  --output "${LOG_PREFIX}_workspace_aggregate.json"

echo "=== D2 banking 4-case (single run) ==="
BANKING_LOGROOT="${BANKING_LOGROOT:-runs/bridge/e2e_banking_deepseek_v4}"
uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s safeconfirm_banking \
  -m "${MODEL}" \
  -a parameter_poison \
  --defense safeconfirm \
  --policy rule_v1 \
  --confirmer llm_user \
  --confirmer-model "${MODEL}" \
  --logdir "${BANKING_LOGROOT}"

echo "Done. Workspace aggregate: ${LOG_PREFIX}_workspace_aggregate.json"
echo "Optional: ./util_scripts/run_16case_p0.sh  (undefended 16-case baseline)"
echo "Optional: ./util_scripts/sync_paper_metrics.sh  (archive aggregates to paper_metrics/)"
