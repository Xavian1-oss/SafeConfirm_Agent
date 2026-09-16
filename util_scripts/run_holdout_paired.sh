#!/usr/bin/env bash
# Goal E3: holdout-only cases (policy-freeze-v1), paired P0 vs SafeConfirm, 3 seeds.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-deepseek-chat}"
SEEDS="${SEEDS:-s0 s1 s2}"
BATCH_ID="${BATCH_ID:-holdout_v1_$(date +%Y%m%d)}"
LOGROOT="${LOGROOT:-runs/bridge/holdout_${BATCH_ID}}"

load_holdout_ut_args() {
  local suite="$1"
  local -n _out="$2"
  _out=()
  local tid
  while IFS= read -r tid; do
    _out+=(-ut "${tid}")
  done < <(uv run python -c "
from safeconfirm_bridge.case_registry import holdout_user_task_ids
for tid in holdout_user_task_ids('${suite}'):
    print(tid)
")
}

HOLDOUT_WS_UT=()
HOLDOUT_BK_UT=()
load_holdout_ut_args safeconfirm_workspace HOLDOUT_WS_UT
load_holdout_ut_args safeconfirm_banking HOLDOUT_BK_UT

run_arm() {
  local suite_name="$1"
  local arm="$2"
  local seed="$3"
  shift 3
  local logdir="${LOGROOT}/${suite_name}_${arm}_${seed}"
  echo "=== holdout ${suite_name} ${arm} seed=${seed} -> ${logdir} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s "${suite_name}" \
    -m "${MODEL}" \
    -a parameter_poison \
    --run-id "${seed}" \
    --seed "${seed#s}" \
    --logdir "${logdir}" \
    "$@"
}

mkdir -p "${LOGROOT}"
for seed in ${SEEDS}; do
  run_arm safeconfirm_workspace p0 "${seed}" "${HOLDOUT_WS_UT[@]}"
  run_arm safeconfirm_workspace sc "${seed}" "${HOLDOUT_WS_UT[@]}" \
    --defense safeconfirm --policy rule_v1 --confirmer llm_user --confirmer-model "${MODEL}"
  run_arm safeconfirm_banking p0 "${seed}" "${HOLDOUT_BK_UT[@]}"
  run_arm safeconfirm_banking sc "${seed}" "${HOLDOUT_BK_UT[@]}" \
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

echo "Done. Holdout batch under ${LOGROOT} (4 corruption cases, post-freeze)"
