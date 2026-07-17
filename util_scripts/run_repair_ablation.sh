#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/ablation_repair}"

run_on() {
  echo "=== repair ON (model=${MODEL}) -> ${LOGROOT}/on ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    --suite "${SUITE}" \
    --model "${MODEL}" \
    --attack parameter_poison \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --logdir "${LOGROOT}/on"
}

run_off() {
  echo "=== repair OFF (model=${MODEL}) -> ${LOGROOT}/off ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    --suite "${SUITE}" \
    --model "${MODEL}" \
    --attack parameter_poison \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --no-repair \
    --logdir "${LOGROOT}/off"
}

run_on
run_off

for label in on off; do
  echo ""
  echo "=== repair ${label} ==="
  uv run python -c "
import json
from pathlib import Path
p = Path('${LOGROOT}/${label}/${SUITE}/metrics.json')
m = json.loads(p.read_text())
print(f\"TSR={m['tsr']*100:.1f}% ASR={m['asr']*100:.1f}% RSR={m['rsr']*100:.1f}% UAR={m['uar']*100:.1f}% Stall={m['stall_rate']*100:.1f}% Composite={m['composite']*100:.1f}%\")
"
done
