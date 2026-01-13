#!/usr/bin/env python3
# S1.2 — Runner T3 (FRAUD) — model + thresholds -> decision (strict v0.1 fields)

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import numpy as np
import xgboost as xgb


DEFAULT_MODEL_FILE = "/home/adien/loan_backbone_ml_T3_FRAUD/models/fraud_t3_ieee_xgb_bcd_best.json"
DEFAULT_THRESHOLDS_ALIAS = "/home/adien/loan_backbone_ml_T3_FRAUD/reports/fraud_t3_ieee_bcd_best_thresholds.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    p.add_argument("--model-file", default=DEFAULT_MODEL_FILE, help="Path to XGBoost model (.json)")
    p.add_argument("--thresholds-alias", default=DEFAULT_THRESHOLDS_ALIAS, help="Path to thresholds alias (.json)")
    p.add_argument("--mode", default=None, help="Threshold mode key (defaults to alias recommended_default_mode)")
    args = p.parse_args()

    t0 = time.time()

    thr_alias = load_json(args.thresholds_alias)
    mode = pick_mode(thr_alias, args.mode)
    thr = get_threshold(thr_alias, mode)

    booster = load_booster(args.model_file)
    prob = score_prob(booster, seed=args.seed)
    dec = decision_from_threshold(prob, thr)

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
    }

    print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
