#!/usr/bin/env bash
# Shared workspace benchmark subsets for SafeConfirm bridge runs.
#
# Usage (from another script):
#   source "$(dirname "$0")/benchmark_subsets.sh"
#   run_bridge ... "${WORKSPACE_12_UT_ARGS[@]}"
#
# The 12-case subset is the first 12 workspace cases in benchmark_cases_e2e.yaml
# (user_task_0 .. user_task_11), frozen before the Goal D v4 extension (+4 cases).

# shellcheck disable=SC2034
WORKSPACE_12_UT_ARGS=(
  -ut user_task_0 -ut user_task_1 -ut user_task_2 -ut user_task_3
  -ut user_task_4 -ut user_task_5 -ut user_task_6 -ut user_task_7
  -ut user_task_8 -ut user_task_9 -ut user_task_10 -ut user_task_11
)

workspace_subset_args() {
  local subset="${1:-full}"
  case "${subset}" in
    12 | ws12 | workspace_12)
      printf '%s\n' "${WORKSPACE_12_UT_ARGS[@]}"
      ;;
    full | 16 | ws16 | workspace_16 | "")
      ;;
    *)
      echo "Unknown workspace subset: ${subset} (use 12 or full)" >&2
      return 1
      ;;
  esac
}

# Populate SUBSET_ARGS array (bash 3.2 compatible; no mapfile).
# When SUBSET is full/16, SUBSET_ARGS stays empty (all workspace cases). Under `set -u`,
# expand with: "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}" instead of "${SUBSET_ARGS[@]}".
load_workspace_subset_args() {
  local subset="${1:-full}"
  SUBSET_ARGS=()
  case "${subset}" in
    12 | ws12 | workspace_12)
      SUBSET_ARGS=("${WORKSPACE_12_UT_ARGS[@]}")
      ;;
    full | 16 | ws16 | workspace_16 | "")
      ;;
    *)
      echo "Unknown workspace subset: ${subset} (use 12 or full)" >&2
      return 1
      ;;
  esac
}
