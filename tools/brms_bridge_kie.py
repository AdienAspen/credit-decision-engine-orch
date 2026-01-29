#!/usr/bin/env python3
import json
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict

DEFAULT_KIE_URL = "http://localhost:8082/kie-server/services/rest/server/containers/loan_rules_1_0_9/dmn"
DEFAULT_USER = "kieserver"
DEFAULT_PASS = "KieServer123!"

DMN_NAMESPACE = "urn:com:acme:loan:decision:v1"
DMN_MODEL = "loan_decision"
DMN_DECISION = "Gate_3_FinalDecision"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _basic_auth_header(user: str, pw: str) -> str:
    import base64
    token = base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def call_kie_dmn(kie_url: str, user: str, pw: str, dmn_context: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "model-namespace": DMN_NAMESPACE,
        "model-name": DMN_MODEL,
        "decision-name": DMN_DECISION,
        "dmn-context": dmn_context,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(kie_url, method="POST", data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", _basic_auth_header(user, pw))

    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # KIE sometimes returns JSON with XML content-type; still parse as JSON.
    return json.loads(raw)


def to_brms_flags_v0_1(dmn_eval: Dict[str, Any], request_id: str, client_id: str) -> Dict[str, Any]:
    """
    Convert DMN evaluation result -> brms_flags_v0_1.
    Robust: tolerate missing/null context AND per-gate shape mismatch (dict/str/bool).
    """
    result = (dmn_eval or {}).get("result") or {}
    dmn_res = (result.get("dmn-evaluation-result") or {})
    ctx = dmn_res.get("dmn-context")

    if not isinstance(ctx, dict):
        ctx = {}

    def _truthy_str(s: str) -> bool:
        v = str(s).strip().upper()
        return v in {"PASS", "APPROVE", "APPROVED", "TRUE", "YES", "OK", "ELIGIBLE"}

    def _as_dict(x: Any) -> Dict[str, Any]:
        return x if isinstance(x, dict) else {}

    # If context is missing/null, do not crash
    if not ctx:
        return {
            "meta_schema_version": "brms_flags_v0_1",
            "meta_generated_at": datetime.now(timezone.utc).isoformat(),
            "meta_request_id": request_id,
            "meta_client_id": str(client_id),
            "meta_policy_id": "unknown",
            "meta_policy_version": "unknown",
            "meta_validation_mode": "unknown",
            "meta_latency_ms": 0,
            "gates": {"gate_1": "UNKNOWN", "gate_2": "UNKNOWN", "gate_3": "UNKNOWN"},
            "flags": ["BRMS_CONTEXT_MISSING"],
            "reasons": ["DMN context missing/null; returning UNKNOWN gates (no crash)"],
        }

    # --- Gate 1: Eligibility ---
    g1 = ctx.get("Gate_1_Eligibility")
    if isinstance(g1, dict):
        gate1_ok = bool(_as_dict(g1).get("eligible", False))
    elif isinstance(g1, (bool, int)):
        gate1_ok = bool(g1)
    elif isinstance(g1, str):
        gate1_ok = _truthy_str(g1)
    else:
        gate1_ok = False

    # --- Gate 2: Offer ---
    g2 = ctx.get("Gate_2_Offer")
    if isinstance(g2, dict):
        d2 = _as_dict(g2)
        # DMN often returns assigned_rate/tier (no "offer" key). Treat non-empty dict as PASS.
        gate2_ok = any(d2.get(k) is not None for k in ("offer", "assigned_rate", "tier", "apr", "rate"))
        if not gate2_ok:
            gate2_ok = bool(d2)
    elif isinstance(g2, str):
        # sometimes DMN returns PASS/OK or a non-empty offer id
        gate2_ok = _truthy_str(g2) or (str(g2).strip() not in {"", "NONE", "NULL"})
    elif isinstance(g2, (bool, int)):
        gate2_ok = bool(g2)
    else:
        gate2_ok = False

    # --- Gate 3: Final decision ---
    g3 = ctx.get("Gate_3_FinalDecision")
    if isinstance(g3, dict):
        gate3_ok = bool(_as_dict(g3).get("approved", False))
    elif isinstance(g3, str):
        gate3_ok = _truthy_str(g3)
    elif isinstance(g3, (bool, int)):
        gate3_ok = bool(g3)
    else:
        gate3_ok = False

    gates = {
        "gate_1": "PASS" if gate1_ok else "BLOCK",
        "gate_2": "PASS" if gate2_ok else "BLOCK",
        "gate_3": "PASS" if gate3_ok else "BLOCK",
    }

    return {
        "meta_schema_version": "brms_flags_v0_1",
        "meta_generated_at": datetime.now(timezone.utc).isoformat(),
        "meta_request_id": request_id,
        "meta_client_id": str(client_id),
        "meta_policy_id": (_as_dict(ctx.get("Context")).get("policy_id") or "unknown"),
        "meta_policy_version": (_as_dict(ctx.get("Context")).get("policy_version") or "unknown"),
        "meta_validation_mode": (_as_dict(ctx.get("Context")).get("validation_mode") or "unknown"),
        "meta_latency_ms": int((dmn_res.get("meta_latency_ms") or 0)),
        "gates": gates,
        "flags": [],
        "reasons": [],
    }
def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: brms_bridge_kie.py <brms_eval_request_v0_1.json>", file=sys.stderr)
        return 2

    req_payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())

    # Minimal contract fields (from your gov spec)
    request_id = req_payload.get("meta_request_id") or "sample"
    client_id = req_payload.get("meta_client_id") or "unknown"

    # Map ORIGINATE->BRMS contract -> DMN context (Applicant/Loan/Context)
    applicant = req_payload.get("applicant", {})
    loan = req_payload.get("loan", {})
    ctx = req_payload.get("context", {})

    dmn_context = {
        "Applicant": {
            "age": applicant.get("age"),
            "fico_credit_score": applicant.get("fico_credit_score"),
            "dti": applicant.get("dti"),
            "employment_status": applicant.get("employment_status"),
        },
        "Loan": {
            "loan_amount": loan.get("loan_amount"),
            "loan_term_months": loan.get("loan_term_months"),
        },
        "Context": {
            "policy_id": ctx.get("policy_id", "P1"),
            "policy_version": ctx.get("policy_version", "1.0"),
            "validation_mode": ctx.get("validation_mode", "TEST"),
        },
    }

    kie_url = req_payload.get("brms", {}).get("kie_url", DEFAULT_KIE_URL)
    user = req_payload.get("brms", {}).get("user", DEFAULT_USER)
    pw = req_payload.get("brms", {}).get("pass", DEFAULT_PASS)

    dmn_eval = call_kie_dmn(kie_url, user, pw, dmn_context)
    out = to_brms_flags_v0_1(dmn_eval, request_id, client_id)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
