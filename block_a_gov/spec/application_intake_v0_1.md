# application_intake_v0_1

## Purpose
Structured intake payload produced by `WORK-FLOW` and consumed by `Eligibility Agent`.

## Naming boundary
Use `eligibility_agent_*` for agent-level artifacts. Do not mix with `brms_gate_*` naming.

## Contract (required fields)

### applicant
- `customer_id` (string, non-empty) OR `is_existing_customer` (boolean) present
- `age` (integer)
- `income_monthly` (number)
- `employment_status` (enum): `EMPLOYED | SELF_EMPLOYED | OTHER`

### loan
- `loan_amount` (number)
- `loan_term_months` (integer)

### dynamic_sensors_for_eligibility
- `dyn_bureau_employment_verified` (boolean)
- `dyn_bureau_tenure_months` (integer, optional)
- `dyn_market_stress_score_7d` (number 0..1)

### meta
- `meta_schema_version` = `application_intake_v0_1`
- `meta_generated_at` (ISO-8601 string)
- `meta_request_id` (string, non-empty)
- `meta_client_id` (string, non-empty)
- `meta_application_id` (string, non-empty)
- `meta_channel` (string, non-empty)
- `meta_as_of_ts` (ISO-8601 string)
- `meta_latency_ms` (number)

## Example (STUB)
```json
{
  "meta_schema_version": "application_intake_v0_1",
  "meta_generated_at": "2026-02-12T00:00:00Z",
  "meta_request_id": "req-123",
  "meta_client_id": "100001",
  "meta_application_id": "app-123",
  "meta_channel": "web",
  "meta_as_of_ts": "2026-02-12T00:00:00Z",
  "meta_latency_ms": 5,
  "applicant": {
    "customer_id": "cust-100001",
    "is_existing_customer": true,
    "age": 30,
    "income_monthly": 2500,
    "employment_status": "EMPLOYED"
  },
  "loan": {
    "loan_amount": 10000,
    "loan_term_months": 36
  },
  "dynamic_sensors_for_eligibility": {
    "dyn_bureau_employment_verified": true,
    "dyn_bureau_tenure_months": 24,
    "dyn_market_stress_score_7d": 0.35
  }
}
```

## Versioning policy
- Additive changes only.
- Do not rename or delete existing keys/enums in `v0.1`.
