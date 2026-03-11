from __future__ import annotations

from typing import Any, Dict, List

from runners.runtime_support import stable_score, utc_now_iso


def evaluate_mock_brms_flags(req_payload: Dict[str, Any]) -> Dict[str, Any]:
    request_id = str(req_payload.get("meta_request_id") or "mock-request")
    client_id = str(req_payload.get("meta_client_id") or "mock-client")
    applicant = req_payload.get("applicant", {}) or {}
    loan = req_payload.get("loan", {}) or {}
    ctx = req_payload.get("context", {}) or {}

    age = int(applicant.get("age") or 0)
    dti = float(applicant.get("dti") or 0.0)
    fico = int(applicant.get("fico_credit_score") or 0)
    amount = float(loan.get("loan_amount") or 0.0)
    term = int(loan.get("loan_term_months") or 0)
    employment = str(applicant.get("employment_status") or "UNKNOWN").upper()

    warnings: List[str] = []
    overrides: List[str] = []
    required_docs: List[str] = []

    gate_1 = "PASS"
    if age < 18:
        gate_1 = "BLOCK"
    elif employment == "OTHER":
        gate_1 = "WARN"
        warnings.append("EMPLOYMENT_STATUS_REVIEW")

    gate_2 = "PASS"
    if dti >= 0.72 or amount > 30000:
        gate_2 = "BLOCK"
    elif dti >= 0.45 or amount > 18000 or term > 48:
        gate_2 = "WARN"
        warnings.append("OFFER_REVIEW_REQUIRED")

    gate_3 = "PASS"
    if fico and fico < 540:
        gate_3 = "BLOCK"
    elif fico and fico < 620:
        gate_3 = "WARN"
        warnings.append("FINAL_DECISION_MANUAL_REVIEW")

    confidence = stable_score(client_id, request_id, age, dti, amount, term, floor=0.55, ceil=0.97)
    if confidence < 0.65:
        required_docs.append("proof_of_income")
    if gate_2 == "WARN" and amount > 20000:
        required_docs.append("bank_statements_90d")
    if gate_1 == "WARN":
        overrides.append("GATE_1_WARN_NOT_BLOCK")

    return {
        "meta_schema_version": "brms_flags_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": request_id,
        "meta_client_id": client_id,
        "meta_policy_id": str(ctx.get("policy_id") or "P1"),
        "meta_policy_version": str(ctx.get("policy_version") or "1.0"),
        "meta_validation_mode": str(ctx.get("validation_mode") or "TEST"),
        "meta_latency_ms": 0,
        "gates": {
            "gate_1": gate_1,
            "gate_2": gate_2,
            "gate_3": gate_3,
        },
        "warnings": warnings,
        "overrides": overrides,
        "required_docs": required_docs,
    }
