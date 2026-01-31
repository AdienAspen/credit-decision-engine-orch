#!/usr/bin/env python3
# S1.2 — Runner T3 (FRAUD) — model + thresholds -> decision (strict v0.1 fields)

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from contract_validate import validate_required, REQUIRED_T3_V0_1

from pathlib import Path
import numpy as np
import xgboost as xgb


DEFAULT_MODEL_FILE = "/home/adien/loan_backbone_ml_T3_FRAUD/models/fraud_t3_ieee_xgb_bcd_best.json"
DEFAULT_THRESHOLDS_ALIAS = "/home/adien/loan_backbone_ml_T3_FRAUD/reports/fraud_t3_ieee_bcd_best_thresholds.json"


DEFAULT_CANONICAL_ALIAS = "/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/t3_fraud_canonical.json"
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_canonical_alias(alias_path: str) -> Dict[str, str]:
    """
    Read canonical alias JSON (gov-layer). Tolerate shape variations.
    Current expected shape:
      { "model": {"model_tag": "...", "model_file": "..."}, "thresholds": {"thresholds_file": "..."} }
    """
    ap = Path(alias_path)
    if not ap.exists():
        return {}
    try:
        import json
        d = json.loads(ap.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(d, dict):
        return {}

    out: Dict[str, str] = {}

    model = d.get("model") or {}
    if isinstance(model, dict):
        mt = model.get("model_tag")
        mf = model.get("model_file")
        if isinstance(mt, str) and mt:
            out["model_tag"] = mt
        if isinstance(mf, str) and mf:
            out["model_file"] = mf

    thr = d.get("thresholds") or {}
    if isinstance(thr, dict):
        tf = thr.get("thresholds_file") or thr.get("thresholds_alias") or thr.get("thresholds_path")
        if isinstance(tf, str) and tf:
            out["thresholds_file"] = tf

    # Also tolerate flat keys (future-proof)
    if isinstance(d.get("model_file"), str) and d.get("model_file"):
        out.setdefault("model_file", d["model_file"])
    if isinstance(d.get("model_tag"), str) and d.get("model_tag"):
        out.setdefault("model_tag", d["model_tag"])
    if isinstance(d.get("thresholds_file"), str) and d.get("thresholds_file"):
        out.setdefault("thresholds_file", d["thresholds_file"])

    return out



def load_booster(model_file: str) -> xgb.Booster:
    booster = xgb.Booster()
    booster.load_model(model_file)
    return booster


def get_feature_names(booster: xgb.Booster) -> Tuple[list, int]:
    names = booster.feature_names
    if not names:
        # Fallback (rare): try f0..f{n-1}
        # But in your case we do have explicit feature names, so this is a safety net.
        n = int(getattr(booster, "num_features")())
        names = [f"f{i}" for i in range(n)]
    return list(names), len(names)


def make_synthetic_row(n_features: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Deterministic synthetic row for PoC wiring (real features will come later via EFV).
    return rng.normal(loc=0.0, scale=1.0, size=(1, n_features)).astype(np.float32)


def score_prob(booster: xgb.Booster, seed: int) -> float:
    feat_names, n_features = get_feature_names(booster)
    X = make_synthetic_row(n_features=n_features, seed=seed)
    dmat = xgb.DMatrix(X, feature_names=feat_names)
    pred = booster.predict(dmat)
    # pred can be array([p]) or shape (1,); ensure float
    return float(pred[0])


def pick_mode(thr_alias: Dict[str, Any], requested_mode: Optional[str]) -> str:
    if requested_mode:
        return requested_mode
    # default recommended mode from alias
    mode = thr_alias.get("recommended_default_mode")
    if not isinstance(mode, str) or not mode:
        raise ValueError("Threshold alias missing recommended_default_mode")
    return mode


def get_threshold(thr_alias: Dict[str, Any], mode: str) -> float:
    if mode not in thr_alias:
        raise ValueError(f"Mode '{mode}' not found in thresholds alias.")
    thr = thr_alias[mode]
    if thr is None:
        raise ValueError(f"Mode '{mode}' exists but threshold is null (None).")
    return float(thr)


def decision_from_threshold(score: float, thr: float) -> str:
    # Fraud: higher score => higher fraud risk
    return "HIGH_FRAUD" if score >= thr else "LOW_FRAUD"


def main() -> int:
    p = argparse.ArgumentParser(description="T3 FRAUD runner (model + thresholds -> decision)")
    p.add_argument("--client-id", required=True, help="Client identifier (string)")
    p.add_argument("--request-id", default=None, help="Request identifier (string)")
    p.add_argument("--seed", type=int, default=42, help="Deterministic seed (default: 42)")
    p.add_argument("--canonical-alias", default=DEFAULT_CANONICAL_ALIAS, help="Path to canonical alias JSON (swap-friendly). If provided, it supplies default model/threshold paths.")
    p.add_argument("--model-file", default=DEFAULT_MODEL_FILE, help="Path to XGBoost model (.json)")
    p.add_argument("--thresholds-alias", default=DEFAULT_THRESHOLDS_ALIAS, help="Path to thresholds alias (.json)")
    p.add_argument("--mode", default=None, help="Threshold mode key (defaults to alias recommended_default_mode)")
    args = p.parse_args()


    # Canonical alias resolution (swap-friendly defaults)
    try:
        alias = load_canonical_alias(args.canonical_alias)
        # Only override if user did not explicitly override defaults
        if alias.get("model_file") and args.model_file == DEFAULT_MODEL_FILE:
            args.model_file = alias["model_file"]
        if alias.get("thresholds_file") and args.thresholds_alias == DEFAULT_THRESHOLDS_ALIAS:
            args.thresholds_alias = alias["thresholds_file"]
        alias_model_tag = alias.get("model_tag")
    except Exception:
        alias_model_tag = None


    t0 = time.time()

    thr_alias = load_json(args.thresholds_alias)
    mode = pick_mode(thr_alias, args.mode)
    thr = get_threshold(thr_alias, mode)

    booster = load_booster(args.model_file)
    prob = score_prob(booster, seed=args.seed)
    dec = decision_from_threshold(prob, thr)

    # PolicyDecider signal (normalized fraud band)
    if prob >= thr:
        decision_fraud_norm = "HIGH_FRAUD"
    elif prob >= (0.5 * thr):
        decision_fraud_norm = "REVIEW_FRAUD"
    else:
        decision_fraud_norm = "LOW_FRAUD"
    latency_ms = int(round((time.time() - t0) * 1000.0))

    payload: Dict[str, Any] = {
        "meta_schema_version": "risk_decision_t3_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": str(args.client_id),
        "meta_model_tag": "fraud_t3_ieee_xgb_bcd_best",
        "meta_model_file": args.model_file,
        "meta_threshold_mode": mode,
        "meta_latency_ms": latency_ms,
        "score_fraud_prob": float(prob),
        "thr_fraud": float(thr),
        "decision_fraud": dec,
        "decision_fraud_norm": decision_fraud_norm,
    }

    # Minimal contract validation (v0.1)
    validate_required(payload, REQUIRED_T3_V0_1)

    print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
