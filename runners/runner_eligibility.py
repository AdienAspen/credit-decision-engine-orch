#!/usr/bin/env python3
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_CANONICAL_ALIAS = "/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/eligibility_canonical.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_intake(path: str | None) -> Dict[str, Any]:
    if path:
        return load_json(path)
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Missing input intake JSON. Use --intake-json or pipe JSON via stdin.")
    return json.loads(raw)


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _existing_customer_ok(applicant: Dict[str, Any]) -> bool:
    val = applicant.get("is_existing_customer")
    if isinstance(val, bool):
        return val
    return bool(str(applicant.get("customer_id") or "").strip())


def validate_intake_min(intake: Dict[str, Any]) -> None:
    if intake.get("meta_schema_version") != "application_intake_v0_1":
        raise ValueError("Expected meta_schema_version=application_intake_v0_1")

    applicant = intake.get("applicant", {})
    loan = intake.get("loan", {})
    ds = intake.get("dynamic_sensors_for_eligibility", {})

    for k in ["age", "income_monthly", "employment_status"]:
        if k not in applicant:
            raise ValueError(f"Missing applicant.{k}")
    if not (_existing_customer_ok(applicant) or "is_existing_customer" in applicant):
        raise ValueError("Require applicant.customer_id or applicant.is_existing_customer")

    for k in ["loan_amount", "loan_term_months"]:
        if k not in loan:
            raise ValueError(f"Missing loan.{k}")

    for k in ["dyn_bureau_employment_verified", "dyn_market_stress_score_7d"]:
        if k not in ds:
            raise ValueError(f"Missing dynamic_sensors_for_eligibility.{k}")


def evaluate_rules(intake: Dict[str, Any], alias: Dict[str, Any]) -> Tuple[str, List[str]]:
    applicant = intake.get("applicant", {})
    ds = intake.get("dynamic_sensors_for_eligibility", {})

    params = alias.get("parameters", {})
    min_age = int(params.get("MIN_AGE", 18))
    min_income = float(params.get("MIN_INCOME", 1200))
    macro_review_thr = float(params.get("MACRO_STRESS_REVIEW_THR", 0.85))

    reject_reasons: List[str] = []
    review_reasons: List[str] = []

    if not _existing_customer_ok(applicant):
        reject_reasons.append("EA_KYC_NOT_EXISTING_CUSTOMER")

    age = int(applicant.get("age", 0))
    if age < min_age:
        reject_reasons.append("EA_AGE_UNDER_MIN")

    income = float(applicant.get("income_monthly", 0.0))
    if income < min_income:
        reject_reasons.append("EA_INCOME_BELOW_MIN")

    if bool(ds.get("dyn_bureau_employment_verified")) is False:
        review_reasons.append("EA_BUREAU_EMPLOYMENT_UNVERIFIED")

    macro_stress = float(ds.get("dyn_market_stress_score_7d", 0.0))
    if macro_stress > macro_review_thr:
        review_reasons.append("EA_MACRO_STRESS_REVIEW")

    if reject_reasons:
        return "REJECTED", reject_reasons
    if review_reasons:
        return "REVIEW_REQUIRED", review_reasons
    return "APPROVED", []


def fetch_json(url: str, timeout_s: float) -> Dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("Expected dict JSON response")
    return data


