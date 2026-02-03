#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi

cd "$ROOT"

BRIDGE_PORT="${BRIDGE_PORT:-8090}"
HEALTH_URL="http://127.0.0.1:${BRIDGE_PORT}/health"
LOG_DIR="tools/smoke/_logs"
mkdir -p "$LOG_DIR"

BRIDGE_LOG="$LOG_DIR/bridge_loop_${BRIDGE_PORT}.log"
BRIDGE_PID_FILE="$LOG_DIR/bridge_loop_${BRIDGE_PORT}.pid"

cleanup() {
  if [[ -f "$BRIDGE_PID_FILE" ]]; then
    PID="$(cat "$BRIDGE_PID_FILE" 2>/dev/null || true)"
    if [[ -n "${PID:-}" ]] && kill -0 "$PID" >/dev/null 2>&1; then
      echo "[BRIDGE_LOOP] stopping bridge pid=$PID"
      kill "$PID" >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT

echo "[BRIDGE_LOOP] root=$ROOT"
echo "[BRIDGE_LOOP] python=$PY"
echo "[BRIDGE_LOOP] health_url=$HEALTH_URL"

echo "[BRIDGE_LOOP] starting bridge..."
nohup env PYTHONPATH="" "$PY" -m tools.brms_bridge_server >"$BRIDGE_LOG" 2>&1 &
echo $! > "$BRIDGE_PID_FILE"
echo "[BRIDGE_LOOP] bridge pid=$(cat "$BRIDGE_PID_FILE") log=$BRIDGE_LOG"

TRIES="${TRIES:-20}"
SLEEP_SECS="${SLEEP_SECS:-0.5}"

for i in $(seq 1 "$TRIES"); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)
  echo "[BRIDGE_LOOP] try=$i http_code=$code"
  if [[ "$code" == "200" ]]; then
    echo "[BRIDGE_LOOP] OK"
    exit 0
  fi
  sleep "$SLEEP_SECS"
done

echo "[BRIDGE_LOOP] FAIL: health never returned 200"
exit 1
