# final_decision_v0_1 — Contract (MVP)

## Purpose
Single, auditable final outcome computed deterministically by ORIGINATE from:
- Eligibility signal (Gate 0)
- DecisionPack (Block A: T2/T3/T4)
- BRMS flags (Block B; optional / fail-open)
- SensorPack (optional)

This output is **policy-bound** (`policy_id`, `policy_version`) and **traceable** (`request_id`, timestamps).

## Schema versioning
- `meta_schema_version` MUST be `"final_decision_v0_1"`.
- Changes MUST be additive only (no renames / no type changes). Breaking changes require `v0_2+`.

## Fields

### Meta
- `meta_schema_version` (string) — `"final_decision_v0_1"`
- `meta_generated_at` (string, ISO8601 UTC)
- `meta_request_id` (string)
- `meta_client_id` (string)
- `meta_policy_id` (string; from BRMS context if present, else `"unknown"`)
- `meta_policy_version` (string; else `"unknown"`)
- `meta_validation_mode` (string; else `"unknown"`)

### Final outcome
- `final_outcome` (string enum): `APPROVE` | `REJECT` | `REVIEW`
- `final_reason_code` (string; enum-ish): e.g.
  - `ELIGIBILITY_BLOCK`
  - `FRAUD_HARD_BLOCK`
  - `FRAUD_REVIEW`
  - `DEFAULT_HIGH_RISK`
  - `BRMS_HARD_BLOCK`
  - `DISCREPANCY_A_VS_B`
  - `MISSING_SIGNALS`
  - `BRMS_UNAVAILABLE_FAIL_OPEN`
  - `COMBINED_WEAK_SIGNALS`

### Explanatory payload (machine-oriented)
- `dominant_signals` (list[string], max ~5)
- `required_docs` (list[string])
- `warnings` (list[string])
- `overrides_applied` (list[string])

### Audit summary (minimal)
- `audit` (object)
  - `a_summary` (object) — minimal summary of A outputs:
    - `t2_default` (string or object minimal)
    - `t3_fraud` (string or object minimal)
    - `t4_payoff` (string or object minimal)
  - `b_summary` (object, optional) — minimal BRMS gates:
    - `gate_1`, `gate_2`, `gate_3` (string)
  - `sensor_summary` (object, optional)
  - `confidence` (float, optional 0..1)
  - `latency_ms_total` (int, optional)

## Example (minimal)
```json
{
  "meta_schema_version": "final_decision_v0_1",
  "meta_generated_at": "2026-01-27T00:00:00Z",
  "meta_request_id": "sample",
  "meta_client_id": "100001",
  "meta_policy_id": "P1",
  "meta_policy_version": "1.0",
  "meta_validation_mode": "TEST",
  "final_outcome": "REVIEW",
  "final_reason_code": "DISCREPANCY_A_VS_B",
  "dominant_signals": ["T2_DEFAULT_VETO"],
  "required_docs": [],
  "warnings": ["BRMS_UNAVAILABLE_FAIL_OPEN"],
  "overrides_applied": [],
  "audit": {
    "a_summary": {
      "t2_default": "REJECT",
      "t3_fraud": "LOW_FRAUD",
      "t4_payoff": "LOW_PAYOFF_RISK"
    },
    "b_summary": {
      "gate_1": "PASS",
      "gate_2": "PASS",
      "gate_3": "PASS"
    }
  }
}
