# originate_dynamic_fraud_signals_v0_1

## Purpose
Define how ORIGINATE consumes and evaluates dynamic fraud/operational signals (`wC`, `wB`) in MVP mode without retraining T3.

## Inputs
- `dyn_device_behavior_fraud_score_24h` (from `wC`)
- `dyn_transaction_anomaly_score_30d` (from `wB`)

## Output object (inside decision_pack.decisions.fraud_signals)
- `meta_schema_version` = `originate_dynamic_fraud_signals_v0_1`
- `meta_generated_at`
- `meta_request_id`
- `meta_client_id`
- `dyn_device_behavior_fraud_score_24h`
- `dyn_transaction_anomaly_score_30d`
- `flag_device_suspicious` (bool)
- `flag_transaction_anomalous` (bool)
- `flag_fraud_signal_high` (bool)
- `action_recommended` in `{ALLOW, REVIEW, STEP_UP, BLOCK}`
- `reason_codes` (stable list)
- `meta_sensor_mode_used` in `{STUB, LIVE, LIVE_FALLBACK}`
- `sensor_trace`:
  - `device_behavior`: `source`, `mode`, `latency_ms`, `status`, `lookback_hours`, `as_of_ts`
  - `transaction_anomaly`: `source`, `mode`, `latency_ms`, `status`, `lookback_days`, `as_of_ts`

## Rule set (MVP)
- One high signal (device OR transaction) -> `STEP_UP` (or `REVIEW` if policy decides)
- Two high signals (device AND transaction) -> `REVIEW` by default (`BLOCK` optional policy)
- `BLOCK` is accepted only with corroboration in PolicyDecider:
  - `T3 HIGH_FRAUD` OR
  - BRMS hard fail

## Corroboration guardrail
A standalone dynamic signal must not hard-block in MVP.

## LIVE/STUB behavior
- STUB mode: use fixture values.
- LIVE mode: query DS_Z endpoints:
  - `/sensor/device_behavior_score`
  - `/sensor/transaction_anomaly_score`
- If any live call fails, fallback per-sensor to STUB and set `meta_sensor_mode_used=LIVE_FALLBACK`.

## Stable reason codes (v0.1)
- `FS_DEVICE_BEHAVIOR_HIGH`
- `FS_TRANSACTION_ANOMALY_HIGH`
- `FS_DUAL_SIGNAL_HIGH`

## Versioning policy
- Additive changes only.
- Existing semantics remain stable in v0.1.
