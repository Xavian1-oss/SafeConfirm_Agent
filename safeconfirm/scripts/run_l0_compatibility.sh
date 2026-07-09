#!/usr/bin/env bash
# L0: AgentDojo utility compatibility — P0 (no defense) vs safeconfirm_log_only
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from template first:"
  echo "  cp .env.example .env"
  echo "Then set OPENAI_API_KEY in .env"
  exit 1
fi

MODEL="${L0_MODEL:-GPT_4O_MINI_2024_07_18}"
SUITE="${L0_SUITE:-workspace}"
BENCH_VERSION="${L0_BENCH_VERSION:-v1.2.2}"
LOGROOT="${L0_LOGROOT:-runs/l0}"
# Smoke: export L0_USER_TASKS="-ut user_task_0 -ut user_task_1"
USER_TASKS=${L0_USER_TASKS:-}

BASELINE_LOG="${LOGROOT}/p0_baseline"
LOGONLY_LOG="${LOGROOT}/p0_safeconfirm_log_only"

mkdir -p "$LOGROOT"

echo "=== L0 Phase 1/2: P0 baseline (no defense) ==="
.venv/bin/python -m agentdojo.scripts.benchmark \
  --model "$MODEL" \
  -s "$SUITE" \
  $USER_TASKS \
  --benchmark-version "$BENCH_VERSION" \
  --logdir "$BASELINE_LOG"

echo ""
echo "=== L0 Phase 2/2: safeconfirm_log_only (passive) ==="
.venv/bin/python -m agentdojo.scripts.benchmark \
  --model "$MODEL" \
  -s "$SUITE" \
  $USER_TASKS \
  --defense safeconfirm_log_only \
  --benchmark-version "$BENCH_VERSION" \
  --logdir "$LOGONLY_LOG"

echo ""
echo "=== L0 comparison ==="
.venv/bin/python safeconfirm/scripts/compare_l0_utility.py \
  --baseline "$BASELINE_LOG" \
  --candidate "$LOGONLY_LOG" \
  --tolerance 0.02
