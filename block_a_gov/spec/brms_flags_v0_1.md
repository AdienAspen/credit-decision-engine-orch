# brms_flags_v0_1 — Output Contract (Block B -> ORIGINATE)

## Purpose
Business-rule signals from BRMS (DMN/Rules) to ORIGINATE.
**Agnostic of Block A (ML decisions + sensors).**

## Contract rules (v0.1)
- Strict schema: do not rename fields.
- Additive-only changes require v0.2+.

## Payload

### Meta (required)
- `meta_schema_version` (str) — must be `"brms_flags_v0_1"`
- `meta_generated_at` (str, ISO-8601 UTC)
- `meta_request_id` (str)
- `meta_client_id` (str)
- `meta_policy_id` (str) — from input `Context.policy_id`
- `meta_policy_version` (str) — from input `Context.policy_version`
- `meta_validation_mode` (str) — from input `Context.validation_mode`

### Gates (required)
- `gate_1` (string) — `PASS|WARN|BLOCK`
- `gate_2` (string) — `PASS|WARN|BLOCK`
- `gate_3` (string) — `PASS|WARN|BLOCK`

### Signals (optional)
- `warnings` (list[string])
- `overrides` (list[string])
- `required_docs` (list[string])

## Notes
- BRMS may return additional `signals.*` fields in v0.2+ (additive).
- BRMS must always echo `meta_request_id` for traceability.
