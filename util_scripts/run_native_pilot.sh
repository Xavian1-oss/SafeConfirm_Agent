#!/usr/bin/env bash
# Minimal native eval smoke: 1 user task × 2 injection tasks × 4 defenses (~8 trajectories).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export NATIVE_LOGROOT="runs/native_eval/pilot"
export NATIVE_USER_TASKS="${NATIVE_USER_TASKS:--ut user_task_0}"
export NATIVE_INJECTION_TASKS="${NATIVE_INJECTION_TASKS:--it injection_task_0 -it injection_task_1}"
export NATIVE_FORCE_RERUN=1
export SAFECONFIRM_CONFIRMER="${SAFECONFIRM_CONFIRMER:-oracle_strict}"

exec "$ROOT/util_scripts/run_native_evaluation.sh"
