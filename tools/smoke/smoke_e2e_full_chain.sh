#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi

SENSOR_MODE="${SENSOR_MODE:-STUB}"   # STUB or LIVE
SENSOR_BASE_URL="${SENSOR_BASE_URL:-http://127.0.0.1:9000}"
SENSOR_TIMEOUT_MS="${SENSOR_TIMEOUT_MS:-1500}"
BRMS_MODE="${BRMS_MODE:-STUB}"       # STUB or LIVE
BRMS_STUB="${BRMS_STUB:-tools/smoke/fixtures/brms_all_pass.json}"
BRMS_URL="${BRMS_URL:-http://localhost:8090/bridge/brms_flags}"
CLIENT_ID="${CLIENT_ID:-100001}"
SEED="${SEED:-42}"

LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/smoke_e2e_full_chain_${TS}.log"
PACK_JSON="$LOG_DIR/e2e_full_chain_pack_${TS}.json"
REPORT_JSON="$LOG_DIR/e2e_full_chain_report_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_E2E_FULL] root=$ROOT"
echo "[SMOKE_E2E_FULL] python=$PY"
echo "[SMOKE_E2E_FULL] sensor_mode=$SENSOR_MODE"
echo "[SMOKE_E2E_FULL] brms_mode=$BRMS_MODE"
echo "[SMOKE_E2E_FULL] log=$LOG_FILE"

if [[ "$SENSOR_MODE" == "LIVE" ]]; then
  if command -v curl >/dev/null 2>&1; then
    HC=$(curl -s -o /dev/null -w "%{http_code}" "$SENSOR_BASE_URL/health" || true)
    echo "[SMOKE_E2E_FULL] DS_Z health_http_code=$HC"
    if [[ "$HC" != "200" ]]; then
      echo "[ERR] DS_Z health is not 200"
      exit 2
    fi
  fi
fi

ORCH_ARGS=(
  "--client-id" "$CLIENT_ID"
  "--seed" "$SEED"
  "--sensor-mode" "$SENSOR_MODE"
  "--sensor-base-url" "$SENSOR_BASE_URL"
  "--sensor-timeout-ms" "$SENSOR_TIMEOUT_MS"
)

if [[ "$BRMS_MODE" == "LIVE" ]]; then
  ORCH_ARGS+=("--brms-url" "$BRMS_URL")
else
  ORCH_ARGS+=("--brms-stub" "$BRMS_STUB")
fi

echo "[SMOKE_E2E_FULL] running workflow+eligibility+originate..."
"$PY" runners/runner_workflow_eligibility.py "${ORCH_ARGS[@]}" > "$PACK_JSON"

echo "[SMOKE_E2E_FULL] running reporter..."
"$PY" runners/runner_reporter.py --decision-pack-json "$PACK_JSON" > "$REPORT_JSON"

echo "[SMOKE_E2E_FULL] validating artifacts..."
"$PY" -c 'import json,sys
pack=json.load(open(sys.argv[1]))
rep=json.load(open(sys.argv[2]))
d=pack.get("decisions",{})
fd=d.get("final_decision",{})
el=d.get("eligibility",{})
print("PACK_SCHEMA", pack.get("meta_schema_version"))
print("ELIG_STATUS", el.get("eligibility_status"))
print("FINAL_OUTCOME", fd.get("final_outcome"))
print("FINAL_REASON", fd.get("final_reason_code"))
print("HAS_REPORT_SUMMARY", bool(rep.get("executive_summary")))
print("REPORT_SCHEMA", rep.get("meta_schema_version"))
assert pack.get("meta_schema_version")=="decision_pack_v0_1"
assert isinstance(fd, dict) and fd.get("meta_schema_version")=="final_decision_v0_1"
assert rep.get("meta_schema_version")=="reporter_output_v0_1"
' "$PACK_JSON" "$REPORT_JSON"

echo "[OK] smoke_e2e_full_chain"
echo "[SMOKE_E2E_FULL] artifacts: $PACK_JSON $REPORT_JSON"
echo "[SMOKE_E2E_FULL] log: $LOG_FILE"
