#!/usr/bin/env bash
# Native external validation — formal v1 (whole workspace × all injections × 4 defenses, single run).
# Configuration is frozen in safeconfirm/spec/native_evaluation.md (native-eval-v1).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
export NATIVE_LOGROOT="${NATIVE_LOGROOT:-runs/native_eval/formal_v1_${COMMIT}}"
export NATIVE_SUITE=workspace
export NATIVE_BENCH_VERSION=v1.2.2
export NATIVE_ATTACK=tool_knowledge
export NATIVE_MODEL="${NATIVE_MODEL:-deepseek-chat}"
export SAFECONFIRM_CONFIRMER=oracle_strict
export NATIVE_FORCE_RERUN=1
# Full task sets: omit NATIVE_USER_TASKS / NATIVE_INJECTION_TASKS → AgentDojo runs all tasks in suite.

exec "$ROOT/util_scripts/run_native_evaluation.sh"
