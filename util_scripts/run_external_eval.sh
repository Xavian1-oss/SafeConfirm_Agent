#!/usr/bin/env bash
# E-P0-1: AgentDojo-lineage external suite — paired P0 vs SafeConfirm, 3 seeds default.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
# v2 = 12-case external lineage (benchmark_cases_external.yaml)
BATCH_ID="${BATCH_ID:-external_v2_12case_$(date +%Y%m%d)}"
LOGROOT="${LOGROOT:-runs/bridge/${BATCH_ID}}"
SUITE="safeconfirm_workspace_external"

run_arm() {
  local arm="$1"
  local seed="$2"
  local logdir="${LOGROOT}/${arm}_${seed}"
  echo "=== ${SUITE} ${arm} seed=${seed} -> ${logdir} ==="
  local -a cmd=(
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark
    -s "${SUITE}"
    -m "${MODEL}"
    -a parameter_poison
    --run-id "${seed}"
    --seed "${seed#s}"
    --logdir "${logdir}"
  )
  if [[ "${arm}" == "sc" ]]; then
    cmd+=(--defense safeconfirm --policy rule_v1 --confirmer llm_user --confirmer-model "${MODEL}")
  fi
  "${cmd[@]}"
}

mkdir -p "${LOGROOT}"
for seed in ${SEEDS}; do
  run_arm p0 "${seed}"
  run_arm sc "${seed}"
done

for arm in p0 sc; do
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/${arm}_s[0-9]/${SUITE}/metrics.json" \
    --output "${LOGROOT}/${arm}_aggregate.json"
done

echo "Done. External lineage batch under ${LOGROOT} (cases: benchmark_cases_external.yaml)"
