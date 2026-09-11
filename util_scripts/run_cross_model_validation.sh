#!/usr/bin/env bash
# Optional cross-model validation on ~50-60% of benchmark cases (rebuttal / revision).
# Primary submission uses DeepSeek-only; run this only when a second model is needed.
#
# Usage:
#   CROSS_MODEL=gemini-1.5-pro-001 ./util_scripts/run_cross_model_validation.sh
#   CROSS_MODEL=gpt-4o-2024-05-13 SUBSET=workspace_corruption_10 ./util_scripts/run_cross_model_validation.sh
set -euo pipefail
cd "$(dirname "$0")/.."

CROSS_MODEL="${CROSS_MODEL:?Set CROSS_MODEL to an AgentDojo ModelsEnum value}"
SUBSET="${SUBSET:-workspace_corruption_8}"
LOGROOT="${LOGROOT:-runs/cross_model/${CROSS_MODEL}}"
mkdir -p "${LOGROOT}"

# user_task indices for corruption cases (see benchmark_cases_e2e.yaml order)
# 8 cases ≈ 50% of full 16-case benchmark; 10 cases ≈ 62%
WS_CORRUPTION_8=(user_task_{0..7})
WS_CORRUPTION_10=(user_task_{0..9})

case "${SUBSET}" in
  workspace_corruption_8) TASKS=("${WS_CORRUPTION_8[@]}") ;;
  workspace_corruption_10) TASKS=("${WS_CORRUPTION_10[@]}") ;;
  full) TASKS=() ;;
  *) echo "Unknown SUBSET=${SUBSET}" >&2; exit 1 ;;
esac

SUITE=safeconfirm_workspace
ut_args=()
if ((${#TASKS[@]})); then
  for t in "${TASKS[@]}"; do ut_args+=(-ut "${t}"); done
fi

echo "=== ${CROSS_MODEL} SafeConfirm (subset=${SUBSET}, n=${#TASKS[@]:-full}) ==="
uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s "${SUITE}" -m "${CROSS_MODEL}" -a parameter_poison \
  --defense safeconfirm --policy rule_v1 \
  --confirmer llm_user --confirmer-model "${CROSS_MODEL}" \
  "${ut_args[@]}" --logdir "${LOGROOT}/safeconfirm"

echo "=== ${CROSS_MODEL} P0 baseline ==="
uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s "${SUITE}" -m "${CROSS_MODEL}" -a parameter_poison \
  "${ut_args[@]}" --logdir "${LOGROOT}/p0"

echo "Done. Logs: ${LOGROOT}/{safeconfirm,p0}"
