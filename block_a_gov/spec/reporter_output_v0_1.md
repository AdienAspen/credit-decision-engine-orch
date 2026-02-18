# reporter_output_v0_1

## Purpose
Human-facing, audit-friendly narrative artifact generated from `decision_pack_v0_1`.

## Scope
Reporter does not change decisions. It only transforms structured outputs into an executive narrative payload.

## Required input
- `decision_pack_v0_1` with `decisions.final_decision` present.

## Output contract (required fields)
- `meta_schema_version` = `reporter_output_v0_1`
- `meta_generated_at` (ISO-8601)
- `meta_request_id` (string)
- `meta_client_id` (string)
- `meta_latency_ms` (number)
- `decision_ref` (object)
  - `final_outcome`
  - `final_reason_code`
- `executive_summary` (string)
- `risk_highlights` (array of strings)
- `governance_highlights` (array of strings)
- `warnings` (array of strings)
- `trace_refs` (object)
  - `a_summary` (object or null)
  - `b_summary` (object or null)
  - `dominant_signals` (array)

## Rules
- Reporter must preserve decision semantics (`final_outcome`, `final_reason_code`).
- Reporter may summarize but must not infer a different decision outcome.
- Missing optional sections should be emitted as empty arrays/objects, not omitted.

## Example
```json
{
  "meta_schema_version": "reporter_output_v0_1",
  "meta_generated_at": "2026-02-13T00:00:00Z",
  "meta_request_id": "req-123",
  "meta_client_id": "100001",
  "meta_latency_ms": 5,
  "decision_ref": {
    "final_outcome": "REVIEW",
    "final_reason_code": "T2_HIGH_RISK"
  },
  "executive_summary": "Outcome REVIEW due to elevated default-risk signal.",
  "risk_highlights": [
    "t2_default=HIGH_RISK"
  ],
  "governance_highlights": [
    "gate_1=PASS",
    "gate_2=PASS",
    "gate_3=PASS"
  ],
  "warnings": [
    "LOW_MARGIN_RISK_T4"
  ],
  "trace_refs": {
    "a_summary": {
      "t2_default": "HIGH_RISK",
      "t3_fraud": "LOW_FRAUD",
      "t4_payoff": "LOW_PAYOFF_RISK"
    },
    "b_summary": {
      "gate_1": "PASS",
      "gate_2": "PASS",
      "gate_3": "PASS"
    },
    "dominant_signals": [
      "t2:high_risk"
    ]
  }
}
```

## Versioning policy
- Additive changes only.
- Existing field names and semantics remain stable in `v0.1`.
