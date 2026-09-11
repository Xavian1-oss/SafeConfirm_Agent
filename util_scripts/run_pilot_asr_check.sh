#!/usr/bin/env bash
# Quick ASR pilot: 6 corruption cases that succeeded under Jul-2026 P0 (12-case subset).
# Use before the full paired rerun to verify the current API batch gives P0 ASR > 0.
#
# Usage:
#   ./util_scripts/run_pilot_asr_check.sh
#   TEMPERATURE=0.7 ./util_scripts/run_pilot_asr_check.sh
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
TEMPERATURE="${TEMPERATURE:-}"
LOGROOT="${LOGROOT:-runs/bridge/pilot_asr_check}"
BATCH_ID="${BATCH_ID:-$(date +%Y%m%d_%H%M%S)}"
LOGDIR="${LOGROOT}/${BATCH_ID}_p0"

# Jul-2026 P0 attack-success cases (user_task_0,1,2,4,8,9)
PILOT_UT_ARGS=(
  -ut user_task_0 -ut user_task_1 -ut user_task_2
  -ut user_task_4 -ut user_task_8 -ut user_task_9
)

TEMP_ARGS=()
if [[ -n "${TEMPERATURE}" ]]; then
  TEMP_ARGS=(--temperature "${TEMPERATURE}")
fi

mkdir -p "${LOGROOT}"
echo "=== ASR pilot batch=${BATCH_ID} model=${MODEL} temperature=${TEMPERATURE:-default} ==="

if ((${#TEMP_ARGS[@]})); then
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_workspace \
    -m "${MODEL}" \
    -a parameter_poison \
    --logdir "${LOGDIR}" \
    "${TEMP_ARGS[@]}" \
    "${PILOT_UT_ARGS[@]}"
else
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s safeconfirm_workspace \
    -m "${MODEL}" \
    -a parameter_poison \
    --logdir "${LOGDIR}" \
    "${PILOT_UT_ARGS[@]}"
fi

uv run python util_scripts/analyze_per_case.py --logdir "${LOGDIR}/safeconfirm_workspace"

METRICS="${LOGDIR}/safeconfirm_workspace/metrics.json"
ASR=$(uv run python -c "import json; m=json.load(open('${METRICS}')); print(f\"{m['asr']*100:.1f}\")")
STALL=$(uv run python -c "import json; m=json.load(open('${METRICS}')); print(f\"{m['stall_rate']*100:.1f}\")")

echo ""
echo "Pilot result: ASR=${ASR}% | Stall=${STALL}%"
echo "Per-case: ${LOGDIR}/safeconfirm_workspace/per_case_summary.json"
if uv run python -c "import json; m=json.load(open('${METRICS}')); exit(0 if m['asr'] > 0 else 1)"; then
  echo "OK: non-zero ASR — proceed with ./util_scripts/run_paired_security_rerun.sh BATCH_ID=${BATCH_ID}"
else
  echo "WARN: ASR still 0%. Try TEMPERATURE=0.7 or TEMPERATURE=1.0, or rerun on another day."
fi
