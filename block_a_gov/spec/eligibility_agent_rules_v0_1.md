# eligibility_agent_rules_v0_1

## Purpose
Decision rules, precedence, and early-cut mapping for `Eligibility Agent v0.1`.

## Parameters (minimum)
- `MIN_AGE` (example: `18`)
- `MIN_INCOME` (example: `1200`)
- `MACRO_STRESS_REVIEW_THR` (example: `0.85`)

## Inputs
From `application_intake_v0_1`:
- `applicant.is_existing_customer` or valid `applicant.customer_id`
- `applicant.age`
- `applicant.income_monthly`
- `applicant.employment_status`
- `loan.loan_amount`
- `loan.loan_term_months`
- `dynamic_sensors_for_eligibility.dyn_bureau_employment_verified`
- `dynamic_sensors_for_eligibility.dyn_bureau_tenure_months` (optional)
- `dynamic_sensors_for_eligibility.dyn_market_stress_score_7d`

## Rule precedence (v0.1)
1. Not existing customer / KYC fail -> `REJECTED` + `EA_KYC_NOT_EXISTING_CUSTOMER`
2. Age < `MIN_AGE` -> `REJECTED` + `EA_AGE_UNDER_MIN`
3. Income < `MIN_INCOME` -> `REJECTED` + `EA_INCOME_BELOW_MIN`
4. Bureau employment not verified -> `REVIEW_REQUIRED` + `EA_BUREAU_EMPLOYMENT_UNVERIFIED`
5. Macro stress > `MACRO_STRESS_REVIEW_THR` -> `REVIEW_REQUIRED` + `EA_MACRO_STRESS_REVIEW`

Default:
- If no rule is triggered -> `APPROVED`.

Notes:
- `wF` macro is soft-only in v0.1: it can trigger `REVIEW_REQUIRED`, never hard block.
- `credit_score` is intentionally out of `Eligibility Agent v0.1` to avoid duplication with BRMS Gate_1.

## Early-cut mapping to final_decision_v0_1

### Case A (`eligibility_status = REJECTED`)
- `final_outcome` = `REJECT`
- `final_reason_code` derived from first `eligibility_reasons` item
- `warnings` may include all `eligibility_reasons`
- `source` semantic = `eligibility_agent`
- Skip T2/T3/T4 and BRMS.

### Case B (`eligibility_status = REVIEW_REQUIRED`)
- `final_outcome` = `REVIEW`
- `final_reason_code` derived from first `eligibility_reasons` item
- `warnings` may include all `eligibility_reasons`
- `source` semantic = `eligibility_agent`
- MVP path: skip T2/T3/T4 and BRMS.

### Case C (`eligibility_status = APPROVED`)
- Continue normal flow: ORIGINATE -> T2/T3/T4 -> BRMS -> `final_decision_v0_1`.

## Versioning policy
- Additive changes only.
- Rule order is normative in v0.1.
