#!/usr/bin/env bash
# After run_unified_12case_batch.sh completes, sync metrics and refresh paper artifacts.
set -euo pipefail
cd "$(dirname "$0")/.."

BATCH_ID="${UNIFIED_12CASE_BATCH:-unified_12case_20260919}"
export UNIFIED_12CASE_BATCH="${BATCH_ID}"

if [[ ! -f "runs/bridge/${BATCH_ID}/rule_v1_aggregate.json" ]]; then
  echo "Missing runs/bridge/${BATCH_ID}/rule_v1_aggregate.json — run unified batch first." >&2
  exit 1
fi

./util_scripts/sync_paper_metrics.sh
uv run python util_scripts/update_safeconfirm_tex_from_canonical.py
uv run python util_scripts/generate_rq1_bar_chart.py
uv run python util_scripts/verify_paper_metrics.py
./6a9fb8173b16b4dea4fd1079/compile_safeconfirm.sh

echo "Paper artifacts updated for batch ${BATCH_ID}."
