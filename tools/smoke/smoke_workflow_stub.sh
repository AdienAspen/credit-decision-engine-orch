#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi

LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/smoke_workflow_stub_${TS}.log"
OUT_JSON="$LOG_DIR/last_application_intake_stub.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_WORKFLOW_STUB] root=$ROOT"
echo "[SMOKE_WORKFLOW_STUB] python=$PY"
echo "[SMOKE_WORKFLOW_STUB] log=$LOG_FILE"
echo "[SMOKE_WORKFLOW_STUB] out_json=$OUT_JSON"

echo "[SMOKE_WORKFLOW_STUB] running runner_workflow..."
"$PY" runners/runner_workflow.py --client-id 100001 --seed 42 > "$OUT_JSON"

echo "[SMOKE_WORKFLOW_STUB] validating output..."
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("SCHEMA", d.get("meta_schema_version")); print("HAS_APPLICANT", isinstance(d.get("applicant"), dict)); print("HAS_LOAN", isinstance(d.get("loan"), dict)); print("HAS_DS", isinstance(d.get("dynamic_sensors_for_eligibility"), dict)); print("REQUEST_ID", d.get("meta_request_id")); print("CLIENT_ID", d.get("meta_client_id"))' "$OUT_JSON"

echo "[OK] smoke_workflow_stub"
echo "[SMOKE_WORKFLOW_STUB] artifacts: $OUT_JSON"
echo "[SMOKE_WORKFLOW_STUB] log: $LOG_FILE"
