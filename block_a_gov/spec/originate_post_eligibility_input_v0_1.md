# originate_post_eligibility_input_v0_1

## Purpose
Define the minimum input contract that must be present before `ORIGINATE` runs in the post-eligibility lane.

## Scope
This contract applies only when `Eligibility Agent` returns `eligibility_status = APPROVED`.
If status is `REJECTED` or `REVIEW_REQUIRED`, ORIGINATE must not run (early-cut path).

## Preconditions
- `workflow_intake.meta_schema_version = application_intake_v0_1`
- `eligibility.meta_schema_version = eligibility_agent_status_v0_1`
- `eligibility.eligibility_status = APPROVED`
- `eligibility.eligibility_reasons` is present (can be empty)

## Required fields for ORIGINATE post-eligibility entry

### request_context
- `meta_request_id` (string, non-empty)
- `meta_client_id` (string, non-empty)

### workflow_intake (attached)
- `meta_schema_version = application_intake_v0_1`
- `meta_request_id` (must match `request_context.meta_request_id`)
- `meta_client_id` (must match `request_context.meta_client_id`)
- `applicant` (dict)
- `loan` (dict)

### eligibility (attached)
- `meta_schema_version = eligibility_agent_status_v0_1`
- `meta_request_id` (must match `request_context.meta_request_id`)
- `meta_client_id` (must match `request_context.meta_client_id`)
- `eligibility_status = APPROVED`
- `eligibility_reasons` (array)

## Runtime invariants
- `meta_request_id` must be equal across `request_context`, `workflow_intake`, and `eligibility`.
- `meta_client_id` must be equal across `request_context`, `workflow_intake`, and `eligibility`.
- ORIGINATE owns post-gate orchestration only: T2/T3/T4 + BRMS + `final_decision_v0_1`.

## Dynamic fraud signals for ORIGINATE (current phase)
In `v0.1` current implementation, ORIGINATE resolves `wB` and `wC` directly (LIVE/STUB):
- `dyn_transaction_anomaly_score_30d` (`wB`)
- `dyn_device_behavior_fraud_score_24h` (`wC`)

These signals are treated as routing signals (not model retrain features in MVP):
- produce flags + reason codes + `action_recommended`
- default behavior:
  - one high signal -> `STEP_UP`/`REVIEW`
  - two high signals -> strong `REVIEW`
  - `BLOCK` only with corroboration (`T3 HIGH_FRAUD` or BRMS hard fail)

Forward-compatibility note:
- future lanes may pass `wB/wC` pre-resolved into ORIGINATE.
- ORIGINATE should remain compatible with both modes:
  - consume pre-attached signals when present
  - otherwise resolve via current LIVE/STUB fetch path

## Minimal payload example (entry view)
```json
{
  "request_context": {
    "meta_request_id": "req-123",
    "meta_client_id": "100001"
  },
  "workflow_intake": {
    "meta_schema_version": "application_intake_v0_1",
    "meta_request_id": "req-123",
    "meta_client_id": "100001",
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
    }
  },
  "eligibility": {
    "meta_schema_version": "eligibility_agent_status_v0_1",
    "meta_request_id": "req-123",
    "meta_client_id": "100001",
    "eligibility_status": "APPROVED",
    "eligibility_reasons": []
  }
}
```

## Non-goals
- This contract does not redefine BRMS payloads.
- This contract does not include DS wiring internals for Eligibility LIVE mode.

## Versioning policy
- Additive changes only.
- Existing keys and semantics in v0.1 must remain stable.
