#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from contract_validate import validate_required, REQUIRED_FINAL_DECISION_V0_1

DEFAULT_BRMS_STUB = "tools/smoke/fixtures/brms_all_pass.json"
DEFAULT_BRMS_POLICY_ALIAS = "block_a_gov/artifacts/brms_policy_canonical.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_json(cmd: List[str]) -> Dict[str, Any]:
    p = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def load_brms_policy_snapshot(path: str = DEFAULT_BRMS_POLICY_ALIAS) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {
            "status": "MISSING_ALIAS",
            "alias_name": "brms_policy_canonical",
            "policy_id": "P1",
            "policy_version": "1.0",
            "bridge_base_url": "http://localhost:8090",
            "bridge_endpoint": "/bridge/brms_flags",
        }
    a = json.loads(p.read_text(encoding="utf-8"))
    return {
        "schema_version": "brms_policy_snapshot_v0_1",
        "status": "OK",
        "alias_name": a.get("alias_name", "brms_policy_canonical"),
        "policy_id": a.get("policy_id", "P1"),
        "policy_version": a.get("policy_version", "1.0"),
        "brms_flags_schema_version": a.get("brms_flags_schema_version", "brms_flags_v0_1"),
        "bridge_base_url": (a.get("bridge") or {}).get("base_url", "http://localhost:8090"),
        "bridge_endpoint": (a.get("bridge") or {}).get("endpoint", "/bridge/brms_flags"),
    }


def reason_to_signal(reason: str) -> str:
    if reason.startswith("EA_"):
        return f"eligibility_agent:{reason.lower()}"
    return "eligibility_agent:decision"


def make_early_final_decision(
    request_id: str,
    client_id: str,
    policy_id: str,
    policy_version: str,
    eligibility_status: str,
    reasons: List[str],
    latency_ms: int,
) -> Dict[str, Any]:
    if eligibility_status == "REJECTED":
        final_outcome = "REJECT"
    else:
        final_outcome = "REVIEW"

    primary_reason = reasons[0] if reasons else ("EA_REJECTED" if final_outcome == "REJECT" else "EA_REVIEW_REQUIRED")
    dominant = [reason_to_signal(primary_reason)]

    out = {
        "meta_schema_version": "final_decision_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": request_id,
        "meta_client_id": client_id,
        "meta_latency_ms": latency_ms,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "validation_mode": "eligibility_agent_early_cut",
        "final_outcome": final_outcome,
        "final_reason_code": primary_reason,
        "dominant_signals": dominant,
        "required_docs": [],
        "warnings": reasons,
        "overrides_applied": [],
        "a_summary": {
            "eligibility_agent": eligibility_status,
        },
        "b_summary": None,
    }
    validate_required(out, REQUIRED_FINAL_DECISION_V0_1, where="workflow_eligibility:final_decision_early_cut")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WORK-FLOW + Eligibility mini-orchestrator (STUB-first)")
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--channel", default="web")
    ap.add_argument("--workflow-canonical-alias", default="/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/eligibility_canonical.json")
    ap.add_argument("--eligibility-canonical-alias", default="/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/eligibility_canonical.json")
    ap.add_argument("--sensor-mode", choices=["STUB", "LIVE"], default="STUB")
    ap.add_argument("--sensor-base-url", default="http://127.0.0.1:9000")
    ap.add_argument("--sensor-timeout-ms", type=int, default=1200)
    ap.add_argument("--brms-url", default="http://localhost:8090/bridge/brms_flags")
    ap.add_argument("--brms-stub", default=DEFAULT_BRMS_STUB)
    ap.add_argument("--no-brms", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    t0 = time.time()
    request_id = args.request_id or str(uuid.uuid4())

    # 1) WORK-FLOW intake
    wf_cmd = [
        sys.executable,
        "runners/runner_workflow.py",
        "--client-id",
        str(args.client_id),
        "--seed",
        str(args.seed),
        "--request-id",
        request_id,
        "--channel",
        args.channel,
        "--canonical-alias",
        args.workflow_canonical_alias,
    ]
    intake = run_json(wf_cmd)

    # 2) Eligibility using the generated intake
    with tempfile.NamedTemporaryFile(mode="w", suffix="_intake.json", delete=False, encoding="utf-8") as tf:
        json.dump(intake, tf)
        intake_path = tf.name
    try:
        elig_cmd = [
            sys.executable,
            "runners/runner_eligibility.py",
            "--intake-json",
            intake_path,
            "--canonical-alias",
            args.eligibility_canonical_alias,
            "--sensor-mode",
            args.sensor_mode,
            "--sensor-base-url",
            args.sensor_base_url,
            "--sensor-timeout-ms",
            str(args.sensor_timeout_ms),
        ]
        eligibility = run_json(elig_cmd)
    finally:
        try:
            os.unlink(intake_path)
        except OSError:
            pass

    policy_snapshot = load_brms_policy_snapshot()

    # 3) Branch by eligibility decision
    elig_status = str(eligibility.get("eligibility_status", "")).upper()
    elig_reasons = eligibility.get("eligibility_reasons") or []

    if elig_status in {"REJECTED", "REVIEW_REQUIRED"}:
        latency_ms = int((time.time() - t0) * 1000)
        final_decision = make_early_final_decision(
            request_id=request_id,
            client_id=str(args.client_id),
            policy_id=str(policy_snapshot.get("policy_id", "P1")),
            policy_version=str(policy_snapshot.get("policy_version", "1.0")),
            eligibility_status=elig_status,
            reasons=list(elig_reasons),
            latency_ms=latency_ms,
        )
        pack = {
            "meta_schema_version": "decision_pack_v0_1",
            "meta_generated_at": utc_now_iso(),
            "meta_request_id": request_id,
            "meta_client_id": str(args.client_id),
            "meta_latency_ms": latency_ms,
            "meta_brms_policy_snapshot": policy_snapshot,
            "decisions": {
                "workflow_intake": intake,
                "eligibility": eligibility,
                "final_decision": final_decision,
            },
        }
    else:
        orig_cmd = [
            sys.executable,
            "runners/originate.py",
            "--client-id",
            str(args.client_id),
            "--seed",
            str(args.seed),
            "--request-id",
            request_id,
        ]
        if args.no_brms:
            orig_cmd.append("--no-brms")
        elif args.brms_stub:
            orig_cmd.extend(["--brms-stub", args.brms_stub])
        else:
            orig_cmd.extend(["--brms-url", args.brms_url])

        pack = run_json(orig_cmd)
        pack.setdefault("decisions", {})["workflow_intake"] = intake
        pack.setdefault("decisions", {})["eligibility"] = eligibility

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(pack, indent=2) + "\n")

    print(json.dumps(pack, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
