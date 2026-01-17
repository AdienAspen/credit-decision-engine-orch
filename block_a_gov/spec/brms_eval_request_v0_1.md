# brms_eval_request_v0_1 — Input Contract (ORIGINATE -> Block B)

## Purpose
Minimal, BRMS-native request payload for evaluating business rules / DMN gates.
**Block B remains agnostic of Block A (ML decisions + sensors).**

## Contract rules (v0.1)
- Strict schema: do not rename fields.
- Additive-only changes require v0.2+.
- Fields mirror DMN inputData: `Applicant`, `Loan`, `Context`.

## Payload

### Meta (required)
- `meta_schema_version` (str) — must be `"brms_eval_request_v0_1"`
- `meta_generated_at` (str, ISO-8601 UTC)
- `meta_request_id` (str)
- `meta_client_id` (str)

### Applicant (required) — DMN inputData `Applicant` (tApplicant)
- `Applicant.age` (number|int)
- `Applicant.fico_credit_score` (number|int)
- `Applicant.dti` (number)
- `Applicant.employment_status` (string)

### Loan (required) — DMN inputData `Loan` (tLoan)
- `Loan.loan_amount` (number)
- `Loan.loan_term_months` (number|int)

### Context (required) — DMN inputData `Context` (tContext)
- `Context.policy_id` (string)
- `Context.policy_version` (string)
- `Context.validation_mode` (string) — e.g. `STRICT|RELAXED|TEST`

## Notes
- No ML scores, thresholds, or decisions are provided to BRMS in v0.1.
- No dynamic sensors are provided to BRMS in v0.1.
