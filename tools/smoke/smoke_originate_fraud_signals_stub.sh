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
LOG_FILE="$LOG_DIR/smoke_originate_fraud_signals_stub_${TS}.log"
OUT_LOW="$LOG_DIR/originate_fraud_stub_low_${TS}.json"
OUT_HIGH="$LOG_DIR/originate_fraud_stub_high_${TS}.json"
TMP_HIGH="/tmp/fraud_signals_high_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_ORIG_FRAUD_STUB] root=$ROOT"
echo "[SMOKE_ORIG_FRAUD_STUB] python=$PY"
echo "[SMOKE_ORIG_FRAUD_STUB] log=$LOG_FILE"

cp tools/smoke/fixtures/fraud_signals_stub.json "$TMP_HIGH"
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["dyn_device_behavior_fraud_score_24h"]=0.95; d["dyn_transaction_anomaly_score_30d"]=0.96; json.dump(d, open(p,"w"), indent=2)' "$TMP_HIGH"

echo "[SMOKE_ORIG_FRAUD_STUB] case LOW (expect allow path)"
"$PY" runners/originate.py --client-id 100001 --seed 42 --brms-stub tools/smoke/fixtures/brms_all_pass.json --fraud-signals-mode STUB --fraud-signals-stub tools/smoke/fixtures/fraud_signals_stub.json > "$OUT_LOW"

echo "[SMOKE_ORIG_FRAUD_STUB] case HIGH (expect review signal, no blind block)"
"$PY" runners/originate.py --client-id 100001 --seed 42 --brms-stub tools/smoke/fixtures/brms_all_pass.json --fraud-signals-mode STUB --fraud-signals-stub "$TMP_HIGH" > "$OUT_HIGH"

"$PY" -c 'import json,sys; lo=json.load(open(sys.argv[1])); hi=json.load(open(sys.argv[2]));
lf=lo["decisions"]["fraud_signals"]; hf=hi["decisions"]["fraud_signals"];
print("LOW_ACTION", lf.get("action_recommended"));
print("HIGH_ACTION", hf.get("action_recommended"));
print("HIGH_FLAGS", hf.get("flag_device_suspicious"), hf.get("flag_transaction_anomalous"));
print("HIGH_FINAL", hi["decisions"]["final_decision"].get("final_outcome"));
assert lf.get("action_recommended") in {"ALLOW","STEP_UP","REVIEW"}
assert hf.get("flag_device_suspicious") is True and hf.get("flag_transaction_anomalous") is True
assert hf.get("action_recommended") in {"REVIEW","BLOCK"}
' "$OUT_LOW" "$OUT_HIGH"

echo "[OK] smoke_originate_fraud_signals_stub"
echo "[SMOKE_ORIG_FRAUD_STUB] artifacts: $OUT_LOW $OUT_HIGH"
echo "[SMOKE_ORIG_FRAUD_STUB] log: $LOG_FILE"
