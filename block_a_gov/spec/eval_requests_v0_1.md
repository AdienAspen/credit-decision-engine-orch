# eval_requests_v0_1

## Purpose
Define the external input dataset contract for batch E2E testing (`dev/eval/edge`) in Block A.

This contract must contain only primary external fields. Runtime outputs (DS/BRMS/ML/final decision) are derived during execution and must not be precomputed in the input dataset.

## Dataset format
- Recommended: `parquet` (preferred), `jsonl` accepted for debugging.
- One row = one request to replay end-to-end.

## Required fields
- `request_id` (string, non-empty)
- `client_id` (string or int, non-empty)
- `as_of_ts` (ISO-8601 timestamp)
- `seed` (int)
- `product_type` (string)
- `requested_amount` (float)
- `term_months` (int)
- `age` (int)
- `employment_status` (`EMPLOYED | SELF_EMPLOYED | OTHER`)
- `declared_income_monthly` (float)
- `is_existing_customer` (bool)

## Optional fields
- `scenario_tag` (string)
- `channel` (string)
- `declared_dti` (float)
- `declared_credit_score` (int or float)
- `country_code` (string)
- `currency` (string)
- `requested_at_hour` (int, 0-23)

## Derived at runtime (must NOT be in eval_requests_v0_1)
- Dynamic sensor outputs (`wE/wF/wB/wC`)
- `brms_flags_v0_1`
- `risk_decision_t2_v0_1`
- `risk_decision_t3_v0_1`
- `risk_decision_t4_v0_1`
- `final_decision_v0_1`
- `reporter_output_v0_1`
- Runtime traces (`latency/source/status maps`, `reason_codes`)

## Usage by stage
### Workflow / Intake
Uses required external fields to build `application_intake_v0_1`.

### Eligibility Agent
Consumes intake and resolves `wE/wF` signals in `STUB|LIVE` with fallback.

### ORIGINATE
Runs only when eligibility is `APPROVED`; resolves or consumes `wB/wC`, runs T2/T3/T4 and BRMS, emits `decision_pack_v0_1`.

### Reporter
Consumes decision pack and emits `reporter_output_v0_1`.

## Batch sets (v0.1)
- `eval_requests_dev_v0_1` (~50 rows)
- `eval_requests_eval_v0_1` (~1000 rows)
- `eval_requests_edge_v0_1` (~100-200 rows)

## Evidence reference
This contract was frozen from reconnaissance evidence:
- `testing/reports/recon_input_inventory_20260302_145954.md`
- `testing/runs/e2e_full_chain_pack_20260218_165122.json`
- `testing/runs/e2e_full_chain_report_20260218_165122.json`
