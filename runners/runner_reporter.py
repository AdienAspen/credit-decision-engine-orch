#!/usr/bin/env python3
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_pack(path: str | None) -> Dict[str, Any]:
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"decision pack not found: {path}")
        return json.loads(p.read_text(encoding="utf-8"))
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Missing decision pack input. Use --decision-pack-json or pipe JSON via stdin.")
    return json.loads(raw)


def _arr(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def _obj(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def build_report(pack: Dict[str, Any], latency_ms: int) -> Dict[str, Any]:
    decisions = _obj(pack.get("decisions"))
    final_decision = _obj(decisions.get("final_decision"))

    request_id = str(pack.get("meta_request_id", final_decision.get("meta_request_id", "unknown")))
    client_id = str(pack.get("meta_client_id", final_decision.get("meta_client_id", "unknown")))

    final_outcome = str(final_decision.get("final_outcome", "UNKNOWN"))
    final_reason = str(final_decision.get("final_reason_code", "UNKNOWN_REASON"))

    a_summary = _obj(final_decision.get("a_summary"))
    b_summary = _obj(final_decision.get("b_summary"))
    warnings = [str(x) for x in _arr(final_decision.get("warnings"))]
    dominant_signals = [str(x) for x in _arr(final_decision.get("dominant_signals"))]

    executive_summary = f"Outcome {final_outcome} due to {final_reason}."

    risk_highlights: List[str] = []
    for k in ("t2_default", "t3_fraud", "t4_payoff"):
        if k in a_summary:
            risk_highlights.append(f"{k}={a_summary[k]}")

    governance_highlights: List[str] = []
    for k in ("gate_1", "gate_2", "gate_3"):
        if k in b_summary:
            governance_highlights.append(f"{k}={b_summary[k]}")

    return {
        "meta_schema_version": "reporter_output_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": request_id,
        "meta_client_id": client_id,
        "meta_latency_ms": latency_ms,
        "decision_ref": {
            "final_outcome": final_outcome,
            "final_reason_code": final_reason,
        },
        "executive_summary": executive_summary,
        "risk_highlights": risk_highlights,
        "governance_highlights": governance_highlights,
        "warnings": warnings,
        "trace_refs": {
            "a_summary": a_summary,
            "b_summary": b_summary,
            "dominant_signals": dominant_signals,
        },
    }


def validate_output(out: Dict[str, Any]) -> None:
    required = [
        "meta_schema_version",
        "meta_generated_at",
        "meta_request_id",
        "meta_client_id",
        "meta_latency_ms",
        "decision_ref",
        "executive_summary",
        "risk_highlights",
        "governance_highlights",
        "warnings",
        "trace_refs",
    ]
    for k in required:
        if k not in out:
            raise ValueError(f"Missing output key: {k}")
    if out["meta_schema_version"] != "reporter_output_v0_1":
        raise ValueError("meta_schema_version must be reporter_output_v0_1")


def main() -> int:
    ap = argparse.ArgumentParser(description="Reporter runner (STUB-first)")
    ap.add_argument("--decision-pack-json", default=None, help="Path to decision_pack_v0_1 JSON")
    ap.add_argument("--out", default=None, help="Optional path to write reporter output JSON")
    args = ap.parse_args()

    t0 = time.time()
    pack = load_pack(args.decision_pack_json)

    decisions = _obj(pack.get("decisions"))
    if not isinstance(decisions.get("final_decision"), dict):
        raise ValueError("decision_pack must include decisions.final_decision")

    out = build_report(pack, int((time.time() - t0) * 1000))
    validate_output(out)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(out, indent=2) + "\n")

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
