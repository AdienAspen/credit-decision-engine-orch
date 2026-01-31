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
from typing import Any, Dict, Optional
from contract_validate import validate_required, REQUIRED_T2_V0_1, REQUIRED_T3_V0_1, REQUIRED_T4_V0_1


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



def load_brms_policy_snapshot() -> Dict[str, Any]:
    """
    Stable policy snapshot (spec-first) loaded from canonical alias JSON.
    This avoids coupling ORIGINATE to the bridge internals.
    """
    alias_path = Path("block_a_gov/artifacts/brms_policy_canonical.json")
    if not alias_path.exists():
        return {
            "schema_version": "brms_policy_snapshot_v0_1",
            "status": "MISSING_ALIAS",
            "alias_path": str(alias_path),
        }

    d = json.loads(alias_path.read_text(encoding="utf-8"))
    bridge = d.get("bridge", {}) or {}

    return {
        "schema_version": "brms_policy_snapshot_v0_1",
        "status": "OK",
        "alias_name": d.get("alias_name"),
        "policy_id": d.get("policy_id"),
        "policy_version": d.get("policy_version"),
        "brms_flags_schema_version": d.get("brms_flags_schema_version"),
        "bridge_base_url": bridge.get("base_url"),
        "bridge_endpoint": bridge.get("endpoint"),
    }


