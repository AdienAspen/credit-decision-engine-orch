#!/usr/bin/env python3
# Minimal BRMS Bridge Server (HTTP) -> returns brms_flags_v0_1
from fastapi import FastAPI, HTTPException
from typing import Any, Dict
import time

from tools.brms_bridge_kie import call_kie_dmn, to_brms_flags_v0_1, DEFAULT_KIE_URL, DEFAULT_USER, DEFAULT_PASS

app = FastAPI()

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}

@app.post("/bridge/brms_flags")
def bridge_brms_flags(req_payload: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal contract fields
    request_id = req_payload.get("meta_request_id") or "sample"
    client_id = req_payload.get("meta_client_id") or "unknown"

    applicant = req_payload.get("applicant", {}) or {}
    loan = req_payload.get("loan", {}) or {}
    ctx = req_payload.get("context", {}) or {}

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

    brms = req_payload.get("brms", {}) or {}
    kie_url = brms.get("kie_url", DEFAULT_KIE_URL)
    user = brms.get("user", DEFAULT_USER)
    pw = brms.get("pass", DEFAULT_PASS)

    t0 = time.time()
    try:
        dmn_eval = call_kie_dmn(kie_url, user, pw, dmn_context)
        out = to_brms_flags_v0_1(dmn_eval, request_id, client_id)
        out["meta_latency_ms"] = int((time.time() - t0) * 1000)
        return out
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"BRMS bridge failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
