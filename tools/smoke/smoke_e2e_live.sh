#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# --- Python resolver (prefer project venv; allow override via env PY) ---
PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi


cd "$ROOT"

BRIDGE_PORT="${BRIDGE_PORT:-8090}"
BRIDGE_URL="http://localhost:${BRIDGE_PORT}/bridge/brms_flags"
CLIENT_ID="${CLIENT_ID:-100001}"
SEED="${SEED:-42}"

echo "[SMOKE] root=$ROOT"
echo "[SMOKE] python=$PY"
echo "[SMOKE] bridge_url=$BRIDGE_URL"

# --- Start BRMS bridge server in background ---
LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"

BRIDGE_LOG="$LOG_DIR/bridge_${BRIDGE_PORT}.log"
BRIDGE_PID_FILE="$LOG_DIR/bridge_${BRIDGE_PORT}.pid"

# If something is already listening, don't start a second server.
if (echo > /dev/tcp/127.0.0.1/"$BRIDGE_PORT") >/dev/null 2>&1; then
  echo "[SMOKE] port ${BRIDGE_PORT} already open -> assume bridge is running"
else
  echo "[SMOKE] starting bridge server..."
  nohup env PYTHONPATH="" "$PY" -m tools.brms_bridge_server >"$BRIDGE_LOG" 2>&1 &
  echo $! > "$BRIDGE_PID_FILE"
  echo "[SMOKE] bridge pid=$(cat "$BRIDGE_PID_FILE") log=$BRIDGE_LOG"
fi

# Ensure we stop the bridge we started (best-effort)
cleanup() {
  if [[ -f "$BRIDGE_PID_FILE" ]]; then
    PID="$(cat "$BRIDGE_PID_FILE" 2>/dev/null || true)"
    if [[ -n "${PID:-}" ]] && kill -0 "$PID" >/dev/null 2>&1; then
      echo "[SMOKE] stopping bridge pid=$PID"
      kill "$PID" >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT

# --- Wait for bridge to accept a TCP connection ---
echo "[SMOKE] waiting for bridge port..."
for i in $(seq 1 25); do
  if (echo > /dev/tcp/127.0.0.1/"$BRIDGE_PORT") >/dev/null 2>&1; then
    echo "[SMOKE] bridge port open"
    break
  fi
  sleep 0.2
done

# --- Probe the endpoint (POST) ---
PROBE_PAYLOAD="$(mktemp)"
cat > "$PROBE_PAYLOAD" <<JSON
{
  "meta_request_id": "smoke-probe",
  "meta_client_id": "${CLIENT_ID}"
}
JSON

BRMS_LIVE_OK=0
if command -v curl >/dev/null 2>&1; then
echo "[SMOKE] probing GET ${BRIDGE_URL%/bridge/brms_flags}/health ..."
HEALTH_URL="${BRIDGE_URL%/bridge/brms_flags}/health"
HC=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)
echo "[SMOKE] health http_code=$HC"

  echo "[SMOKE] probing POST ${BRIDGE_URL} ..."
  # If KIE is down, this may return 500; we treat that as "live not OK".
  if curl -sS -m 2 -X POST "$BRIDGE_URL" -H "Content-Type: application/json" -d @"$PROBE_PAYLOAD" >/dev/null; then
    BRMS_LIVE_OK=1
    echo "[SMOKE] bridge POST OK"
  else
    echo "[SMOKE] bridge POST NOT OK (maybe KIE down). Will use stub for originate."
  fi
else
  echo "[SMOKE] curl not found -> cannot probe. Will use stub for originate."
fi

# --- Build a minimal BRMS stub (always available) ---
BRMS_STUB="$(mktemp)"
cat > "$BRMS_STUB" <<JSON
{
  "meta_schema_version": "brms_flags_v0_1",
  "meta_generated_at": "1970-01-01T00:00:00Z",
  "meta_request_id": "smoke-stub",
  "meta_client_id": "${CLIENT_ID}",
  "meta_policy_id": "stub_policy",
  "meta_policy_version": "0.0.0",
  "meta_validation_mode": "stub",
  "meta_latency_ms": 0,
  "gates": { "gate_1": "PASS", "gate_2": "PASS", "gate_3": "PASS" },
  "flags": [],
  "reasons": []
}
JSON

# --- Run ORIGINATE (live if probe ok, else stub) ---
echo "[SMOKE] running originate..."
OUT_JSON="$(mktemp)"


if [[ "$BRMS_LIVE_OK" -eq 1 ]]; then
  "$PY" runners/originate.py --client-id "$CLIENT_ID" --seed "$SEED" --brms-url "$BRIDGE_URL" > "$OUT_JSON"
else
  "$PY" runners/originate.py --client-id "$CLIENT_ID" --seed "$SEED" --brms-stub "$BRMS_STUB" > "$OUT_JSON"
fi

# --- Validate minimal expectations ---
echo "[SMOKE] validate output..."
echo "[SMOKE] validate output..."
"$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); fd=d.get(\"decisions\",{}).get(\"final_decision\"); print(\"HAS_FINAL_DECISION\", bool(fd)); print(\"FINAL_OUTCOME\", fd.get(\"final_outcome\") if fd else None); print(\"FINAL_REASON\", fd.get(\"final_reason_code\") if fd else None)" "$OUT_JSON"
