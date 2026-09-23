#!/usr/bin/env bash
# Native AgentDojo evaluation matrix: P0, Block, Vague, SafeConfirm (frozen policy via env).
# After runs, aggregates utility/security (whole suite + binding subset), SDR/CLR, and coverage.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODEL="${NATIVE_MODEL:-deepseek-chat}"
SUITE="${NATIVE_SUITE:-workspace}"
BENCH_VERSION="${NATIVE_BENCH_VERSION:-v1.2.2}"
ATTACK="${NATIVE_ATTACK:-tool_knowledge}"
LOGROOT="${NATIVE_LOGROOT:-runs/native_eval/latest}"
DRY_RUN="${NATIVE_DRY_RUN:-0}"
FORCE_RERUN="${NATIVE_FORCE_RERUN:-0}"
# oracle_strict avoids extra LLM confirmer calls during native matrix runs
export SAFECONFIRM_CONFIRMER="${SAFECONFIRM_CONFIRMER:-oracle_strict}"

USER_TASK_ARGS=()
if [[ -n "${NATIVE_USER_TASKS:-}" ]]; then
  # shellcheck disable=SC2206
  USER_TASK_ARGS=($NATIVE_USER_TASKS)
fi
INJECTION_TASK_ARGS=()
if [[ -n "${NATIVE_INJECTION_TASKS:-}" ]]; then
  # shellcheck disable=SC2206
  INJECTION_TASK_ARGS=($NATIVE_INJECTION_TASKS)
fi

mkdir -p "$LOGROOT"

run_benchmark() {
  local label=$1
  local defense=$2
  local policy=$3
  local out="${LOGROOT}/${label}"
  mkdir -p "$out"

  local -a cmd=(
    uv run python -m agentdojo.scripts.benchmark
    --model "$MODEL"
    -s "$SUITE"
    --benchmark-version "$BENCH_VERSION"
    --attack "$ATTACK"
    --logdir "$out"
  )
  if ((${#USER_TASK_ARGS[@]})); then
    cmd+=("${USER_TASK_ARGS[@]}")
  fi
  if ((${#INJECTION_TASK_ARGS[@]})); then
    cmd+=("${INJECTION_TASK_ARGS[@]}")
  fi
  if [[ "$FORCE_RERUN" == "1" ]]; then
    cmd+=(--force-rerun)
  fi
  if [[ -n "$defense" ]]; then
    cmd+=(--defense "$defense")
  fi

  echo "=== ${label} (defense=${defense:-none}, SAFECONFIRM_POLICY=${policy:-default}) → ${out} ==="
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "(dry run) SAFECONFIRM_POLICY=${policy:-} ${cmd[*]}"
    return 0
  fi
  if [[ -n "$policy" ]]; then
    SAFECONFIRM_POLICY="$policy" "${cmd[@]}"
  else
    "${cmd[@]}"
  fi
}

run_benchmark P0 "" ""
run_benchmark Block safeconfirm baseline_block
run_benchmark Vague safeconfirm baseline_vague
run_benchmark SafeConfirm safeconfirm rule_v1

REPORT="${LOGROOT}/native_comparison.json"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "(dry run) skip aggregate"
  exit 0
fi

uv run python util_scripts/aggregate_native_evaluation.py \
  --run "P0:${LOGROOT}/P0" \
  --run "Block:${LOGROOT}/Block" \
  --run "Vague:${LOGROOT}/Vague" \
  --run "SafeConfirm:${LOGROOT}/SafeConfirm" \
  --output "$REPORT"

echo ""
echo "Report: $REPORT"
