#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI

from runners.runtime_support import stable_score, utc_now_iso
from tools.mock_brms_logic import evaluate_mock_brms_flags

app = FastAPI()


def _score(*parts: Any, floor: float = 0.05, ceil: float = 0.95) -> float:
    return stable_score(*parts, floor=floor, ceil=ceil)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "mode": "mock"}


@app.get("/sensor/device_behavior_score")
def device_behavior_score(client_id: str, lookback_hours: int = 24, request_id: str = "mock", seed: int = 42) -> Dict[str, Any]:
    return {
        "device_behavior_fraud_score_24h": _score("device", client_id, request_id, seed),
        "lookback_hours": lookback_hours,
        "generated_at": utc_now_iso(),
        "latency_ms": 5,
        "source": "mock_sensor_server",
    }


@app.get("/sensor/transaction_anomaly_score")
def transaction_anomaly_score(client_id: str, lookback_days: int = 30, request_id: str = "mock", seed: int = 42) -> Dict[str, Any]:
    return {
        "transaction_anomaly_score_30d": _score("transaction", client_id, request_id, seed),
        "lookback_days": lookback_days,
        "generated_at": utc_now_iso(),
        "latency_ms": 5,
        "source": "mock_sensor_server",
    }


@app.get("/sensor/bureau_spike_score")
def bureau_spike_score(client_id: str, lookback_hours: int = 24, request_id: str = "mock") -> Dict[str, Any]:
    return {
        "bureau_spike_score_24h": _score("bureau", client_id, request_id, floor=0.0, ceil=1.0),
        "lookback_hours": lookback_hours,
        "generated_at": utc_now_iso(),
        "latency_ms": 5,
        "source": "mock_sensor_server",
    }


@app.get("/sensor/market_snapshot")
def market_snapshot(request_id: str = "mock", as_of: str | None = None) -> Dict[str, Any]:
    return {
        "market_stress_score_7d": _score("market", request_id, as_of or "none", floor=0.0, ceil=1.0),
        "generated_at": as_of or utc_now_iso(),
        "latency_ms": 5,
        "source": "mock_sensor_server",
    }


@app.post("/bridge/brms_flags")
def bridge_brms_flags(req_payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate_mock_brms_flags(req_payload)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

