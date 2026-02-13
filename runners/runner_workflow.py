#!/usr/bin/env python3
import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

DEFAULT_CANONICAL_ALIAS = "/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/eligibility_canonical.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_bool(v: Any, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return default


def load_alias(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Canonical alias not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_intake(payload: Dict[str, Any]) -> None:
    required_top = [
        "meta_schema_version",
        "meta_generated_at",
        "meta_request_id",
        "meta_client_id",
        "meta_application_id",
        "meta_channel",
        "meta_as_of_ts",
        "meta_latency_ms",
        "applicant",
        "loan",
        "dynamic_sensors_for_eligibility",
    ]
    for k in required_top:
        if k not in payload:
            raise ValueError(f"Missing required key: {k}")

    if payload["meta_schema_version"] != "application_intake_v0_1":
        raise ValueError("meta_schema_version must be application_intake_v0_1")

    a = payload["applicant"]
    l = payload["loan"]
    d = payload["dynamic_sensors_for_eligibility"]

    for k in ["age", "income_monthly", "employment_status"]:
        if k not in a:
            raise ValueError(f"Missing applicant.{k}")
    if not (bool(a.get("customer_id")) or isinstance(a.get("is_existing_customer"), bool)):
        raise ValueError("Require applicant.customer_id or applicant.is_existing_customer")

    for k in ["loan_amount", "loan_term_months"]:
        if k not in l:
            raise ValueError(f"Missing loan.{k}")

    for k in ["dyn_bureau_employment_verified", "dyn_market_stress_score_7d"]:
        if k not in d:
            raise ValueError(f"Missing dynamic_sensors_for_eligibility.{k}")


def main() -> int:
    ap = argparse.ArgumentParser(description="WORK-FLOW runner (STUB) -> application_intake_v0_1")
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--application-id", default=None)
    ap.add_argument("--channel", default="web")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS)
    ap.add_argument("--as-of-ts", default=None)
    args = ap.parse_args()

    t0 = time.time()
    alias = load_alias(args.canonical_alias)

    request_id = args.request_id or str(uuid.uuid4())
    application_id = args.application_id or f"app-{request_id[:8]}"
    as_of_ts = args.as_of_ts or utc_now_iso()

    seeded = args.seed + sum(ord(c) for c in str(args.client_id))
    rng = random.Random(seeded)

    is_existing = _as_bool(alias.get("policy", {}).get("only_existing_customers"), True)
    employment_status = ["EMPLOYED", "SELF_EMPLOYED", "OTHER"][rng.randint(0, 2)]

    payload = {
        "meta_schema_version": "application_intake_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": request_id,
        "meta_client_id": str(args.client_id),
        "meta_application_id": application_id,
        "meta_channel": str(args.channel),
        "meta_as_of_ts": as_of_ts,
        "meta_latency_ms": 0,
        "applicant": {
            "customer_id": f"cust-{args.client_id}",
            "is_existing_customer": is_existing,
            "age": 21 + rng.randint(0, 35),
            "income_monthly": float(1200 + rng.randint(0, 5000)),
            "employment_status": employment_status,
            "declared_dti": round(0.1 + rng.random() * 0.6, 4),
        },
        "loan": {
            "loan_amount": float(2000 + rng.randint(0, 30000)),
            "loan_term_months": [12, 24, 36, 48, 60][rng.randint(0, 4)],
        },
        "dynamic_sensors_for_eligibility": {
            "dyn_bureau_employment_verified": rng.random() > 0.15,
            "dyn_bureau_tenure_months": rng.randint(0, 120),
            "dyn_market_stress_score_7d": round(rng.random(), 4),
        },
    }

    payload["meta_latency_ms"] = int((time.time() - t0) * 1000)
    validate_intake(payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
