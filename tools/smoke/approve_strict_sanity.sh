#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
source .venv/bin/activate

python3 - <<'PY'
from runners.originate import policy_decider_v0_1

def mk_pack(brms_flags, t2_norm="LOW_DEFAULT", t3_norm="LOW_FRAUD", t4_norm="HIGH_PAYOFF_RISK"):
    # Minimal pack shape that matches PolicyDecider usage in originate.py:
    # decision_pack -> has "decisions" dict; policy_decider reads d = decisions
    return {
        "meta": {"request_id": "smoke", "client_id": "100001"},
        "policy": {"policy_id": "smoke_policy", "policy_version": "v0.1", "validation_mode": "smoke"},
        "decisions": {
            "t2_default": {"decision_default_norm": t2_norm},
            "t3_fraud": {"decision_fraud_norm": t3_norm},
            "t4_payoff": {"decision_payoff_norm": t4_norm},
        }
    }, brms_flags

def outcome(res: dict) -> str:
    return str(res.get("final_outcome", "")).strip().upper()

# E0: BRMS dict present but EMPTY gates -> must NOT APPROVE (this is the bug we freeze)
pack, bf = mk_pack(brms_flags={"gates": {}}, t2_norm="LOW_DEFAULT", t3_norm="LOW_FRAUD")
res = policy_decider_v0_1(decision_pack=pack, brms_flags=bf)
o = outcome(res)
assert o != "APPROVE", f"E0 expected NOT APPROVE when gates empty, got {o} | res={res}"

# E1: BRMS all PASS + T2 LOW -> APPROVE
bf_pass = {"gates": {"gate_1": {"status": "PASS"}, "gate_2": {"status": "PASS"}, "gate_3": {"status": "PASS"}}}
pack, bf = mk_pack(brms_flags=bf_pass, t2_norm="LOW_DEFAULT", t3_norm="LOW_FRAUD")
res = policy_decider_v0_1(decision_pack=pack, brms_flags=bf)
o = outcome(res)
assert o == "APPROVE", f"E1 expected APPROVE when gates pass + T2 low, got {o} | res={res}"

print("[OK] approve_strict_sanity: E0/E1 passed")
PY
