#!/usr/bin/env bash
# Native AgentDojo workspace eval (non-SafeConfirm cases) — P0 vs SafeConfirm.
# Addresses external validity: same defense on AgentDojo's own tasks + attacks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODEL="${NATIVE_MODEL:-deepseek-chat}"
SUITE="${NATIVE_SUITE:-workspace}"
BENCH_VERSION="${NATIVE_BENCH_VERSION:-v1.2.2}"
ATTACK="${NATIVE_ATTACK:-tool_knowledge}"
LOGROOT="${NATIVE_LOGROOT:-runs/native_gen/ds_v1}"
# Subset smoke (default: 10 native workspace tasks); override with NATIVE_USER_TASKS=
DEFAULT_NATIVE_UT="-ut user_task_0 -ut user_task_1 -ut user_task_2 -ut user_task_3 -ut user_task_4 -ut user_task_5 -ut user_task_6 -ut user_task_7 -ut user_task_8 -ut user_task_9"
USER_TASKS=${NATIVE_USER_TASKS:-$DEFAULT_NATIVE_UT}

mkdir -p "$LOGROOT"

echo "=== Native generalization: P0 + ${ATTACK} (${MODEL}) ==="
uv run python -m agentdojo.scripts.benchmark \
  --model "$MODEL" \
  -s "$SUITE" \
  $USER_TASKS \
  --benchmark-version "$BENCH_VERSION" \
  --attack "$ATTACK" \
  --logdir "${LOGROOT}/p0_${ATTACK}"

echo ""
echo "=== Native generalization: SafeConfirm + ${ATTACK} (${MODEL}) ==="
uv run python -m agentdojo.scripts.benchmark \
  --model "$MODEL" \
  -s "$SUITE" \
  $USER_TASKS \
  --benchmark-version "$BENCH_VERSION" \
  --attack "$ATTACK" \
  --defense safeconfirm \
  --logdir "${LOGROOT}/safeconfirm_${ATTACK}"

echo ""
echo "=== Summary (utility / security from logdirs) ==="
for d in "${LOGROOT}/p0_${ATTACK}" "${LOGROOT}/safeconfirm_${ATTACK}"; do
  echo "--- $d ---"
  uv run python - <<PY
import json
from pathlib import Path
logdir = Path("$d")
utilities, securities = [], []
for path in logdir.rglob("*.json"):
    raw = json.loads(path.read_text())
    if "utility" in raw:
        utilities.append(bool(raw["utility"]))
    if "security" in raw:
        securities.append(bool(raw["security"]))
if utilities:
    print(f"  utility: {sum(utilities)/len(utilities)*100:.1f}% ({sum(utilities)}/{len(utilities)})")
if securities:
    print(f"  security: {sum(securities)/len(securities)*100:.1f}% ({sum(securities)}/{len(securities)})")
PY
done
