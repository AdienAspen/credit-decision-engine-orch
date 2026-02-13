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
LOG_FILE="$LOG_DIR/smoke_workflow_eligibility_stub_${TS}.log"
OUT_A_JSON="$LOG_DIR/workflow_eligibility_out_a_${TS}.json"
OUT_B_JSON="$LOG_DIR/workflow_eligibility_out_b_${TS}.json"
OUT_C_JSON="$LOG_DIR/workflow_eligibility_out_c_${TS}.json"

ALIAS_A="/tmp/eligibility_canonical_case_a_${TS}.json"
ALIAS_B="/tmp/eligibility_canonical_case_b_${TS}.json"
ALIAS_C="/tmp/eligibility_canonical_case_c_${TS}.json"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] root=$ROOT"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] python=$PY"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] log=$LOG_FILE"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] preparing canonical aliases for A/B/C..."
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_A"
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_B"
cp block_a_gov/artifacts/eligibility_canonical.json "$ALIAS_C"

# Case A -> force REJECT (income below threshold)
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=100000; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=0.99; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_A"

# Case B -> force REVIEW (macro threshold very low, keep income pass)
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=1; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=0.0; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_B"

# Case C -> APPROVED path (easy pass)
"$PY" -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["parameters"]["MIN_INCOME"]=1; d["parameters"]["MACRO_STRESS_REVIEW_THR"]=1.0; json.dump(d, open(p,"w"), indent=2)' "$ALIAS_C"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] running Case A (expect REJECT early-cut)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id 100001 \
  --seed 42 \
  --eligibility-canonical-alias "$ALIAS_A" \
  --workflow-canonical-alias "$ALIAS_A" \
  > "$OUT_A_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] running Case B (expect REVIEW early-cut)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id 100001 \
  --seed 42 \
  --eligibility-canonical-alias "$ALIAS_B" \
  --workflow-canonical-alias "$ALIAS_B" \
  > "$OUT_B_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] running Case C (expect APPROVED -> ORIGINATE)..."
"$PY" runners/runner_workflow_eligibility.py \
  --client-id 100001 \
  --seed 42 \
  --eligibility-canonical-alias "$ALIAS_C" \
  --workflow-canonical-alias "$ALIAS_C" \
  --brms-stub tools/smoke/fixtures/brms_all_pass.json \
  > "$OUT_C_JSON"

echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] validating outputs..."
"$PY" -c 'import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); c=json.load(open(sys.argv[3]));

a_el=a.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
a_out=a.get("decisions",{}).get("final_decision",{}).get("final_outcome");
a_has_t2=("t2_default" in a.get("decisions",{}));
print("CASE_A_ELIG",a_el); print("CASE_A_OUT",a_out); print("CASE_A_HAS_T2",a_has_t2);

b_el=b.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
b_out=b.get("decisions",{}).get("final_decision",{}).get("final_outcome");
b_has_t2=("t2_default" in b.get("decisions",{}));
print("CASE_B_ELIG",b_el); print("CASE_B_OUT",b_out); print("CASE_B_HAS_T2",b_has_t2);

c_el=c.get("decisions",{}).get("eligibility",{}).get("eligibility_status");
c_out=c.get("decisions",{}).get("final_decision",{}).get("final_outcome");
c_has_t2=("t2_default" in c.get("decisions",{}));
print("CASE_C_ELIG",c_el); print("CASE_C_OUT",c_out); print("CASE_C_HAS_T2",c_has_t2);

assert a_el=="REJECTED" and a_out=="REJECT" and (not a_has_t2)
assert b_el=="REVIEW_REQUIRED" and b_out=="REVIEW" and (not b_has_t2)
assert c_el=="APPROVED" and c_has_t2
' "$OUT_A_JSON" "$OUT_B_JSON" "$OUT_C_JSON"

echo "[OK] smoke_workflow_eligibility_stub"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] artifacts: $OUT_A_JSON $OUT_B_JSON $OUT_C_JSON"
echo "[SMOKE_WORKFLOW_ELIGIBILITY_STUB] log: $LOG_FILE"
