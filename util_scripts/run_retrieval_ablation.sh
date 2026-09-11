#!/usr/bin/env bash
# H3: retrieval policy vs rule_v1 on 12-case workspace subset (Appendix tab:retrieval).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=benchmark_subsets.sh
source "$(dirname "$0")/benchmark_subsets.sh"

MODEL="${MODEL:-deepseek-chat}"
SUITE="${SUITE:-safeconfirm_workspace}"
SUBSET="${SUBSET:-12}"
LOGROOT="${LOGROOT:-runs/bridge/e2e_retrieval_ablation}"
mkdir -p "${LOGROOT}"

load_workspace_subset_args "${SUBSET}"

run_policy() {
  local policy="$1"
  local logdir="$2"
  echo "=== policy=${policy} -> ${logdir} ==="
  uv run python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
    -s "${SUITE}" \
    -m "${MODEL}" \
    -a parameter_poison \
    --defense safeconfirm \
    --policy "${policy}" \
    --confirmer llm_user \
    --confirmer-model "${MODEL}" \
    --logdir "${logdir}" \
    "${SUBSET_ARGS[@]+"${SUBSET_ARGS[@]}"}"
}

run_policy rule_v1 "${LOGROOT}/rule_v1"
run_policy retrieval "${LOGROOT}/retrieval"

for label in rule_v1 retrieval; do
  uv run python -c "
import json
from pathlib import Path
m = json.loads(Path('${LOGROOT}/${label}/${SUITE}/metrics.json').read_text())
print(f'${label}: TSR={m[\"tsr\"]*100:.1f}% ASR={m[\"asr\"]*100:.1f}%')
"
done

echo "Done. Retrieval ablation under ${LOGROOT}"
