# eligibility_agent_status_v0_1

## Purpose
Output contract for `Eligibility Agent` as gatekeeper before ORIGINATE.

## Naming boundary
This contract is agent-level and must use `eligibility_agent_*` semantics.
It is independent from `BRMS Gate_1 Eligibility`.

## Contract (required fields)
- `meta_schema_version` = `eligibility_agent_status_v0_1`
- `meta_generated_at` (ISO-8601 string)
- `meta_request_id` (string, non-empty)
- `meta_client_id` (string, non-empty)
- `meta_latency_ms` (number)
- `eligibility_status` (enum): `APPROVED | REJECTED | REVIEW_REQUIRED`
- `eligibility_reasons` (array of stable reason codes, additive-only)

## Stable reason codes v0.1
- `EA_KYC_NOT_EXISTING_CUSTOMER`
- `EA_AGE_UNDER_MIN`
- `EA_INCOME_BELOW_MIN`
- `EA_BUREAU_EMPLOYMENT_UNVERIFIED`
- `EA_MACRO_STRESS_REVIEW`
- `EA_EMPLOYMENT_STATUS_REVIEW` (optional, if policy enabled)

## Example
```json
{
  "meta_schema_version": "eligibility_agent_status_v0_1",
  "meta_generated_at": "2026-02-12T00:00:00Z",
  "meta_request_id": "req-123",
  "meta_client_id": "100001",
  "meta_latency_ms": 8,
  "eligibility_status": "REVIEW_REQUIRED",
  "eligibility_reasons": [
    "EA_BUREAU_EMPLOYMENT_UNVERIFIED"
  ]
}
```

## Versioning policy
- Additive changes only.
- Existing reason codes are stable; new codes can be appended only.
