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
LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/smoke_originate_fraud_signals_live_${TS}.log"
OUT_JSON="$LOG_DIR/originate_fraud_live_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_ORIG_FRAUD_LIVE] root=$ROOT"
echo "[SMOKE_ORIG_FRAUD_LIVE] python=$PY"
echo "[SMOKE_ORIG_FRAUD_LIVE] sensor_base_url=$SENSOR_BASE_URL"
echo "[SMOKE_ORIG_FRAUD_LIVE] log=$LOG_FILE"

if command -v curl >/dev/null 2>&1; then
  HC=$(curl -s -o /dev/null -w "%{http_code}" "$SENSOR_BASE_URL/health" || true)
  echo "[SMOKE_ORIG_FRAUD_LIVE] health_http_code=$HC"
  if [[ "$HC" != "200" ]]; then
    echo "[ERR] DS_Z health is not 200"
    exit 2
  fi
fi

"$PY" runners/originate.py --client-id 100001 --seed 42 --brms-stub tools/smoke/fixtures/brms_all_pass.json --fraud-signals-mode LIVE --fraud-sensor-base-url "$SENSOR_BASE_URL" > "$OUT_JSON"

"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); fs=d["decisions"].get("fraud_signals",{}); print("MODE", fs.get("meta_sensor_mode_used")); print("ACTION", fs.get("action_recommended")); print("HAS_TRACE", isinstance(fs.get("sensor_trace"), dict)); assert fs.get("meta_sensor_mode_used") in {"LIVE","LIVE_FALLBACK"}; assert isinstance(fs.get("sensor_trace"), dict)' "$OUT_JSON"

echo "[OK] smoke_originate_fraud_signals_live"
echo "[SMOKE_ORIG_FRAUD_LIVE] artifacts: $OUT_JSON"
echo "[SMOKE_ORIG_FRAUD_LIVE] log: $LOG_FILE"
