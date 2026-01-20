# BRMS Flags Contract — v0.1 (brms_flags_v0_1)

## Purpose
Provide a stable, auditable decision payload from the BRMS Bridge to ORIGINATE.
This contract is consumed by ORIGINATE and may be referenced by sub-agent runners (T2/T3/T4) without coupling to bridge internals.

## Location in ORIGINATE response
`decisions.brms_flags`

## Schema versioning
- `meta_schema_version` MUST be: `brms_flags_v0_1`
- Future changes must be additive (v0.2+). No renames/removals in v0.1.

## Fields

### Meta (traceability + governance)
All meta fields are REQUIRED unless explicitly stated otherwise.

- `meta_schema_version` (string)
  - Example: `brms_flags_v0_1`
- `meta_generated_at` (string, ISO-8601)
- `meta_request_id` (string)
- `meta_client_id` (string or int serialized as string)
- `meta_policy_id` (string)
  - Example: `P1`
- `meta_policy_version` (string)
  - Example: `1.0`
- `meta_validation_mode` (string)
  - Suggested values: `STRICT` | `LENIENT` | `OFF`
- `meta_latency_ms` (int)
  - Bridge end-to-end evaluation latency (best effort)

### Gates (primary outcomes)
Gates are REQUIRED.

- `gate_1` (string)
- `gate_2` (string)
- `gate_3` (string)

Allowed values (recommended):
- `PASS` | `FAIL` | `WARN` | `NA`

Semantics:
- `PASS`: gate satisfied
- `FAIL`: gate blocks progression (unless override applied)
- `WARN`: non-blocking but should be surfaced
- `NA`: not evaluated / not applicable

### Overrides (exceptions / forced decisions)
- `overrides` (list) — REQUIRED
  - Default: `[]`
  - Each item should be an object (dict) when used, with at minimum:
    - `override_id` (string)
    - `reason` (string)
    - `applied_by` (string)
    - `applied_at` (string, ISO-8601)

### Required documents (compliance / KYC)
- `required_docs` (list) — REQUIRED
  - Default: `[]`
  - Each item should be a string doc code OR an object with:
    - `doc_code` (string)
    - `doc_label` (string, optional)

### Warnings (non-blocking alerts)
- `warnings` (list) — REQUIRED
  - Default: `[]`
  - Each item should be a string warning code OR an object with:
    - `warning_code` (string)
    - `message` (string, optional)

## Known-good example (observed)
- `meta_policy_id`: `P1`
- `meta_policy_version`: `1.0`
- `meta_schema_version`: `brms_flags_v0_1`
- `meta_latency_ms`: `22`
- `gate_1/2/3`: `PASS`
- `overrides/required_docs/warnings`: `[]`

## Non-goals
- This contract does not define the internal DMN/DRL rules.
- This contract does not define ML model scoring outputs.

