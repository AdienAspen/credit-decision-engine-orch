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
    ctx = dmn_eval["result"]["dmn-evaluation-result"]["dmn-context"]

    gate1_ok = bool(ctx.get("Gate_1_Eligibility", {}).get("eligible", False))
    gate2_ok = ctx.get("Gate_2_Offer") is not None
    gate3_ok = (ctx.get("Gate_3_FinalDecision") == "Approved")

    out = {
        "meta_schema_version": "brms_flags_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": str(request_id),
        "meta_client_id": str(client_id),
        "meta_policy_id": ctx.get("Context", {}).get("policy_id"),
        "meta_policy_version": ctx.get("Context", {}).get("policy_version"),
        "meta_validation_mode": ctx.get("Context", {}).get("validation_mode"),
        "gate_1": "PASS" if gate1_ok else "BLOCK",
        "gate_2": "PASS" if gate2_ok else "BLOCK",
        "gate_3": "PASS" if gate3_ok else "BLOCK",
        "warnings": [],
        "overrides": [],
        "required_docs": [],
    }
    return out


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
