#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path
import sys
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from contract_validate import REQUIRED_T4_V0_1, validate_required
from runners.runtime_support import load_json, resolve_project_path, stable_score, utc_now_iso

DEFAULT_MODEL_FILE = "mock_runtime/t4_payoff_model.json"
DEFAULT_THRESHOLDS_FILE = "mock_runtime/t4_payoff_thresholds.json"
DEFAULT_FEATURE_LIST_FILE = "mock_runtime/t4_payoff_feature_list.json"
DEFAULT_CANONICAL_ALIAS = "block_a_gov/artifacts/t4_payoff_canonical.json"


def collect_thr_candidates(obj) -> dict:
    out = {}
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.startswith("thr_valid_"):
                    if isinstance(v, (int, float)):
                        out[k] = float(v)
                    elif isinstance(v, dict) and isinstance(v.get("threshold"), (int, float)):
                        out[k] = float(v["threshold"])
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(obj)
    return out


def infer_mode(thr_payload: dict) -> str:
    preferred = ["thr_valid_best_f1", "thr_valid_recall_ge_0_90"]
    cand = collect_thr_candidates(thr_payload.get("panel_valid", thr_payload))
    m = thr_payload.get("recommended_default_mode")
    if isinstance(m, str) and m in cand:
        return m
    for k in preferred:
        if k in cand:
            return k
    return sorted(cand.keys())[0]


def resolve_thr(thr_payload: dict, mode: str) -> float:
    cand = collect_thr_candidates(thr_payload.get("panel_valid", thr_payload))
    if mode not in cand:
        raise KeyError(f"Threshold mode not found: {mode}")
    return float(cand[mode])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mode", default=None)
    ap.add_argument("--override-thr", type=float, default=None)
    ap.add_argument("--model-file", default=DEFAULT_MODEL_FILE)
    ap.add_argument("--thresholds-file", default=DEFAULT_THRESHOLDS_FILE)
    ap.add_argument("--feature-list-file", default=DEFAULT_FEATURE_LIST_FILE)
    ap.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS)
    args = ap.parse_args()

    alias_payload = {}
    alias_path = resolve_project_path(args.canonical_alias)
    if alias_path.exists():
        alias_payload = load_json(alias_path)
    if isinstance(alias_payload, dict):
        if args.model_file == DEFAULT_MODEL_FILE:
            args.model_file = alias_payload.get("model", {}).get("model_file", args.model_file)
        if args.thresholds_file == DEFAULT_THRESHOLDS_FILE:
            args.thresholds_file = alias_payload.get("thresholds", {}).get("thresholds_file", args.thresholds_file)
        if args.feature_list_file == DEFAULT_FEATURE_LIST_FILE:
            args.feature_list_file = alias_payload.get("model", {}).get("feature_list_file", args.feature_list_file)

    t0 = time.time()
    thr_payload = load_json(args.thresholds_file)
    mode = args.mode or infer_mode(thr_payload)
    thr = float(args.override_thr) if args.override_thr is not None else resolve_thr(thr_payload, mode)
    prob = stable_score("t4", args.client_id, args.request_id or "none", args.seed, mode)
    decision = "HIGH_PAYOFF" if prob >= thr else "LOW_PAYOFF"
    if prob >= thr:
        decision_norm = "HIGH_PAYOFF_RISK"
    elif prob >= 0.5 * thr:
        decision_norm = "REVIEW_PAYOFF"
    else:
        decision_norm = "LOW_PAYOFF_RISK"

    out = {
        "meta_schema_version": "risk_decision_t4_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": str(args.client_id),
        "meta_model_tag": alias_payload.get("model", {}).get("model_tag", Path(args.model_file).stem),
        "meta_model_file": str(resolve_project_path(args.model_file)),
        "meta_threshold_mode": mode,
        "meta_latency_ms": int((time.time() - t0) * 1000),
        "score_payoff_prob": float(prob),
        "thr_payoff": float(thr),
        "decision_payoff": decision,
        "decision_payoff_norm": decision_norm,
    }
    validate_required(out, REQUIRED_T4_V0_1)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

