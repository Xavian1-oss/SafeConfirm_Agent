#!/usr/bin/env bash
# Smoke wrapper: 10 native workspace tasks → full native evaluation matrix.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export NATIVE_LOGROOT="${NATIVE_LOGROOT:-runs/native_gen/ds_v1}"
export NATIVE_USER_TASKS="${NATIVE_USER_TASKS:--ut user_task_0 -ut user_task_1 -ut user_task_2 -ut user_task_3 -ut user_task_4 -ut user_task_5 -ut user_task_6 -ut user_task_7 -ut user_task_8 -ut user_task_9}"

exec "$ROOT/util_scripts/run_native_evaluation.sh"
