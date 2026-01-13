# risk_decision_t2_v0_1 — Output Contract (T2 DEFAULT)

## Purpose
Canonical output payload for the **T2 Default Risk** sub-agent runner.
Used by ORIGINATE to assemble `decision_pack_v0_1`.

## Contract rules (v0.1)
- **Strict schema**: do not rename existing fields.
- **Additive-only**: new fields require v0.2+ or must be clearly additive.
- `meta_*` fields are for traceability; `score_*` and `thr_*` are model outputs; `decision_*` is the business-facing decision.

## Required fields
### Meta
- `meta_schema_version` (str) — must be `"risk_decision_t2_v0_1"`
- `meta_generated_at` (str, ISO-8601 UTC)
- `meta_request_id` (str|null)
- `meta_client_id` (str)
- `meta_model_tag` (str)
- `meta_model_file` (str)
- `meta_operating_point` (str) — operating point id/name used (e.g., op_a/op_b variants)
- `meta_latency_ms` (int)

### Scores / thresholds / decision
- `score_default_prob` (float) — probability of default (positive class)
- `thr_default` (float) — threshold applied under selected operating point
- `decision_default` (str) — `"HIGH_RISK"` if `score_default_prob >= thr_default` else `"LOW_RISK"`

## Example
```json
{
  "meta_schema_version": "risk_decision_t2_v0_1",
  "meta_generated_at": "2026-01-13T00:00:00Z",
  "meta_request_id": "uuid",
  "meta_client_id": "100001",
  "meta_model_tag": "t2_default_xgb_v3a_microA",
  "meta_model_file": "/path/to/model.json",
  "meta_operating_point": "op_a_best_f1_under_flag",
  "meta_latency_ms": 123,
  "score_default_prob": 0.17,
  "thr_default": 0.65,
  "decision_default": "LOW_RISK"
}

