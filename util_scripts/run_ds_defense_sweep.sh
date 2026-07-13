#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
SUITE="safeconfirm_workspace"
MODEL="deepseek-chat"
ATTACK="parameter_poison"

run_one() {
  local name="$1"
  local defense="${2:-}"
  local logdir="runs/bridge/e2e_ds_${name}"
  echo "========== ${name} (defense=${defense:-none}) =========="
  if [[ -z "${defense}" ]]; then
    "${PYTHON}" -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" -m "${MODEL}" -a "${ATTACK}" \
      --logdir "${logdir}"
  else
    "${PYTHON}" -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" -m "${MODEL}" -a "${ATTACK}" \
      --defense "${defense}" \
      --logdir "${logdir}"
  fi
}

run_one p0 ""
run_one spotlighting spotlighting_with_delimiting
run_one repeat repeat_user_prompt
run_one tool_filter tool_filter
if "${PYTHON}" -c "import torch, transformers" 2>/dev/null; then
  run_one pi_detector transformers_pi_detector
else
  echo "Skipping PI detector (install: pip install 'agentdojo[transformers]')"
fi
run_one log_only safeconfirm_log_only
run_one safeconfirm safeconfirm

echo "========== Comparison =========="
"${PYTHON}" -m safeconfirm_bridge.scripts.compare_defenses \
  --run "P0:runs/bridge/e2e_ds_p0/safeconfirm_workspace" \
  --run "Spotlighting:runs/bridge/e2e_ds_spotlighting/safeconfirm_workspace" \
  --run "Repeat prompt:runs/bridge/e2e_ds_repeat/safeconfirm_workspace" \
  --run "Tool filter:runs/bridge/e2e_ds_tool_filter/safeconfirm_workspace" \
  --run "PI detector:runs/bridge/e2e_ds_pi_detector/safeconfirm_workspace" \
  --run "SC log-only:runs/bridge/e2e_ds_log_only/safeconfirm_workspace" \
  --run "SafeConfirm:runs/bridge/e2e_ds_safeconfirm/safeconfirm_workspace" \
  --output runs/bridge/e2e_ds_defense_comparison.json
