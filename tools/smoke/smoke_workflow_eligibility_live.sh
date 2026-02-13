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
LOG_FILE="$LOG_DIR/smoke_workflow_eligibility_live_${TS}.log"
OUT_A_JSON="$LOG_DIR/workflow_eligibility_live_out_a_${TS}.json"
OUT_B_JSON="$LOG_DIR/workflow_eligibility_live_out_b_${TS}.json"
OUT_C_JSON="$LOG_DIR/workflow_eligibility_live_out_c_${TS}.json"

ALIAS_A="/tmp/eligibility_live_case_a_${TS}.json"
ALIAS_B="/tmp/eligibility_live_case_b_${TS}.json"
ALIAS_C="/tmp/eligibility_live_case_c_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] root=$ROOT"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] python=$PY"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] sensor_base_url=$SENSOR_BASE_URL"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] log=$LOG_FILE"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] probing DS_Z health..."
if command -v curl >/dev/null 2>&1; then
  HC=$(curl -s -o /dev/null -w "%{http_code}" "$SENSOR_BASE_URL/health" || true)
  echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] health_http_code=$HC"
  if [[ "$HC" != "200" ]]; then
    echo "[ERR] DS_Z health is not 200; start DS_Z before running LIVE smoke"
    exit 2
  fi
fi

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] preparing canonical aliases for A/B/C..."
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_A"
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_B"
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_C"

# Case A -> force REJECT by income threshold
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=100000; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=1.0; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_A"

# Case B -> force REVIEW by macro threshold, keep income easy pass
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=1; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=0.0; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_B"

# Case C -> APPROVED path, avoid review by high threshold and low income gate
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=1; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=1.0; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_C"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] running Case A (REJECT early-cut)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id "$CLIENT_ID" \
  --seed "$SEED" \
  --sensor-mode LIVE \
  --sensor-base-url "$SENSOR_BASE_URL" \
  --sensor-timeout-ms "$SENSOR_TIMEOUT_MS" \
  --eligibility-canonical-alias "$ALIAS_A" \
  --workflow-canonical-alias "$ALIAS_A" \
  > "$OUT_A_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] running Case B (REVIEW early-cut)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id "$CLIENT_ID" \
  --seed "$SEED" \
  --sensor-mode LIVE \
  --sensor-base-url "$SENSOR_BASE_URL" \
  --sensor-timeout-ms "$SENSOR_TIMEOUT_MS" \
  --eligibility-canonical-alias "$ALIAS_B" \
  --workflow-canonical-alias "$ALIAS_B" \
  > "$OUT_B_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] running Case C (APPROVED -> ORIGINATE)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id "$CLIENT_ID" \
  --seed "$SEED" \
  --sensor-mode LIVE \
  --sensor-base-url "$SENSOR_BASE_URL" \
  --sensor-timeout-ms "$SENSOR_TIMEOUT_MS" \
  --eligibility-canonical-alias "$ALIAS_C" \
  --workflow-canonical-alias "$ALIAS_C" \
  --brms-stub tools/smoke/fixtures/brms_all_pass.json \
  > "$OUT_C_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] validating outputs..."
"$PY" -c 'import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); c=json.load(open(sys.argv[3]));

a_el=a.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
a_out=a.get("decisions",{}).get("final_decision",{}).get("final_outcome");
a_has_t2=("t2_default" in a.get("decisions",{}));
a_mode=a.get("decisions",{}).get("eligibility",{}).get("meta_sensor_mode_used");
print("CASE_A_ELIG",a_el); print("CASE_A_OUT",a_out); print("CASE_A_HAS_T2",a_has_t2); print("CASE_A_MODE",a_mode);

b_el=b.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
b_out=b.get("decisions",{}).get("final_decision",{}).get("final_outcome");
b_has_t2=("t2_default" in b.get("decisions",{}));
b_mode=b.get("decisions",{}).get("eligibility",{}).get("meta_sensor_mode_used");
print("CASE_B_ELIG",b_el); print("CASE_B_OUT",b_out); print("CASE_B_HAS_T2",b_has_t2); print("CASE_B_MODE",b_mode);

c_el=c.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
c_out=c.get("decisions",{}).get("final_decision",{}).get("final_outcome");
c_has_t2=("t2_default" in c.get("decisions",{}));
c_mode=c.get("decisions",{}).get("eligibility",{}).get("meta_sensor_mode_used");
print("CASE_C_ELIG",c_el); print("CASE_C_OUT",c_out); print("CASE_C_HAS_T2",c_has_t2); print("CASE_C_MODE",c_mode);

assert a_el=="REJECTED" and a_out=="REJECT" and (not a_has_t2)
assert b_el=="REVIEW_REQUIRED" and b_out=="REVIEW" and (not b_has_t2)
assert c_el=="APPROVED" and c_has_t2
assert a_mode in {"LIVE","LIVE_FALLBACK"}
assert b_mode in {"LIVE","LIVE_FALLBACK"}
assert c_mode in {"LIVE","LIVE_FALLBACK"}
' "$OUT_A_JSON" "$OUT_B_JSON" "$OUT_C_JSON"

echo "[OK] smoke_workflow_eligibility_live"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] artifacts: $OUT_A_JSON $OUT_B_JSON $OUT_C_JSON"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_LIVE] log: $LOG_FILE"
