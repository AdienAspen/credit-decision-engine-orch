#!/usr/bin/env python3
# S1.1 — RISK_T2 runner (Default)

import argparse
import json
import time
from pathlib import Path
import sys
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from typing import Any, Dict

from contract_validate import REQUIRED_T2_V0_1, validate_required
from runners.runtime_support import load_json, resolve_project_path, stable_score, utc_now_iso


DEFAULT_CANONICAL_ALIAS = "block_a_gov/artifacts/t2_default_canonical.json"
DEFAULT_MODEL_FILE = "mock_runtime/t2_default_model.json"
DEFAULT_OPERATING_PICK = "mock_runtime/t2_default_operating_pick.json"


def _normalize_op_name(x: str | None) -> str | None:
    if x is None:
        return x
    v = str(x).strip()
    if not v:
        return v
    v_up = v.upper()
    if v_up == "OP_A":
        return "op_a"
    if v_up == "OP_B":
        return "op_b"
    return v.lower()


def select_op_block(op_pick: Dict[str, Any], op_name: str) -> Dict[str, Any]:
    if op_name == "op_a":
        key = "op_a_best_f1_under_flag"
    elif op_name == "op_b":
        key = "op_b_max_recall_under_flag"
    else:
        raise ValueError("Invalid op_name. Use op_a or op_b.")

    block = op_pick.get("test", {}).get(key) or op_pick.get("valid", {}).get(key)
    if not block:
        raise ValueError(f"Operating pick block not found for {key} (valid/test).")
    return {"key": key, "block": block}


def main() -> int:
    ap = argparse.ArgumentParser(description="S1.1 RISK_T2 runner (Default)")
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model-json", default=DEFAULT_MODEL_FILE)
    ap.add_argument("--operating-pick", default=DEFAULT_OPERATING_PICK)
    ap.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS)
    ap.add_argument("--op", choices=["op_a", "op_b"], default="op_a")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    alias_payload = {}
    alias_path = resolve_project_path(args.canonical_alias)
    if alias_path.exists():
        alias_payload = load_json(alias_path)

    model_file = alias_payload.get("model", {}).get("model_file", args.model_json)
    operating_pick_file = alias_payload.get("operating", {}).get("operating_pick_file", args.operating_pick)
    model_tag = alias_payload.get("model", {}).get("model_tag", Path(model_file).stem)
    args.op = _normalize_op_name(args.op)

    t0 = time.time()
    op_pick = load_json(operating_pick_file)
    op_sel = select_op_block(op_pick, args.op)
    op_key = op_sel["key"]
    op_block = op_sel["block"]

    thr = float(op_block["threshold"])
    prob = stable_score("t2", args.client_id, args.request_id or "none", args.seed, args.op)
    decision = "HIGH_RISK" if prob >= thr else "LOW_RISK"
    if prob >= thr:
        decision_norm = "HIGH_RISK"
    elif prob >= 0.5 * thr:
        decision_norm = "REVIEW_RISK"
    else:
        decision_norm = "LOW_RISK"

    payload: Dict[str, Any] = {
        "meta_schema_version": "risk_decision_t2_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": args.client_id,
        "meta_model_tag": model_tag,
        "meta_model_file": str(resolve_project_path(model_file)),
        "meta_operating_point": op_key,
        "meta_latency_ms": int((time.time() - t0) * 1000),
        "score_default_prob": prob,
        "thr_default": thr,
        "decision_default": decision,
        "decision_default_norm": decision_norm,
    }
    validate_required(payload, REQUIRED_T2_V0_1)

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

