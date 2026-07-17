#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
MODEL="gpt-4o-2024-05-13"
ATTACK="parameter_poison"

run_suite() {
  local suite="$1"
  local logdir="$2"
  echo "========== GPT-4o ${suite} -> ${logdir} =========="
  "${PYTHON}" -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s "${suite}" -m "${MODEL}" -a "${ATTACK}" \
    --defense safeconfirm --policy rule_v1 \
    --logdir "${logdir}"
}

run_suite safeconfirm_workspace "runs/bridge/e2e_gpt4o_v2"
run_suite safeconfirm_banking "runs/bridge/e2e_gpt4o_banking_v3"

echo "Done. Logs under runs/bridge/e2e_gpt4o_v2 and e2e_gpt4o_banking_v3"
