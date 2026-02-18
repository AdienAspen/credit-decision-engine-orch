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
LOG_FILE="$LOG_DIR/smoke_reporter_stub_${TS}.log"
PACK_JSON="$LOG_DIR/reporter_input_pack_${TS}.json"
OUT_JSON="$LOG_DIR/reporter_output_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_REPORTER_STUB] root=$ROOT"
echo "[SMOKE_REPORTER_STUB] python=$PY"
echo "[SMOKE_REPORTER_STUB] log=$LOG_FILE"

echo "[SMOKE_REPORTER_STUB] building decision pack via workflow+eligibility orchestrator..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id 100001 \
  --seed 42 \
  --sensor-mode STUB \
  --brms-stub tools/smoke/fixtures/brms_all_pass.json \
  > "$PACK_JSON"

echo "[SMOKE_REPORTER_STUB] running reporter..."
"$PY" runners/runner_reporter.py --decision-pack-json "$PACK_JSON" > "$OUT_JSON"

echo "[SMOKE_REPORTER_STUB] validating output..."
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("SCHEMA", d.get("meta_schema_version")); print("HAS_EXEC_SUMMARY", bool(d.get("executive_summary"))); print("OUTCOME", d.get("decision_ref",{}).get("final_outcome")); print("REASON", d.get("decision_ref",{}).get("final_reason_code")); assert d.get("meta_schema_version")=="reporter_output_v0_1"; assert isinstance(d.get("risk_highlights"), list); assert isinstance(d.get("governance_highlights"), list)' "$OUT_JSON"

echo "[OK] smoke_reporter_stub"
echo "[SMOKE_REPORTER_STUB] artifacts: $PACK_JSON $OUT_JSON"
echo "[SMOKE_REPORTER_STUB] log: $LOG_FILE"
