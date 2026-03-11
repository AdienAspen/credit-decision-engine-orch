#!/usr/bin/env python3
# S1.2 — Runner T3 (FRAUD)

import argparse
import json
import time
from pathlib import Path
import sys
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from typing import Any, Dict, Optional

from contract_validate import REQUIRED_T3_V0_1, validate_required
from runners.runtime_support import load_json, resolve_project_path, stable_score, utc_now_iso

DEFAULT_MODEL_FILE = "mock_runtime/t3_fraud_model.json"
DEFAULT_THRESHOLDS_ALIAS = "mock_runtime/t3_fraud_thresholds.json"
DEFAULT_CANONICAL_ALIAS = "block_a_gov/artifacts/t3_fraud_canonical.json"


def load_canonical_alias(alias_path: str) -> Dict[str, str]:
    ap = resolve_project_path(alias_path)
    if not ap.exists():
        return {}
    d = load_json(ap)
    out: Dict[str, str] = {}
    model = d.get("model") or {}
    thresholds = d.get("thresholds") or {}
    if isinstance(model, dict):
        if isinstance(model.get("model_tag"), str):
            out["model_tag"] = model["model_tag"]
        if isinstance(model.get("model_file"), str):
            out["model_file"] = model["model_file"]
    if isinstance(thresholds, dict) and isinstance(thresholds.get("thresholds_file"), str):
        out["thresholds_file"] = thresholds["thresholds_file"]
    return out


def pick_mode(thr_alias: Dict[str, Any], requested_mode: Optional[str]) -> str:
    if requested_mode:
        return requested_mode
    mode = thr_alias.get("recommended_default_mode")
    if not isinstance(mode, str) or not mode:
        raise ValueError("Threshold alias missing recommended_default_mode")
    return mode


def get_threshold(thr_alias: Dict[str, Any], mode: str) -> float:
    if mode not in thr_alias:
        raise ValueError(f"Mode '{mode}' not found in thresholds alias.")
    return float(thr_alias[mode])


def decision_from_threshold(score: float, thr: float) -> str:
    return "HIGH_FRAUD" if score >= thr else "LOW_FRAUD"


def main() -> int:
    p = argparse.ArgumentParser(description="T3 FRAUD runner (mock demonstrator)")
    p.add_argument("--client-id", required=True)
    p.add_argument("--request-id", default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS)
    p.add_argument("--model-file", default=DEFAULT_MODEL_FILE)
    p.add_argument("--thresholds-alias", default=DEFAULT_THRESHOLDS_ALIAS)
    p.add_argument("--mode", default=None)
    args = p.parse_args()

    alias = load_canonical_alias(args.canonical_alias)
    if alias.get("model_file") and args.model_file == DEFAULT_MODEL_FILE:
        args.model_file = alias["model_file"]
    if alias.get("thresholds_file") and args.thresholds_alias == DEFAULT_THRESHOLDS_ALIAS:
        args.thresholds_alias = alias["thresholds_file"]
    model_tag = alias.get("model_tag", Path(args.model_file).stem)

    t0 = time.time()
    thr_alias = load_json(args.thresholds_alias)
    mode = pick_mode(thr_alias, args.mode)
    thr = get_threshold(thr_alias, mode)
    prob = stable_score("t3", args.client_id, args.request_id or "none", args.seed, mode)
    dec = decision_from_threshold(prob, thr)
    if prob >= thr:
        decision_fraud_norm = "HIGH_FRAUD"
    elif prob >= (0.5 * thr):
        decision_fraud_norm = "REVIEW_FRAUD"
    else:
        decision_fraud_norm = "LOW_FRAUD"

    payload: Dict[str, Any] = {
        "meta_schema_version": "risk_decision_t3_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": str(args.client_id),
        "meta_model_tag": model_tag,
        "meta_model_file": str(resolve_project_path(args.model_file)),
        "meta_threshold_mode": mode,
        "meta_latency_ms": int(round((time.time() - t0) * 1000.0)),
        "score_fraud_prob": float(prob),
        "thr_fraud": float(thr),
        "decision_fraud": dec,
        "decision_fraud_norm": decision_fraud_norm,
    }
    validate_required(payload, REQUIRED_T3_V0_1)
    print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

