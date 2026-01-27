#!/usr/bin/env python3
# S1.1 — RISK_T2 runner (Default)
# - Loads canonical T2 model (XGBoost JSON)
# - Applies predict_proba
# - Applies operating threshold (OP_A or OP_B) from operating_pick.json
# - Emits risk_decision_t2_v0_1 payload (Decision Pack compatible)



def _normalize_op_name(x: str) -> str:
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
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

def load_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))

import numpy as np
import xgboost as xgb


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def safe_write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def load_booster(model_json_path: Path) -> xgb.Booster:
    booster = xgb.Booster()
    booster.load_model(str(model_json_path))
    return booster


def infer_feature_dim(booster: xgb.Booster) -> int:
    """
    Best-effort: uses the internal attribute that XGBoost stores for feature count.
    Falls back to a conservative default if not present.
    """
    cfg = json.loads(booster.save_config())
    # XGBoost stores num_feature in learner->learner_model_param
    try:
        n = int(cfg["learner"]["learner_model_param"]["num_feature"])
        if n > 0:
            return n
    except Exception:
        pass
    return 100  # fallback for PoC; should be replaced by real feature vector mapping


def select_op_block(op_pick: Dict[str, Any], op_name: str) -> Dict[str, Any]:
    """
    op_name: 'op_a' or 'op_b'
    """
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


def score_default_prob(booster: xgb.Booster, n_features: int, seed: int = 42) -> float:
    """
    PoC scoring:
    - We don't yet map EFV/static features to the model feature vector.
    - We generate a deterministic pseudo-feature vector for smoke purposes.
    Replace this with real feature mapping in S1.2+.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(loc=0.0, scale=1.0, size=(1, n_features)).astype(np.float32)
    feature_names = getattr(booster, 'feature_names', None)
    if not feature_names:
        # Fallback: if model has no names, use f0..fN-1
        feature_names = [f"f{i}" for i in range(x.shape[1])]
    dmat = xgb.DMatrix(x, feature_names=feature_names)

    pred = booster.predict(dmat)
    # For binary:logistic, predict returns probability
    return float(pred[0])


def main() -> int:
    ap = argparse.ArgumentParser(description="S1.1 RISK_T2 runner (Default)")
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument(
        "--model-json",
        default="/home/adien/loan_backbone_ml_T2_DEFAULT_V2_FULLBUNDLE/models/t2_default_xgb_v3a_microA.json",
        help="Canonical XGBoost model (JSON) path",
    )
    ap.add_argument(
        "--operating-pick",
        default="/home/adien/loan_backbone_ml_T2_DEFAULT_V2_FULLBUNDLE/reports/t2_default_xgb_v3a_microA_operating_pick.json",
        help="Operating pick JSON path (contains OP_A/OP_B thresholds and metrics)",
    )
    ap.add_argument(
        "--canonical-alias",
        default="/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/block_a_gov/artifacts/t2_default_canonical.json",
        help="Path to canonical alias JSON (swap-friendly). If provided, it supplies default model/feature/operating_pick paths."
    )
    ap.add_argument(
        "--op",
        choices=["op_a", "op_b"],
        default="op_a",
        help="Operating point selector (op_a recommended, op_b high recall)",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Optional output file path (JSON). If omitted, prints to stdout.",
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
        # Fill defaults ONLY if user did NOT override via CLI
        if hasattr(args, "model_file") and args.model_file == ap.get_default("model_file"):
            args.model_file = alias_payload.get("model", {}).get("model_file", args.model_file)
        if hasattr(args, "feature_list_file") and args.feature_list_file == ap.get_default("feature_list_file"):
            args.feature_list_file = alias_payload.get("model", {}).get("feature_list_file", args.feature_list_file)
        if hasattr(args, "operating_pick") and args.operating_pick == ap.get_default("operating_pick"):
            args.operating_pick = alias_payload.get("operating", {}).get("operating_pick_file", args.operating_pick)
        op_default = alias_payload.get("operating", {}).get("default_operating_point")
        if op_default:
            for attr in ["op", "operating_point", "operating_point_id", "operating_point_name"]:
                if hasattr(args, attr) and getattr(args, attr) == ap.get_default(attr):
                    setattr(args, attr, op_default)


    t0 = time.time()
    model_path = Path(args.model_json)
    op_path = Path(args.operating_pick)

    booster = load_booster(model_path)
    n_features = infer_feature_dim(booster)

    op_pick = read_json(op_path)
    # Normalize operating point naming (accept OP_A/OP_B as well as op_a/op_b)
    if hasattr(args, "op") and args.op is not None:
        args.op = _normalize_op_name(args.op)

    op_sel = select_op_block(op_pick, args.op)
    op_key = op_sel["key"]
    op_block = op_sel["block"]

    thr = float(op_block["threshold"])
    prob = score_default_prob(booster, n_features=n_features, seed=args.seed)
    decision = "HIGH_RISK" if prob >= thr else "LOW_RISK"

    # Normalized band for PolicyDecider (MVP)
    if prob >= thr:
        decision_norm = "HIGH_RISK"
    elif prob >= 0.5 * thr:
        decision_norm = "REVIEW_RISK"
    else:
        decision_norm = "LOW_RISK"

    latency_ms = int((time.time() - t0) * 1000)

    payload: Dict[str, Any] = {
        "meta_schema_version": "risk_decision_t2_v0_1",
        "meta_generated_at": utc_now_iso(),
        "meta_request_id": args.request_id,
        "meta_client_id": args.client_id,
        "meta_model_tag": op_pick.get("tag", model_path.stem),
        "meta_model_file": str(model_path),
        "meta_operating_point": op_key,
        "meta_latency_ms": latency_ms,
        "score_default_prob": prob,
        "thr_default": thr,
        "decision_default": decision,
        "decision_default_norm": decision_norm,
        "op_ref": {
            "threshold": thr,
            "precision": float(op_block.get("precision")),
            "recall": float(op_block.get("recall")),
            "f1": float(op_block.get("f1")),
            "flag_rate": float(op_block.get("flag_rate")),
        },
    }

    if args.out:
        safe_write_json(Path(args.out), payload)
        print(f"[OK] Wrote: {args.out}")
    else:
        # --- Spec compliance: emit exact v0.1 fields only ---
        _STRICT_FIELDS = [
          'meta_schema_version',
          'meta_generated_at',
          'meta_request_id',
          'meta_client_id',
          'meta_model_tag',
          'meta_model_file',
          'meta_operating_point',
          'meta_latency_ms',
          'score_default_prob',
          'thr_default',
          'decision_default',
            'decision_default_norm',
        ]
        payload = {k: payload.get(k) for k in _STRICT_FIELDS}

        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
