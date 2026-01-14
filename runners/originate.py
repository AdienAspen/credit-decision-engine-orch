#!/usr/bin/env python3
# S1.4 — ORIGINATE (MVP) — orchestrate T2/T3/T4 -> decision_pack_v0_1

import argparse
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_json(cmd: list) -> Dict[str, Any]:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--out", default=None, help="Optional path to write decision_pack json")
    args = ap.parse_args()

    t0 = time.time()
    request_id = args.request_id or str(uuid.uuid4())

    # Sub-agents (local CLIs). Each runner reads its canonical alias by default.
    t2 = run_json(["python3", "runners/runner_t2.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    t3 = run_json(["python3", "runners/runner_t3.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    t4 = run_json(["python3", "runners/runner_t4.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])

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

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(pack, indent=2) + "\n")

    print(json.dumps(pack, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
