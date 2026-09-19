#!/usr/bin/env bash
# Goal C master runner: blocker experiments (12-case ablation + L0 + multi-seed).
# For primary E2E (28-case), run ./util_scripts/run_extended_28case.sh separately.
set -euo pipefail
cd "$(dirname "$0")/.."

LOGROOT="runs/bridge/goal_c_master"
mkdir -p "${LOGROOT}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOGROOT}/master.log"
}

run_step() {
  local name="$1"
  shift
  log "START ${name}"
  if "$@" >> "${LOGROOT}/master.log" 2>&1; then
    log "DONE ${name}"
  else
    log "FAILED ${name} (exit $?)"
    exit 1
  fi
}

log "Goal C experiment batch starting (DeepSeek-only)"

run_step "E4-E5 component ablation (DeepSeek)" ./util_scripts/run_component_ablation.sh
run_step "E10 L0 compatibility (DeepSeek)" env L0_MODEL=deepseek-chat L0_LOGROOT=runs/l0/goal_c_v1_ds_full ./safeconfirm/scripts/run_l0_compatibility.sh
run_step "E1+E6 multi-seed" ./util_scripts/run_goal_c_multiseed.sh

log "Goal C experiment batch complete"
log "Primary E2E (28-case): ./util_scripts/run_extended_28case.sh"
log "Optional cross-model: SECONDARY_MODEL=... ./util_scripts/run_cross_model_signature.sh"
