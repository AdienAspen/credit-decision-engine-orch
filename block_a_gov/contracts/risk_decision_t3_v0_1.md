# risk_decision_t3_v0_1 — Contract (MVP)

## Purpose
Fraud risk decision payload emitted by `runners/runner_t3.py`. This is a deterministic, auditable output consumed by ORIGINATE (DecisionPack) and later by PolicyDecider.

## Schema versioning
- `meta_schema_version` MUST be `"risk_decision_t3_v0_1"`.
- Backward compatibility rule: changes MUST be additive only (no renames / no type changes). New fields require a new version only if semantics change.

## Fields

### Meta
- `meta_schema_version` (string) — `"risk_decision_t3_v0_1"`
- `meta_generated_at` (string, ISO8601 UTC)
- `meta_request_id` (string)
- `meta_client_id` (string)
- `meta_model_tag` (string)
- `meta_model_file` (string)
- `meta_threshold_mode` (string)
- `meta_latency_ms` (int)

### Signals
- `score_fraud_prob` (float, 0..1) — model probability output.
- `thr_fraud` (float, 0..1) — operating threshold for fraud.
- `decision_fraud` (string enum) — base decision derived from thresholding.
  - Allowed: `LOW_FRAUD` | `HIGH_FRAUD` (MVP; may expand later)
- `decision_fraud_norm` (string enum) — normalized band for PolicyDecider.
  - Allowed: `LOW_FRAUD` | `REVIEW_FRAUD` | `HIGH_FRAUD`

## Normalization rule (MVP)
Given `score_fraud_prob = p` and `thr_fraud = t`:
- If `p >= t` → `decision_fraud_norm = HIGH_FRAUD`
- Else if `p >= 0.5 * t` → `decision_fraud_norm = REVIEW_FRAUD`
- Else → `decision_fraud_norm = LOW_FRAUD`

## Example (minimal)
```json
{
  "meta_schema_version": "risk_decision_t3_v0_1",
  "meta_generated_at": "2026-01-22T00:00:00Z",
  "meta_request_id": "sample",
  "meta_client_id": "100001",
  "meta_model_tag": "fraud_t3_ieee_xgb_bcd_best",
  "meta_model_file": "models/fraud_t3_ieee_xgb.json",
  "meta_threshold_mode": "recommended",
  "meta_latency_ms": 25,
  "score_fraud_prob": 0.12,
  "thr_fraud": 0.20,
  "decision_fraud": "LOW_FRAUD",
  "decision_fraud_norm": "REVIEW_FRAUD"
}
