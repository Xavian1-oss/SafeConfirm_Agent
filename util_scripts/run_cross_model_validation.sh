#!/usr/bin/env bash
# Deprecated wrapper — use run_cross_model_signature.sh (12-case signature replication).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${CROSS_MODEL:-}" ]]; then
  export SECONDARY_MODEL="${CROSS_MODEL}"
fi
echo "Note: run_cross_model_validation.sh delegates to run_cross_model_signature.sh" >&2
exec ./util_scripts/run_cross_model_signature.sh "$@"
