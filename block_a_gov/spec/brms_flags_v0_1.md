# brms_flags_v0_1 — Output Contract (Block B -> ORIGINATE)

## Purpose
Canonical payload returned by Block B (BRMS/RHPAM) to ORIGINATE.
This payload contains **rule-based gate signals** (warnings/overrides) used by ORIGINATE to produce the final decision.

## Contract rules (v0.1)
- Strict schema: do not rename fields.
- Additive-only changes require v0.2+.
- BRMS does not receive model internals; it receives only minimal inputs and returns flags/gates.

## Required fields
### Meta
- `meta_schema_version` (str) — must be `"brms_flags_v0_1"`
- `meta_generated_at` (str, ISO-8601 UTC)
- `meta_request_id` (str)
- `meta_client_id` (str)
- `meta_latency_ms` (int)

### Gate signals
- `gate_1_eligibility` (str) — `PASS|FAIL|REVIEW`
- `gate_2_offer` (str) — `PASS|FAIL|REVIEW`
- `gate_3_final` (str) — `PASS|FAIL|REVIEW`

### Flags / warnings / overrides
- `flags` (list[str]) — machine-friendly rule flags (can be empty)
- `warnings` (list[str]) — human-friendly warnings (can be empty)
- `overrides` (dict) — optional rule overrides (can be empty)
  - example keys: `force_decision`, `max_amount`, `manual_review_required`

## Optional fields
- `reasons` (list[str]) — reason codes
- `policy_version` (str) — BRMS policy/ruleset version
