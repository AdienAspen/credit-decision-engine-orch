# risk_decision_t3_v0_1 — Output Contract (T3 FRAUD)

## Purpose
Canonical output payload for the **T3 Fraud** sub-agent runner.
Used by ORIGINATE to assemble `decision_pack_v0_1`.

## Contract rules (v0.1)
- **Strict schema**: do not rename existing fields.
- **Additive-only**: new fields require v0.2+ or must be clearly additive.
- Threshold modes are selected on **VALID** and applied/evaluated on **TEST**.

## Required fields
### Meta
- `meta_schema_version` (str) — must be `"risk_decision_t3_v0_1"`
- `meta_generated_at` (str, ISO-8601 UTC)
- `meta_request_id` (str|null)
- `meta_client_id` (str)
- `meta_model_tag` (str)
- `meta_model_file` (str)
- `meta_threshold_mode` (str) — selected threshold mode id (e.g. `thr_valid_recall_ge_0_90`)
- `meta_latency_ms` (int)

### Scores / thresholds / decision
- `score_fraud_prob` (float) — probability of fraud (positive class)
- `thr_fraud` (float) — threshold for the selected mode
- `decision_fraud` (str) — `"HIGH_FRAUD"` if `score_fraud_prob >= thr_fraud` else `"LOW_FRAUD"`

## Example
```json
{
  "meta_schema_version": "risk_decision_t3_v0_1",
  "meta_generated_at": "2026-01-13T00:00:00Z",
  "meta_request_id": "uuid",
  "meta_client_id": "100001",
  "meta_model_tag": "fraud_t3_ieee_xgb_bcd_best",
  "meta_model_file": "/path/to/model.json",
  "meta_threshold_mode": "thr_valid_recall_ge_0_90",
  "meta_latency_ms": 210,
  "score_fraud_prob": 0.02,
  "thr_fraud": 0.07,
  "decision_fraud": "LOW_FRAUD"
}

