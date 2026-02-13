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
LOG_FILE="$LOG_DIR/smoke_originate_fraud_signals_consume_present_${TS}.log"
OUT_DEFAULT="$LOG_DIR/originate_consume_present_default_${TS}.json"
OUT_ATTACHED="$LOG_DIR/originate_consume_present_attached_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_ORIG_FRAUD_CONSUME] root=$ROOT"
echo "[SMOKE_ORIG_FRAUD_CONSUME] python=$PY"
echo "[SMOKE_ORIG_FRAUD_CONSUME] log=$LOG_FILE"

echo "[SMOKE_ORIG_FRAUD_CONSUME] case default (resolve path)..."
"$PY" runners/originate.py \
  --client-id 100001 \
  --seed 42 \
  --brms-stub tools/smoke/fixtures/brms_all_pass.json \
  --fraud-signals-mode STUB \
  --fraud-signals-stub tools/smoke/fixtures/fraud_signals_stub.json \
  > "$OUT_DEFAULT"

echo "[SMOKE_ORIG_FRAUD_CONSUME] case attached (consume-if-present path)..."
"$PY" runners/originate.py \
  --client-id 100001 \
  --seed 42 \
  --brms-stub tools/smoke/fixtures/brms_all_pass.json \
  --fraud-signals-json tools/smoke/fixtures/fraud_signals_stub.json \
  > "$OUT_ATTACHED"

echo "[SMOKE_ORIG_FRAUD_CONSUME] validating outputs..."
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); a=json.load(open(sys.argv[2]));
fs_d=d["decisions"].get("fraud_signals",{}); fs_a=a["decisions"].get("fraud_signals",{});
print("DEFAULT_HAS_META", "meta_schema_version" in fs_d);
print("ATTACHED_SOURCE", fs_a.get("sensor_trace",{}).get("device_behavior",{}).get("source"));
print("ATTACHED_MODE", fs_a.get("sensor_trace",{}).get("device_behavior",{}).get("mode"));
assert "meta_schema_version" in fs_d
assert fs_a.get("sensor_trace",{}).get("device_behavior",{}).get("source")=="stub_fixture_v0_1"
assert fs_a.get("sensor_trace",{}).get("device_behavior",{}).get("mode")=="STUB"' "$OUT_DEFAULT" "$OUT_ATTACHED"

echo "[OK] smoke_originate_fraud_signals_consume_present"
echo "[SMOKE_ORIG_FRAUD_CONSUME] artifacts: $OUT_DEFAULT $OUT_ATTACHED"
echo "[SMOKE_ORIG_FRAUD_CONSUME] log: $LOG_FILE"
