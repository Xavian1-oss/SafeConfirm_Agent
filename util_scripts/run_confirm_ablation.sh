#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
LOGROOT="${LOGROOT:-runs/bridge/confirm_ablation_v3}"
mkdir -p "${LOGROOT}"

run_row() {
  local policy="$1"
  local confirmer="$2"
  local logdir="$3"
  echo "=== policy=${policy} confirmer=${confirmer} -> ${logdir} ==="
  if [[ "${confirmer}" == "llm_user" ]]; then
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      --suite "${SUITE}" \
      --model "${MODEL}" \
      --attack parameter_poison \
      --defense safeconfirm \
      --policy "${policy}" \
      --confirmer "${confirmer}" \
      --confirmer-model "${MODEL}" \
      --logdir "${logdir}"
  else
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
      --suite "${SUITE}" \
      --model "${MODEL}" \
      --attack parameter_poison \
      --defense safeconfirm \
      --policy "${policy}" \
      --confirmer "${confirmer}" \
      --logdir "${logdir}"
  fi
}

run_row rule_v1 llm_user "${LOGROOT}/sa_llm"
run_row baseline_vague llm_user "${LOGROOT}/vague_llm"
run_row rule_v1 oracle_strict "${LOGROOT}/sa_oracle"
run_row baseline_vague oracle_strict "${LOGROOT}/vague_oracle"

uv run python util_scripts/compare_confirm_ablation.py --logroot "${LOGROOT}"
