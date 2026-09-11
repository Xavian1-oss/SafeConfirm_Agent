#!/usr/bin/env bash
# Route A: paired P0 + SafeConfirm rerun in one batch (same model, subset, seeds).
# Goal: P0 ASR > 0 and SafeConfirm ASR ≈ 0 under identical conditions.
#
# Recommended workflow:
#   1. ./util_scripts/run_pilot_asr_check.sh          # verify P0 ASR > 0 first
#   2. ./util_scripts/run_paired_security_rerun.sh    # full paired rerun
#   3. ./util_scripts/sync_paper_metrics.sh           # archive aggregates
#
# Env:
#   SUBSET=12|16          workspace cases (default 12 — Jul batch had 60% P0 ASR here)
#   SEEDS="s0 s1 s2"      seed labels (stored in metrics; LLM seed not wired yet)
#   TEMPERATURE=0.7       optional agent temperature for P0+SC (same for both arms)
#   BATCH_ID=20260910     output folder name (default: timestamp)
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SUBSET="${SUBSET:-12}"
SEEDS="${SEEDS:-s0 s1 s2}"
TEMPERATURE="${TEMPERATURE:-}"
BATCH_ID="${BATCH_ID:-$(date +%Y%m%d_%H%M%S)}"
LOGROOT="${LOGROOT:-runs/bridge/paired_security_${BATCH_ID}}"

load_workspace_subset_args "${SUBSET}"

TEMP_ARGS=()
if [[ -n "${TEMPERATURE}" ]]; then
  TEMP_ARGS=(--temperature "${TEMPERATURE}")
fi

mkdir -p "${LOGROOT}"
TEMP_JSON="null"
if [[ -n "${TEMPERATURE}" ]]; then
  TEMP_JSON="${TEMPERATURE}"
fi
cat > "${LOGROOT}/batch_meta.json" <<EOF
{
  "batch_id": "${BATCH_ID}",
  "model": "${MODEL}",
  "subset": "${SUBSET}",
  "seeds": "${SEEDS}",
  "temperature": ${TEMP_JSON},
  "started_at": "$(date -Iseconds)",
  "goal": "P0 ASR > 0, SafeConfirm ASR ≈ 0, same batch"
}
EOF

run_arm() {
  local arm="$1"
  local seed="$2"
  local logdir="${LOGROOT}/${arm}_${seed}"
  shift 2
  echo "=== ${arm} seed=${seed} subset=${SUBSET} -> ${logdir} ==="
  local -a cmd=(
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark
    -s safeconfirm_workspace
    -m "${MODEL}"
    -a parameter_poison
    --run-id "${seed}"
    --seed "${seed#s}"
    --logdir "${logdir}"
  )
  if ((${#TEMP_ARGS[@]})); then
    cmd+=("${TEMP_ARGS[@]}")
  fi
  if ((${#SUBSET_ARGS[@]})); then
    cmd+=("${SUBSET_ARGS[@]}")
  fi
  if (("$#")); then
    cmd+=("$@")
  fi
  "${cmd[@]}"
}

for seed in ${SEEDS}; do
  run_arm p0 "${seed}" 
  run_arm sc "${seed}" \
    --defense safeconfirm \
    --policy rule_v1 \
    --confirmer llm_user \
    --confirmer-model "${MODEL}"
done

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${LOGROOT}/p0_s[0-9]/safeconfirm_workspace/metrics.json" \
  --output "${LOGROOT}/p0_aggregate.json"

uv run python util_scripts/aggregate_seed_metrics.py \
  --pattern "${LOGROOT}/sc_s[0-9]/safeconfirm_workspace/metrics.json" \
  --output "${LOGROOT}/sc_aggregate.json"

uv run python util_scripts/compare_paired_security_rerun.py \
  --p0 "${LOGROOT}/p0_aggregate.json" \
  --sc "${LOGROOT}/sc_aggregate.json" \
  --meta "${LOGROOT}/batch_meta.json" \
  --output "${LOGROOT}/paired_comparison.json"

echo ""
echo "Done. Batch: ${LOGROOT}"
echo "  P0 aggregate: ${LOGROOT}/p0_aggregate.json"
echo "  SC aggregate: ${LOGROOT}/sc_aggregate.json"
echo "  Comparison:   ${LOGROOT}/paired_comparison.json"
echo ""
echo "If P0 ASR > 0 and SC ASR ≈ 0, update paper Table 3 from this batch and footnote Sep-2026 variance."
