#!/usr/bin/env bash
# E-P1-3: cross-model signature — confirm ablation subset only (not full 28-case).
# Optional / rebuttal: skipped for submission when no second-model API budget (see evidence_strength_plan §3.6).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

PRIMARY_MODEL="${PRIMARY_MODEL:-deepseek-chat}"
SECONDARY_MODEL="${SECONDARY_MODEL:-gpt-4o-mini-2024-07-18}"
SEEDS="${SEEDS:-s0 s1 s2}"
LOGROOT="${LOGROOT:-runs/bridge/cross_model_signature}"
SUBSET="${SUBSET:-12}"
mkdir -p "${LOGROOT}"
load_workspace_subset_args "${SUBSET}"

run_signature() {
  local model="$1"
  local tag="$2"
  local seed="$3"
  for arm in p0 sc; do
    local logdir="${LOGROOT}/${tag}_${arm}_${seed}"
    local -a cmd=(
      uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark
      -s safeconfirm_workspace
      -m "${model}"
      -a parameter_poison
      --run-id "${seed}"
      --seed "${seed#s}"
      --logdir "${logdir}"
      "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
    )
    if [[ "${arm}" == "sc" ]]; then
      cmd+=(--defense safeconfirm --policy rule_v1 --confirmer llm_user --confirmer-model "${model}")
    fi
    echo "=== ${tag} ${arm} seed=${seed} ==="
    "${cmd[@]}"
  done
}

for seed in ${SEEDS}; do
  run_signature "${PRIMARY_MODEL}" primary "${seed}"
  run_signature "${SECONDARY_MODEL}" secondary "${seed}"
done

echo "Signature check: ASR(P0) >= ASR(SC) and SDR/CLR split on vague vs source-aware (see confirm ablation logs)."
echo "Secondary model: ${SECONDARY_MODEL}. Logs: ${LOGROOT}"
