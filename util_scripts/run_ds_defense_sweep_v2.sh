#!/usr/bin/env bash
# AgentDojo defense sweep on the 12-case workspace subset (Appendix Table tab:defense).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

if [[ -n "${PYTHON:-}" ]]; then
  read -r -a PYTHON_CMD <<< "${PYTHON}"
else
  PYTHON_CMD=(uv run python)
fi
SUITE="safeconfirm_workspace"
MODEL="deepseek-chat"
ATTACK="parameter_poison"
LOGROOT="${LOGROOT:-runs/bridge/e2e_ds_v2}"
COMPARE_OUTPUT="${COMPARE_OUTPUT:-runs/bridge/e2e_ds_v2_defense_comparison.json}"
SUBSET="${SUBSET:-12}"

load_workspace_subset_args "${SUBSET}"

run_one() {
  local name="$1"
  local defense="${2:-}"
  shift 2 || true
  local logdir="${LOGROOT}_${name}"
  echo "========== ${name} (defense=${defense:-none}) =========="
  if [[ -z "${defense}" ]]; then
    "${PYTHON_CMD[@]}" -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" -m "${MODEL}" -a "${ATTACK}" \
      --logdir "${logdir}" "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}" "$@"
  else
    "${PYTHON_CMD[@]}" -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      -s "${SUITE}" -m "${MODEL}" -a "${ATTACK}" \
      --defense "${defense}" \
      --logdir "${logdir}" "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}" "$@"
  fi
}

run_one p0 ""
run_one spotlighting spotlighting_with_delimiting
run_one repeat repeat_user_prompt
run_one tool_filter tool_filter
if "${PYTHON_CMD[@]}" -c "import torch, transformers" 2>/dev/null; then
  run_one pi_detector transformers_pi_detector
else
  echo "Skipping PI detector (install: pip install 'agentdojo[transformers]')"
fi
run_one log_only safeconfirm_log_only
run_one safeconfirm safeconfirm --policy rule_v1

echo "========== Comparison =========="
COMPARE_ARGS=(
  --run "P0:${LOGROOT}_p0/safeconfirm_workspace"
  --run "Spotlighting:${LOGROOT}_spotlighting/safeconfirm_workspace"
  --run "Repeat prompt:${LOGROOT}_repeat/safeconfirm_workspace"
  --run "Tool filter:${LOGROOT}_tool_filter/safeconfirm_workspace"
)
if [[ -f "${LOGROOT}_pi_detector/safeconfirm_workspace/metrics.json" ]]; then
  COMPARE_ARGS+=(--run "PI detector:${LOGROOT}_pi_detector/safeconfirm_workspace")
fi
COMPARE_ARGS+=(
  --run "SC log-only:${LOGROOT}_log_only/safeconfirm_workspace"
  --run "SafeConfirm:${LOGROOT}_safeconfirm/safeconfirm_workspace"
  --output "${COMPARE_OUTPUT}"
)
"${PYTHON_CMD[@]}" -m safeconfirm_bridge.scripts.compare_defenses "${COMPARE_ARGS[@]}"