def _a_summary_from_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a minimal A summary for auditing.
    Keep it stable and small; do not leak full runner payloads.
    """
    d = (pack or {}).get("decisions", {}) or {}
    t2 = d.get("t2_default", {}) or {}
    t3 = d.get("t3_fraud", {}) or {}
    t4 = d.get("t4_payoff", {}) or {}

    return {
        "t2_default": t2.get("decision_default_norm", t2.get("decision_default", "UNKNOWN")),
        "t3_fraud": t3.get("decision_fraud_norm", t3.get("decision_fraud", "UNKNOWN")),
        "t4_payoff": t4.get("decision_payoff_norm", t4.get("decision_payoff", "UNKNOWN")),
    }


def _b_summary_from_flags(brms_flags: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not brms_flags:
        return None
    gates = brms_flags.get("gates", {}) or {}
    return {
        "gate_1": gates.get("gate_1"),
        "gate_2": gates.get("gate_2"),
        "gate_3": gates.get("gate_3"),
    }


def policy_decider_v0_1(
    *,
    decision_pack: Dict[str, Any],
    brms_flags: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Deterministic Policy Engine (v0.1) — pure function.
    Priority pyramid:
      Eligibility > BRMS hard blocks > Fraud > Default > Payoff
    """
    now = utc_now_iso()
    request_id = (decision_pack or {}).get("meta_request_id", "unknown")
    client_id = (decision_pack or {}).get("meta_client_id", "unknown")

    snap = (decision_pack or {}).get("meta_brms_policy_snapshot", {}) or {}
    policy_id = snap.get("policy_id", "unknown")
    policy_version = snap.get("policy_version", "unknown")
    validation_mode = "unknown"
    if brms_flags:
        policy_id = brms_flags.get("meta_policy_id", policy_id)
        policy_version = brms_flags.get("meta_policy_version", policy_version)
        validation_mode = brms_flags.get("meta_validation_mode", validation_mode)

    final_outcome = "REVIEW"
    reason_code = "MVP_REVIEW_DEFAULT"
    dominant_signals: list = []
    required_docs: list = []
    warnings: list = []
    overrides_applied: list = []

    def _set_review(reason: str, signal: str) -> None:
        nonlocal final_outcome, reason_code, dominant_signals
        # Set REVIEW only if we are not already REJECT and reason is still default
        if final_outcome != "REJECT":
            if final_outcome != "REVIEW" or reason_code == "MVP_REVIEW_DEFAULT":
                final_outcome = "REVIEW"
                reason_code = reason
            dominant_signals.append(signal)


    if not brms_flags:
        warnings.append("BRMS_UNAVAILABLE_FAIL_OPEN")

    d = (decision_pack or {}).get("decisions", {}) or {}

    # 1) Eligibility (if present) veto
    elig = d.get("eligibility", {}) or {}
    elig_status = elig.get("eligibility_status") or elig.get("decision_eligibility") or elig.get("status")
    if isinstance(elig_status, str) and elig_status.upper() in {"INELIGIBLE", "REJECT", "BLOCK"}:
        final_outcome = "REJECT"
        reason_code = "ELIGIBILITY_FAIL"
        dominant_signals.append("eligibility:fail")

    # 2) BRMS hard blocks veto
    if final_outcome != "REJECT" and brms_flags:
        gates = brms_flags.get("gates", {}) or {}
        g1, g2, g3 = gates.get("gate_1"), gates.get("gate_2"), gates.get("gate_3")
        if any(x == "FAIL" for x in [g1, g2, g3]):
            final_outcome = "REJECT"
            reason_code = "BRMS_GATE_FAIL"
            if g1 == "FAIL": dominant_signals.append("brms:gate_1_fail")
            if g2 == "FAIL": dominant_signals.append("brms:gate_2_fail")
            if g3 == "FAIL": dominant_signals.append("brms:gate_3_fail")

    # 3) Fraud (T3)
    if final_outcome != "REJECT":
        t3 = d.get("t3_fraud", {}) or {}
        fraud_norm = t3.get("decision_fraud_norm") or t3.get("decision_fraud")
        if fraud_norm == "HIGH_FRAUD":
            final_outcome = "REJECT"
            reason_code = "T3_HIGH_FRAUD_VETO"
            dominant_signals.append("t3:high_fraud")
        elif fraud_norm == "REVIEW_FRAUD":
            final_outcome = "REVIEW"
            reason_code = "T3_REVIEW_FRAUD"
            dominant_signals.append("t3:review_fraud")

    # 4) Default risk (T2)
    if final_outcome != "REJECT":
        t2 = d.get("t2_default", {}) or {}
        t2_norm = t2.get("decision_default_norm") or t2.get("decision_default")
        if t2_norm == "HIGH_RISK":
            _set_review("T2_HIGH_RISK", "t2:high_risk")
        elif t2_norm == "REVIEW_RISK":
            _set_review("T2_REVIEW_RISK", "t2:review_risk")
    # T2-driven outcome/reason => T4 must not become dominant
    t2_driven = reason_code.startswith("T2_")

    # 5) Payoff (T4) — NON-BLOCKING (margin/offer only)
    # T4 must NOT change final_outcome/reason_code in v0.1 credit decision.
    # It may only add secondary dominant_signals and warnings/overrides.
    # MARKER: T4_NON_BLOCKING_MARGIN_ONLY
    if final_outcome != "REJECT":
        t4 = d.get("t4_payoff", {}) or {}
        t4_norm = t4.get("decision_payoff_norm") or t4.get("decision_payoff")
        if t4_norm == "HIGH_PAYOFF_RISK":
            # T4 is non-blocking: only dominant when nothing else set
            if (not t2_driven) and (reason_code == "MVP_REVIEW_DEFAULT"):
                dominant_signals.append("t4:high_payoff_risk")

            warnings.append("LOW_MARGIN_RISK_T4")
        elif t4_norm == "REVIEW_PAYOFF":
            # T4 is non-blocking: only dominant when nothing else set
            if (not t2_driven) and (reason_code == "MVP_REVIEW_DEFAULT"):
                dominant_signals.append("t4:review_payoff")

            warnings.append("MEDIUM_MARGIN_RISK_T4")


    # Approve only when BRMS is present and gates PASS (strict freeze)
    # MARKER: APPROVE_STRICT_V0_1
    if final_outcome == "REVIEW" and reason_code == "MVP_REVIEW_DEFAULT" and (not t2_driven):
        if brms_flags is None:
            final_outcome = "REVIEW"
            reason_code = "BRMS_UNAVAILABLE_FAIL_OPEN"
        else:
            # Normalize BRMS flags shape (bridge may wrap payload)
            bf = brms_flags
            if isinstance(bf, dict) and "gates" not in bf:
                for k in ("brms_flags_v0_1", "brms_flags", "payload", "data"):
                    v = bf.get(k)
                    if isinstance(v, dict) and ("gates" in v or "flags" in v or "reasons" in v):
                        bf = v
                        break

            gates = bf.get("gates") if isinstance(bf, dict) else None

            def _is_pass_like(x):
                s = str(x).strip().upper()
                return s in ("PASS", "OK", "ALLOW", "APPROVE")

            brms_all_pass = False
            if isinstance(gates, dict) and gates:
                statuses = []
                for _, gv in gates.items():
                    if isinstance(gv, dict):
                        statuses.append(gv.get("status"))
                    else:
                        statuses.append(gv)
                brms_all_pass = all((st is not None and _is_pass_like(st)) for st in statuses)

            if not brms_all_pass:
                final_outcome = "REVIEW"
                reason_code = "APPROVE_BLOCKED_BY_STRICT_RULE"
            else:
                final_outcome = "APPROVE"
                reason_code = "ALL_CLEAR"

    return {
        "meta_schema_version": "final_decision_v0_1",
        "meta_generated_at": now,
        "meta_request_id": request_id,
        "meta_client_id": str(client_id),
        "policy_id": str(policy_id),
        "policy_version": str(policy_version),
        "validation_mode": str(validation_mode),
        "final_outcome": final_outcome,
        "final_reason_code": reason_code,
        "dominant_signals": dominant_signals[:5],
        "required_docs": required_docs,
        "warnings": warnings,
        "overrides_applied": overrides_applied,
        "a_summary": _a_summary_from_pack(decision_pack),
        "b_summary": _b_summary_from_flags(brms_flags),
    }


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
    validate_required(t2, REQUIRED_T2_V0_1, where="originate:t2_default")
    t3 = run_json([sys.executable, "runners/runner_t3.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    validate_required(t3, REQUIRED_T3_V0_1, where="originate:t3_fraud")
    t4 = run_json([sys.executable, "runners/runner_t4.py", "--client-id", str(args.client_id), "--seed", str(args.seed), "--request-id", request_id])
    validate_required(t4, REQUIRED_T4_V0_1, where="originate:t4_payoff")

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

    # BRMS policy snapshot (stable indirection; loaded from canonical alias)
    pack["meta_brms_policy_snapshot"] = load_brms_policy_snapshot()


    # BRMS bridge (online) — fail-open (MVP)
    if (not args.no_brms) and args.brms_url:
        try:
            brms_payload = {
                "meta_request_id": request_id,
                "meta_client_id": str(args.client_id),
                "applicant": {"age": 30, "fico_credit_score": 700, "dti": 0.2, "employment_status": "EMPLOYED"},
                "loan": {"loan_amount": 10000, "loan_term_months": 36},
                "context": {"policy_id": "P1", "policy_version": "1.0", "validation_mode": "TEST"}
            }
            brms_flags = fetch_brms_flags(args.brms_url, brms_payload)
            # MARKER: BRMS_FLAGS_SNAPSHOT_V0_1
            # Persist BRMS flags snapshot for E2E debugging (best-effort)
            try:
                from pathlib import Path as _Path
                import json as _json
                _Path('tools/smoke/_logs').mkdir(parents=True, exist_ok=True)
                _Path('tools/smoke/_logs/last_brms_flags.json').write_text(_json.dumps(brms_flags, indent=2, default=str), encoding='utf-8')
            except Exception:
                pass
        except Exception as e:
            brms_flags = None

    if brms_flags is not None:
        pack["decisions"]["brms_flags"] = brms_flags

    # PolicyDecider v0.1 (pure) — emit final_decision_v0_1

    pack["decisions"]["final_decision"] = policy_decider_v0_1(decision_pack=pack, brms_flags=brms_flags)


    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(pack, indent=2) + "\n")

    print(json.dumps(pack, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
