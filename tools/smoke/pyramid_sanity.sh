#!/usr/bin/env bash
# Pyramid sanity for PolicyDecider v0.1
# - No brittle heredoc-in-$(...) patterns
# - Uses env CASE_JSON to feed python deterministically

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${PY:-python3}"

echo "[SANITY] running pyramid sanity scenarios..."

run_case() {
  local LABEL="$1"
  local CASE_JSON="$2"
  local EXP_OUTCOME="$3"
  local EXP_REASON="$4"
  local MUST_NOT_CONTAIN_JSON="${5:-[]}"
  local EXP_WARN_CONTAINS_JSON="${6:-[]}"
  local EXP_DOM_CONTAINS_JSON="${7:-[]}"

  echo "[STEP] Scenario ${LABEL}..."
  CASE_JSON="$CASE_JSON" \
  EXP_OUTCOME="$EXP_OUTCOME" \
  EXP_REASON="$EXP_REASON" \
  MUST_NOT_CONTAIN_JSON="$MUST_NOT_CONTAIN_JSON" \
  EXP_WARN_CONTAINS_JSON="$EXP_WARN_CONTAINS_JSON" \
  EXP_DOM_CONTAINS_JSON="$EXP_DOM_CONTAINS_JSON" \
  "$PY" - <<'PY'
import json, os
from runners.originate import policy_decider_v0_1

label = os.environ["LABEL"] if "LABEL" in os.environ else "?"
case = json.loads(os.environ["CASE_JSON"])
fd = policy_decider_v0_1(decision_pack=case["decision_pack"], brms_flags=case.get("brms_flags"))

print(f"{case['label']}_FINAL_OUTCOME", fd.get("final_outcome"))
print(f"{case['label']}_FINAL_REASON", fd.get("final_reason_code"))
print(f"{case['label']}_WARNINGS", fd.get("warnings"))
print(f"{case['label']}_DOMINANT", fd.get("dominant_signals"))

exp_outcome = os.environ["EXP_OUTCOME"]
exp_reason = os.environ["EXP_REASON"]
must_not = json.loads(os.environ.get("MUST_NOT_CONTAIN_JSON","[]"))
warn_contains = json.loads(os.environ.get("EXP_WARN_CONTAINS_JSON","[]"))
dom_contains = json.loads(os.environ.get("EXP_DOM_CONTAINS_JSON","[]"))

assert fd.get("final_outcome") == exp_outcome
assert fd.get("final_reason_code") == exp_reason

dom = fd.get("dominant_signals") or []
for x in must_not:
    assert x not in dom

warn = fd.get("warnings") or []
for x in warn_contains:
    assert x in warn

for x in dom_contains:
    assert x in dom

print(f"{case['label']}_OK")
PY
}

# --- Load BRMS fixtures ---
BRMS_ALL_PASS="$(cat tools/smoke/fixtures/brms_all_pass.json)"
BRMS_GATE2_FAIL="$(cat tools/smoke/fixtures/brms_gate2_fail.json)"

# --- Scenario A: BRMS gate_2 FAIL => REJECT / BRMS_GATE_FAIL ---
CASE_A="$(cat <<JSON
{
  "label": "A",
  "decision_pack": {
    "meta_request_id": "sanity-A",
    "meta_client_id": "100001",
    "meta_brms_policy_snapshot": {"policy_id": "P1", "policy_version": "1.0"},
    "decisions": {
      "t3_fraud": {"decision_fraud_norm": "LOW_FRAUD"},
      "t2_default": {"decision_default_norm": "LOW_RISK"},
      "t4_payoff": {"decision_payoff_norm": "LOW_PAYOFF_RISK"}
    }
  },
  "brms_flags": $BRMS_GATE2_FAIL
}
JSON
)"
LABEL="A" run_case "A" "$CASE_A" "REJECT" "BRMS_GATE_FAIL" "[]" "[]" "[]"

# --- Scenario B: T3 HIGH_FRAUD veto => REJECT / T3_HIGH_FRAUD_VETO ---
CASE_B="$(cat <<JSON
{
  "label": "B",
  "decision_pack": {
    "meta_request_id": "sanity-B",
    "meta_client_id": "100001",
    "meta_brms_policy_snapshot": {"policy_id": "P1", "policy_version": "1.0"},
    "decisions": {
      "t3_fraud": {"decision_fraud_norm": "HIGH_FRAUD"},
      "t2_default": {"decision_default_norm": "LOW_RISK"},
      "t4_payoff": {"decision_payoff_norm": "LOW_PAYOFF_RISK"}
    }
  },
  "brms_flags": $BRMS_ALL_PASS
}
JSON
)"
LABEL="B" run_case "B" "$CASE_B" "REJECT" "T3_HIGH_FRAUD_VETO" "[]" "[]" "[]"

# --- Scenario C: T2_HIGH => REVIEW by T2; T4 must NOT be dominant (warning only) ---
CASE_C="$(cat <<JSON
{
  "label": "C",
  "decision_pack": {
    "meta_request_id": "sanity-C",
    "meta_client_id": "100001",
    "meta_brms_policy_snapshot": {"policy_id": "P1", "policy_version": "1.0"},
    "decisions": {
      "t3_fraud": {"decision_fraud_norm": "LOW_FRAUD"},
      "t2_default": {"decision_default_norm": "HIGH_RISK"},
      "t4_payoff": {"decision_payoff_norm": "REVIEW_PAYOFF"}
    }
  },
  "brms_flags": $BRMS_ALL_PASS
}
JSON
)"
LABEL="C" run_case "C" "$CASE_C" "REVIEW" "T2_HIGH_RISK" '["t4:review_payoff","t4:high_payoff_risk"]' '["MEDIUM_MARGIN_RISK_T4"]' '["t2:high_risk"]'

# --- Scenario D: T2_LOW + T4_HIGH => APPROVE + ALL_CLEAR + T4 warning + T4 dominant ok ---
CASE_D="$(cat <<JSON
{
  "label": "D",
  "decision_pack": {
    "meta_request_id": "sanity-D",
    "meta_client_id": "100001",
    "meta_brms_policy_snapshot": {"policy_id": "P1", "policy_version": "1.0"},
    "decisions": {
      "t3_fraud": {"decision_fraud_norm": "LOW_FRAUD"},
      "t2_default": {"decision_default_norm": "LOW_RISK"},
      "t4_payoff": {"decision_payoff_norm": "HIGH_PAYOFF_RISK"}
    }
  },
  "brms_flags": $BRMS_ALL_PASS
}
JSON
)"
LABEL="D" run_case "D" "$CASE_D" "APPROVE" "ALL_CLEAR" "[]" '["LOW_MARGIN_RISK_T4"]' '["t4:high_payoff_risk"]'

echo "[DONE] pyramid sanity OK (A/B/C/D)"