def resolve_dynamic_sensors(
    intake: Dict[str, Any],
    alias: Dict[str, Any],
    sensor_mode: str,
    sensor_base_url: str,
    sensor_timeout_ms: int,
) -> Tuple[Dict[str, Any], str]:
    ds = dict(intake.get("dynamic_sensors_for_eligibility", {}) or {})
    mode_used = "STUB"
    if sensor_mode.upper() != "LIVE":
        return ds, mode_used

    client_id = str(intake.get("meta_client_id", "")).strip()
    request_id = str(intake.get("meta_request_id", "")).strip()
    as_of = intake.get("meta_as_of_ts")
    timeout_s = max(float(sensor_timeout_ms) / 1000.0, 0.1)
    base = sensor_base_url.rstrip("/")

    params = alias.get("parameters", {}) or {}
    bureau_unverified_thr = float(params.get("BUREAU_UNVERIFIED_THR", 0.8))

    mode_used = "LIVE"

    # wE -> derive employment verified from bureau spike score
    try:
        q = urllib.parse.urlencode(
            {
                "client_id": client_id,
                "lookback_hours": 24,
                "request_id": request_id,
            }
        )
        we = fetch_json(f"{base}/sensor/bureau_spike_score?{q}", timeout_s=timeout_s)
        bureau_score = float(we.get("bureau_spike_score_24h"))
        ds["dyn_bureau_employment_verified"] = bureau_score < bureau_unverified_thr
    except Exception as e:
        _eprint(f"[ELIGIBILITY][LIVE->STUB] wE fallback engaged: {e}")
        mode_used = "LIVE_FALLBACK"

    # wF -> market stress score
    try:
        wf_params = {"request_id": request_id}
        if as_of:
            wf_params["as_of"] = str(as_of)
        q = urllib.parse.urlencode(wf_params)
        wf = fetch_json(f"{base}/sensor/market_snapshot?{q}", timeout_s=timeout_s)
        ds["dyn_market_stress_score_7d"] = float(wf.get("market_stress_score_7d"))
    except Exception as e:
        # Common case: DS_Z returns 400 when provided as_of is not in snapshot range.
        # Retry once without as_of so DS_Z can use its stable default snapshot.
        retried_ok = False
        if as_of and isinstance(e, urllib.error.HTTPError) and e.code == 400:
            try:
                q = urllib.parse.urlencode({"request_id": request_id})
                wf = fetch_json(f"{base}/sensor/market_snapshot?{q}", timeout_s=timeout_s)
                ds["dyn_market_stress_score_7d"] = float(wf.get("market_stress_score_7d"))
                retried_ok = True
            except Exception as e2:
                _eprint(f"[ELIGIBILITY][LIVE->STUB] wF retry-without-as_of failed: {e2}")
        if not retried_ok:
            _eprint(f"[ELIGIBILITY][LIVE->STUB] wF fallback engaged: {e}")
            mode_used = "LIVE_FALLBACK"

    return ds, mode_used


def build_output(intake: Dict[str, Any], status: str, reasons: List[str], latency_ms: int) -> Dict[str, Any]:
    return {
        "meta_schema_version": "eligibility_agent_status_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": str(intake.get("meta_request_id", "unknown")),
        "meta_client_id": str(intake.get("meta_client_id", "unknown")),
        "meta_latency_ms": latency_ms,
        "eligibility_status": status,
        "eligibility_reasons": reasons,
    }


def validate_output(payload: Dict[str, Any]) -> None:
    required = [
        "meta_schema_version",
        "meta_generated_at",
        "meta_request_id",
        "meta_client_id",
        "meta_latency_ms",
        "eligibility_status",
        "eligibility_reasons",
    ]
    for k in required:
        if k not in payload:
            raise ValueError(f"Missing output key: {k}")

    if payload["meta_schema_version"] != "eligibility_agent_status_v0_1":
        raise ValueError("meta_schema_version must be eligibility_agent_status_v0_1")

    if payload["eligibility_status"] not in {"APPROVED", "REJECTED", "REVIEW_REQUIRED"}:
        raise ValueError("eligibility_status out of enum")

    if not isinstance(payload["eligibility_reasons"], list):
        raise ValueError("eligibility_reasons must be list")
    if "meta_sensor_mode_used" in payload and not isinstance(payload["meta_sensor_mode_used"], str):
        raise ValueError("meta_sensor_mode_used must be string")


def main() -> int:
    ap = argparse.ArgumentParser(description="Eligibility Agent runner (STUB-first, LIVE optional)")
    ap.add_argument("--intake-json", default=None, help="Path to application_intake_v0_1 JSON")
    ap.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS)
    ap.add_argument("--sensor-mode", choices=["STUB", "LIVE"], default="STUB")
    ap.add_argument("--sensor-base-url", default="http://127.0.0.1:9000")
    ap.add_argument("--sensor-timeout-ms", type=int, default=1200)
    args = ap.parse_args()

    t0 = time.time()
    alias = load_json(args.canonical_alias)
    intake = load_intake(args.intake_json)

    validate_intake_min(intake)
    resolved_ds, sensor_mode_used = resolve_dynamic_sensors(
        intake=intake,
        alias=alias,
        sensor_mode=args.sensor_mode,
        sensor_base_url=args.sensor_base_url,
        sensor_timeout_ms=args.sensor_timeout_ms,
    )
    intake["dynamic_sensors_for_eligibility"] = resolved_ds
    status, reasons = evaluate_rules(intake, alias)

    out = build_output(intake, status, reasons, int((time.time() - t0) * 1000))
    out["meta_sensor_mode_used"] = sensor_mode_used
    validate_output(out)

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
