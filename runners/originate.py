#!/usr/bin/env python3
# S1.4 — ORIGINATE (MVP) — orchestrate T2/T3/T4 -> decision_pack_v0_1

import argparse
import json
import subprocess
import time
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_json(cmd: list) -> Dict[str, Any]:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)

def fetch_brms_flags(brms_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal HTTP client (MVP). Block B returns brms_flags_v0_1.
    try:
        import requests
    except Exception as e:
        raise RuntimeError("requests is required for BRMS bridge (pip install requests)") from e
    t0 = time.time()
    r = requests.post(brms_url, json=payload, timeout=10)
    r.raise_for_status()
    out = r.json()
    # If BRMS does not include latency, add it here (non-breaking additive for our internal use).
    if isinstance(out, dict) and "meta_latency_ms" not in out:
        out["meta_latency_ms"] = int((time.time() - t0) * 1000)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--out", default=None, help="Optional path to write decision_pack json")
    ap.add_argument("--brms-url", default="http://localhost:8082/bridge/brms_flags", help="BRMS flags endpoint (Block B -> ORIGINATE)")
    ap.add_argument("--brms-stub", default=None, help="Path to brms_flags_v0_1 JSON (offline stub)")
    ap.add_argument("--no-brms", action="store_true", help="Skip BRMS call (offline mode)")
    args = ap.parse_args()
    t0 = time.time()
    request_id = args.request_id or str(uuid.uuid4())
    brms_flags = None
    if args.brms_stub:
        brms_flags = json.loads(Path(args.brms_stub).read_text(encoding="utf-8"))
        args.no_brms = True
    # Sub-agents (local CLIs). Each runner reads its canonical alias by default.
    t2 = run_json([sys.executable, "runners/runner_t2.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    t3 = run_json([sys.executable, "runners/runner_t3.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    t4 = run_json([sys.executable, "runners/runner_t4.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])

    latency_ms = int((time.time() - t0) * 1000)

    pack = {
        "meta_schema_version": "decision_pack_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": request_id,
        "meta_client_id": str(args.client_id),
        "meta_latency_ms": latency_ms,
        "decisions": {
            "t2_default": t2,
            "t3_fraud": t3,
            "t4_payoff": t4
        }
      }


    # BRMS bridge (online) — fail-open (MVP)
    if (not args.no_brms) and args.brms_url:
        try:
            brms_payload = {
                "meta_request_id": request_id,
                "meta_client_id": str(args.client_id),
                "Applicant": {},
                "Loan": {},
                "Context": {"policy_id": "P1", "policy_version": "1.0", "validation_mode": "TEST"}
            }
            brms_flags = fetch_brms_flags(args.brms_url, brms_payload)
        except Exception as e:
            brms_flags = None

    if brms_flags is not None:
        pack["decisions"]["brms_flags"] = brms_flags

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(pack, indent=2) + "\n")

    print(json.dumps(pack, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
