#!/usr/bin/env python3
import argparse, json, time
from datetime import datetime, timezone

from pathlib import Path
import sys
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
from contract_validate import validate_required, REQUIRED_T4_V0_1
from pathlib import Path

import numpy as np
import xgboost as xgb

try:
    import joblib
except Exception:
    joblib = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def collect_thr_candidates(obj) -> dict:
    """
    Recursively collect threshold modes like 'thr_valid_*'.

    Supports:
      - numeric: thr_valid_*: 0.36
      - dict payload: thr_valid_*: {"threshold": 0.36, ...}

    Returns: {mode_key: threshold_float}
    """
    out = {}

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.startswith("thr_valid_"):
                    # Case A: direct numeric
                    if isinstance(v, (int, float)):
                        out[k] = float(v)
                    # Case B: dict containing "threshold"
                    elif isinstance(v, dict) and isinstance(v.get("threshold"), (int, float)):
                        out[k] = float(v["threshold"])
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return out


def infer_mode(thr_payload: dict) -> str:
    # preferred ordering (same spirit as T2/T3):
    preferred = [
        "thr_valid_best_f1",
        "thr_valid_recall_ge_0_90",
        "thr_valid_recall_ge_0_95",
        "thr_valid_precision_ge_0_70",
    ]

    # Prefer panel_valid if present (this is where thresholds are defined)
    base = thr_payload.get("panel_valid")
    if not isinstance(base, dict):
        base = thr_payload

    cand = collect_thr_candidates(base)

    # 1) explicit recommended key if present AND exists in candidates
    m = thr_payload.get("recommended_default_mode")
    if isinstance(m, str) and m.strip() and m.strip() in cand:
        return m.strip()

    # 2) pick from preferred list
    for k in preferred:
        if k in cand:
            return k

    # 3) last resort: deterministic first available
    if cand:
        return sorted(cand.keys())[0]

    raise KeyError("No thr_valid_* thresholds found (numeric or dict-with-'threshold') in thresholds JSON.")


def resolve_thr(thr_payload: dict, mode: str) -> float:
    # Prefer panel_valid if present
    base = thr_payload.get("panel_valid")
    if not isinstance(base, dict):
        base = thr_payload

    # Fast path: direct numeric or dict with "threshold"
    if isinstance(base, dict) and mode in base:
        v = base.get(mode)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict) and isinstance(v.get("threshold"), (int, float)):
            return float(v["threshold"])

    # Recursive candidates
    cand = collect_thr_candidates(base)
    if mode in cand:
        return float(cand[mode])

    raise KeyError(f"Threshold mode not found: {mode}. Available: {sorted(cand.keys())[:30]}")


def load_feature_names(p: Path):
    payload = load_json(p)
    if isinstance(payload, list):
        return [str(x) for x in payload]
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return [str(x) for x in payload["features"]]
    raise ValueError("Unsupported feature list format (expected list or {'features':[...]}).")


def load_model(path: Path):
    suf = path.suffix.lower()
    if suf == ".json":
        b = xgb.Booster()
        b.load_model(str(path))
        return ("booster", b)
    if suf in (".joblib", ".pkl"):
        if joblib is None:
            raise SystemExit("joblib required for .joblib/.pkl model files.")
        return ("obj", joblib.load(str(path)))
    raise ValueError(f"Unsupported model file extension: {path}")


def predict_prob(kind, model, X, feature_names):
    dmat = xgb.DMatrix(X, feature_names=feature_names)
    if kind == "booster":
        return float(model.predict(dmat)[0])
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(X)[0, 1])
    if hasattr(model, "predict"):
        return float(model.predict(dmat)[0])
    raise TypeError("Model has no usable predict method.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mode", default=None, help="e.g. thr_valid_best_f1 / thr_valid_recall_ge_0_90 ...")
    ap.add_argument("--override-thr", type=float, default=None, help="TEST ONLY: override threshold value")
    ap.add_argument(
        "--model-file",
        default="/home/adien/loan_backbone_ml_T4_PAYOFF/models/t4_payoff_xgb_v1_guarded.json",
    )
    ap.add_argument(
        "--thresholds-file",
        default="/home/adien/loan_backbone_ml_T4_PAYOFF/reports/t4_payoff_xgb_v1_guarded_thresholds.json",
    )
    ap.add_argument(
        "--feature-list-file",
        default="/home/adien/loan_backbone_ml_T4_PAYOFF/reports/t4_payoff_xgb_v1_guarded_feature_list.json",
    )
    ap.add_argument(
        "--canonical-alias",
        default="/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/t4_payoff_canonical.json",
        help="Path to canonical alias JSON (swap-friendly). If provided, it supplies default model/threshold/feature paths."
    )
    args = ap.parse_args()

    # Canonical alias resolution (swap-friendly defaults)
    alias_payload = None
    try:
        alias_path = Path(args.canonical_alias)
        if alias_path.exists():
            alias_payload = load_json(alias_path)
    except Exception:
        alias_payload = None

    if isinstance(alias_payload, dict):
        # Only fill defaults if user did NOT explicitly override via CLI
        if args.model_file == ap.get_default("model_file"):
            args.model_file = alias_payload.get("model", {}).get("model_file", args.model_file)
        if args.thresholds_file == ap.get_default("thresholds_file"):
            args.thresholds_file = alias_payload.get("thresholds", {}).get("thresholds_file", args.thresholds_file)
        if args.feature_list_file == ap.get_default("feature_list_file"):
            args.feature_list_file = alias_payload.get("model", {}).get("feature_list_file", args.feature_list_file)

    t0 = time.time()
    model_path = Path(args.model_file)
    thr_path = Path(args.thresholds_file)
    feat_path = Path(args.feature_list_file)

    thr_payload = load_json(thr_path)
    mode = args.mode or infer_mode(thr_payload)
    thr = resolve_thr(thr_payload, mode)


    if args.override_thr is not None:
        thr = float(args.override_thr)
    feature_names = load_feature_names(feat_path)
    n = len(feature_names)

    rng = np.random.default_rng(args.seed)
    X = rng.normal(0, 1, size=(1, n)).astype(np.float32)

    kind, model = load_model(model_path)
    prob = predict_prob(kind, model, X, feature_names)

    # NOTE: payoff = positive class => HIGH_PAYOFF if prob >= thr
    decision = "HIGH_PAYOFF" if prob >= thr else "LOW_PAYOFF"

    # Normalized band for PolicyDecider (MVP)
    if prob >= thr:
        decision_norm = "HIGH_PAYOFF_RISK"
    elif prob >= 0.5 * thr:
        decision_norm = "REVIEW_PAYOFF"
    else:
        decision_norm = "LOW_PAYOFF_RISK"

    latency_ms = int((time.time() - t0) * 1000)

    out = {
        "meta_schema_version": "risk_decision_t4_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": str(args.client_id),
        "meta_model_tag": model_path.stem,
        "meta_model_file": str(model_path),
        "meta_threshold_mode": mode,
        "meta_latency_ms": latency_ms,
        "score_payoff_prob": float(prob),
        "thr_payoff": float(thr),
        "decision_payoff": decision,
        "decision_payoff_norm": decision_norm,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
