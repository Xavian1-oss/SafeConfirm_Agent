#!/usr/bin/env bash
# Goal E2: full 28-case suite (22 workspace + 6 banking), P0 vs SafeConfirm, 3 seeds.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
BATCH_ID="${BATCH_ID:-extend_v1_$(date +%Y%m%d)}"
LOGROOT="${LOGROOT:-runs/bridge/e2e_extended_${BATCH_ID}}"

run_arm() {
  local suite_name="$1"
  local arm="$2"
  local seed="$3"
  local logdir="${LOGROOT}/${suite_name}_${arm}_${seed}"
  shift 3
  echo "=== ${suite_name} ${arm} seed=${seed} -> ${logdir} ==="
  local -a cmd=(
    uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark
    -s "${suite_name}"
    -m "${MODEL}"
    -a parameter_poison
    --run-id "${seed}"
    --seed "${seed#s}"
    --logdir "${logdir}"
  )
  if (("$#")); then
    cmd+=("$@")
  fi
  "${cmd[@]}"
}

mkdir -p "${LOGROOT}"
for seed in ${SEEDS}; do
  run_arm safeconfirm_workspace p0 "${seed}"
  run_arm safeconfirm_workspace sc "${seed}" \
    --defense safeconfirm --policy rule_v1 --confirmer llm_user --confirmer-model "${MODEL}"
  run_arm safeconfirm_banking p0 "${seed}"
  run_arm safeconfirm_banking sc "${seed}" \
    --defense safeconfirm --policy rule_v1 --confirmer llm_user --confirmer-model "${MODEL}"
done

for suite_name in safeconfirm_workspace safeconfirm_banking; do
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/${suite_name}_p0_s[0-9]/${suite_name}/metrics.json" \
    --output "${LOGROOT}/${suite_name}_p0_aggregate.json"
  uv run python util_scripts/aggregate_seed_metrics.py \
    --pattern "${LOGROOT}/${suite_name}_sc_s[0-9]/${suite_name}/metrics.json" \
    --output "${LOGROOT}/${suite_name}_sc_aggregate.json"
done

echo "Done. Extended 28-case batch under ${LOGROOT}"
