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
LOG_FILE="$LOG_DIR/smoke_eligibility_stub_${TS}.log"
BASE_JSON="$LOG_DIR/eligibility_base_${TS}.json"
CASE_A_JSON="$LOG_DIR/eligibility_case_a_reject_${TS}.json"
CASE_B_JSON="$LOG_DIR/eligibility_case_b_review_${TS}.json"
CASE_C_JSON="$LOG_DIR/eligibility_case_c_approved_${TS}.json"
OUT_A_JSON="$LOG_DIR/eligibility_out_a_${TS}.json"
OUT_B_JSON="$LOG_DIR/eligibility_out_b_${TS}.json"
OUT_C_JSON="$LOG_DIR/eligibility_out_c_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_ELIGIBILITY_STUB] root=$ROOT"
echo "[SMOKE_ELIGIBILITY_STUB] python=$PY"
echo "[SMOKE_ELIGIBILITY_STUB] log=$LOG_FILE"

echo "[SMOKE_ELIGIBILITY_STUB] building base intake..."
"$PY" runners/runner_workflow.py --client-id 100001 --seed 42 > "$BASE_JSON"

cp "$BASE_JSON" "$CASE_A_JSON"
cp "$BASE_JSON" "$CASE_B_JSON"
cp "$BASE_JSON" "$CASE_C_JSON"

echo "[SMOKE_ELIGIBILITY_STUB] preparing Case A (REJECT)..."
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["applicant"]["is_existing_customer"]=False; d["applicant"]["customer_id"]=""; json.dump(d, open(p,"w"), indent=2)' "$CASE_A_JSON"

echo "[SMOKE_ELIGIBILITY_STUB] preparing Case B (REVIEW)..."
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["applicant"]["is_existing_customer"]=True; d["applicant"]["customer_id"]="cust-100001"; d["dynamic_sensors_for_eligibility"]["dyn_bureau_employment_verified"]=False; d["dynamic_sensors_for_eligibility"]["dyn_market_stress_score_7d"]=0.2; json.dump(d, open(p,"w"), indent=2)' "$CASE_B_JSON"

echo "[SMOKE_ELIGIBILITY_STUB] preparing Case C (APPROVED)..."
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["applicant"]["is_existing_customer"]=True; d["applicant"]["customer_id"]="cust-100001"; d["applicant"]["age"]=30; d["applicant"]["income_monthly"]=2500; d["dynamic_sensors_for_eligibility"]["dyn_bureau_employment_verified"]=True; d["dynamic_sensors_for_eligibility"]["dyn_market_stress_score_7d"]=0.2; json.dump(d, open(p,"w"), indent=2)' "$CASE_C_JSON"

echo "[SMOKE_ELIGIBILITY_STUB] running eligibility for A/B/C..."
"$PY" runners/runner_eligibility.py --intake-json "$CASE_A_JSON" > "$OUT_A_JSON"
"$PY" runners/runner_eligibility.py --intake-json "$CASE_B_JSON" > "$OUT_B_JSON"
"$PY" runners/runner_eligibility.py --intake-json "$CASE_C_JSON" > "$OUT_C_JSON"

echo "[SMOKE_ELIGIBILITY_STUB] validating expected statuses..."
"$PY" -c 'import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); c=json.load(open(sys.argv[3])); print("CASE_A_STATUS", a.get("eligibility_status")); print("CASE_A_REASONS", a.get("eligibility_reasons")); print("CASE_B_STATUS", b.get("eligibility_status")); print("CASE_B_REASONS", b.get("eligibility_reasons")); print("CASE_C_STATUS", c.get("eligibility_status")); print("CASE_C_REASONS", c.get("eligibility_reasons")); assert a.get("eligibility_status")=="REJECTED"; assert b.get("eligibility_status")=="REVIEW_REQUIRED"; assert c.get("eligibility_status")=="APPROVED"' "$OUT_A_JSON" "$OUT_B_JSON" "$OUT_C_JSON"

echo "[OK] smoke_eligibility_stub"
echo "[SMOKE_ELIGIBILITY_STUB] artifacts: $OUT_A_JSON $OUT_B_JSON $OUT_C_JSON"
echo "[SMOKE_ELIGIBILITY_STUB] log: $LOG_FILE"
