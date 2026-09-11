#!/usr/bin/env bash
# D0b: REPAIR ablation on role-reference subset (ground_truth includes REPAIR).
# Workspace user_task_0..4: email supervisor/manager/advisor + share supervisor/client.
set -euo pipefail

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/ablation_repair_subset_v1}"
TASKS=(user_task_0 user_task_1 user_task_2 user_task_3 user_task_4)

UT_FLAGS=()
for t in "${TASKS[@]}"; do
  UT_FLAGS+=(-ut "$t")
done

run_on() {
  echo "=== repair subset ON (${#TASKS[@]} cases) -> ${LOGROOT}/on ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    --suite "${SUITE}" \
    --model "${MODEL}" \
    --attack parameter_poison \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    "${UT_FLAGS[@]}" \
    --logdir "${LOGROOT}/on"
}

run_off() {
  echo "=== repair subset OFF (${#TASKS[@]} cases) -> ${LOGROOT}/off ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    --suite "${SUITE}" \
    --model "${MODEL}" \
    --attack parameter_poison \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    "${UT_FLAGS[@]}" \
    --no-repair \
    --logdir "${LOGROOT}/off"
}

run_on
run_off

for label in on off; do
  echo ""
  echo "=== subset ${label} ==="
  uv run python -c "
import json
from pathlib import Path
p = Path('${LOGROOT}/${label}/${SUITE}/metrics.json')
m = json.loads(p.read_text())
print(f\"TSR={m['tsr']*100:.1f}% ASR={m['asr']*100:.1f}% repair_attempts={m['repair_attempts']} RSR={m['rsr']*100:.1f}%\")
"
done
