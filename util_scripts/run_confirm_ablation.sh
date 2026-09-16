#!/usr/bin/env bash
# Confirm ablation: source-aware vs vague × LLM vs oracle (12-case subset by default).
# Env:
#   SEEDS="s0 s1 s2"   multi-seed LLM rows (oracle stays single-run)
#   LOGROOT=...        output root (default runs/bridge/confirm_ablation_v4)
#   SUBSET=12|16
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
SUBSET="${SUBSET:-12}"
SEEDS="${SEEDS:-}"
LOGROOT="${LOGROOT:-runs/bridge/confirm_ablation_v4}"
mkdir -p "${LOGROOT}"

load_workspace_subset_args "${SUBSET}"

run_row() {
  local policy="$1"
  local confirmer="$2"
  local logdir="$3"
  shift 3
  echo "=== policy=${policy} confirmer=${confirmer} -> ${logdir} ==="
  local -a cmd=(
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark
    --suite "${SUITE}"
    --model "${MODEL}"
    --attack parameter_poison
    --defense safeconfirm
    --policy "${policy}"
    --confirmer "${confirmer}"
    --logdir "${logdir}"
  )
  if [[ "${confirmer}" == "llm_user" || "${confirmer}" == "compliant_llm" ]]; then
    cmd+=(--confirmer-model "${MODEL}")
  fi
  if ((${#SUBSET_ARGS[@]})); then
    cmd+=("${SUBSET_ARGS[@]}")
  fi
  if (("$#")); then
    cmd+=("$@")
  fi
  "${cmd[@]}"
}

if [[ -n "${SEEDS}" ]]; then
  for seed in ${SEEDS}; do
    seed_dir="${LOGROOT}/${seed}"
    run_row rule_v1 llm_user "${seed_dir}/sa_llm" --run-id "${seed}" --seed "${seed#s}"
    run_row baseline_vague llm_user "${seed_dir}/vague_llm" --run-id "${seed}" --seed "${seed#s}"
  done
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/s[0-9]/sa_llm/${SUITE}/metrics.json" \
    --output "${LOGROOT}/sa_llm_aggregate.json"
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/s[0-9]/vague_llm/${SUITE}/metrics.json" \
    --output "${LOGROOT}/vague_llm_aggregate.json"
else
  run_row rule_v1 llm_user "${LOGROOT}/sa_llm"
  run_row baseline_vague llm_user "${LOGROOT}/vague_llm"
fi

run_row rule_v1 oracle_strict "${LOGROOT}/sa_oracle"
run_row baseline_vague oracle_strict "${LOGROOT}/vague_oracle"

if [[ "${COMPLIANT_VAGUE:-}" == "1" ]]; then
  if [[ -n "${SEEDS}" ]]; then
    for seed in ${SEEDS}; do
      seed_dir="${LOGROOT}/${seed}"
      run_row baseline_vague compliant_llm "${seed_dir}/vague_compliant_llm" --run-id "${seed}" --seed "${seed#s}"
    done
    uv run python util_scripts/aggregate_seed_metrics.py \
      --pattern "${LOGROOT}/s[0-9]/vague_compliant_llm/${SUITE}/metrics.json" \
      --output "${LOGROOT}/vague_compliant_llm_aggregate.json"
  else
    run_row baseline_vague compliant_llm "${LOGROOT}/vague_compliant_llm"
  fi
fi

uv run python util_scripts/compare_confirm_ablation.py --logroot "${LOGROOT}"

echo "Done. Confirm ablation under ${LOGROOT} (subset=${SUBSET}, seeds=${SEEDS:-single-run})"
