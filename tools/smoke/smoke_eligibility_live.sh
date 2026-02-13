#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi

SENSOR_BASE_URL="${SENSOR_BASE_URL:-http://127.0.0.1:9000}"
SENSOR_TIMEOUT_MS="${SENSOR_TIMEOUT_MS:-1500}"
CLIENT_ID="${CLIENT_ID:-100001}"
SEED="${SEED:-42}"

LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/smoke_eligibility_live_${TS}.log"
INTAKE_JSON="$LOG_DIR/eligibility_live_intake_${TS}.json"
OUT_JSON="$LOG_DIR/eligibility_live_out_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_ELIGIBILITY_LIVE] root=$ROOT"
echo "[SMOKE_ELIGIBILITY_LIVE] python=$PY"
echo "[SMOKE_ELIGIBILITY_LIVE] sensor_base_url=$SENSOR_BASE_URL"
echo "[SMOKE_ELIGIBILITY_LIVE] log=$LOG_FILE"

echo "[SMOKE_ELIGIBILITY_LIVE] probing DS_Z health..."
if command -v curl >/dev/null 2>&1; then
  HC=$(curl -s -o /dev/null -w "%{http_code}" "$SENSOR_BASE_URL/health" || true)
  echo "[SMOKE_ELIGIBILITY_LIVE] health_http_code=$HC"
  if [[ "$HC" != "200" ]]; then
    echo "[ERR] DS_Z health is not 200; start DS_Z before running LIVE smoke"
    exit 2
  fi
else
  echo "[WARN] curl not found; skipping explicit health probe"
fi

echo "[SMOKE_ELIGIBILITY_LIVE] building intake..."
"$PY" runners/runner_workflow.py --client-id "$CLIENT_ID" --seed "$SEED" > "$INTAKE_JSON"

echo "[SMOKE_ELIGIBILITY_LIVE] running eligibility in LIVE mode..."
"$PY" runners/runner_eligibility.py \
  --intake-json "$INTAKE_JSON" \
  --sensor-mode LIVE \
  --sensor-base-url "$SENSOR_BASE_URL" \
  --sensor-timeout-ms "$SENSOR_TIMEOUT_MS" \
  > "$OUT_JSON"

echo "[SMOKE_ELIGIBILITY_LIVE] validating output..."
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("STATUS", d.get("eligibility_status")); print("MODE", d.get("meta_sensor_mode_used")); assert d.get("meta_schema_version")=="eligibility_agent_status_v0_1"; assert d.get("meta_sensor_mode_used") in {"LIVE","LIVE_FALLBACK"};' "$OUT_JSON"

echo "[OK] smoke_eligibility_live"
echo "[SMOKE_ELIGIBILITY_LIVE] artifacts: $INTAKE_JSON $OUT_JSON"
echo "[SMOKE_ELIGIBILITY_LIVE] log: $LOG_FILE"
