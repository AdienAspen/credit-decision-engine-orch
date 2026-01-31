#!/usr/bin/env python3
"""
Minimal contract validation helpers for runner payloads (v0.1).
Goal: fail fast with clear error if required fields are missing / wrong type.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


class ContractValidationError(ValueError):
    pass


def _is_nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_required(payload: Dict[str, Any], checks: Iterable[Tuple[str, str]], where: str = "") -> None:
    """
    checks: list of (field_name, kind)
      kind in {"str", "nonempty_str", "number", "dict"}
    """
    if not isinstance(payload, dict):
        raise ContractValidationError("Payload must be a dict")

    missing = []
    bad = []

    for key, kind in checks:
        if key not in payload:
            missing.append(key)
            continue

        v = payload.get(key)

        if kind == "str":
            if not isinstance(v, str):
                bad.append(f"{key}: expected str, got {type(v).__name__}")
        elif kind == "nonempty_str":
            if not _is_nonempty_str(v):
                bad.append(f"{key}: expected non-empty str")
        elif kind == "number":
            if not _is_number(v):
                bad.append(f"{key}: expected number, got {type(v).__name__}")
        elif kind == "dict":
            if not isinstance(v, dict):
                bad.append(f"{key}: expected dict, got {type(v).__name__}")
        else:
            bad.append(f"{key}: unknown check kind '{kind}'")

    if missing or bad:
        prefix = f"[{where}] " if where else ""
        msg = prefix + "Contract validation failed."
        if missing:
            msg += f" Missing: {missing}."
        if bad:
            msg += f" Bad: {bad}."
        raise ContractValidationError(msg)
# --- Minimal required fields per contract (v0.1) ---
REQUIRED_T2_V0_1 = [
    ("meta_schema_version", "nonempty_str"),
    ("meta_generated_at", "nonempty_str"),
    ("meta_client_id", "nonempty_str"),
    ("meta_latency_ms", "number"),
]

REQUIRED_T3_V0_1 = [
    ("meta_schema_version", "nonempty_str"),
    ("meta_generated_at", "nonempty_str"),
    ("meta_client_id", "nonempty_str"),
    ("meta_model_tag", "nonempty_str"),
    ("meta_model_file", "nonempty_str"),
    ("meta_threshold_mode", "nonempty_str"),
    ("meta_latency_ms", "number"),
    ("score_fraud_prob", "number"),
    ("thr_fraud", "number"),
    ("decision_fraud", "nonempty_str"),
    ("decision_fraud_norm", "nonempty_str"),
]

REQUIRED_T4_V0_1 = [
    ("meta_schema_version", "nonempty_str"),
    ("meta_generated_at", "nonempty_str"),
    ("meta_client_id", "nonempty_str"),
    ("meta_latency_ms", "number"),
]
