#!/usr/bin/env bash
# E-P0-2: banking benign-only diagnostic (P0 arm, no SafeConfirm).
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0}"
LOGROOT="${LOGROOT:-runs/bridge/banking_benign_check}"

mkdir -p "${LOGROOT}"

for seed in ${SEEDS}; do
  logdir="${LOGROOT}/p0_${seed}"
  echo "=== banking benign check seed=${seed} -> ${logdir} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_banking \
    -m "${MODEL}" \
    -a parameter_poison \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${logdir}" \
    -ut user_task_5
done

echo "Benign case is user_task_5 (bk_transfer_benign_explicit_e2e). See ${LOGROOT}/"
