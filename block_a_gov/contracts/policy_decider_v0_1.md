
policy_decider_v0_1 — Spec (MVP)
Role

Deterministic policy engine inside ORIGINATE.

Pure function: no HTTP, no file I/O, no LLM, no narrative generation.

Input → Output only (easy to unit test with fixtures).

Produces final_decision_v0_1.

Inputs (conceptual)

eligibility_signal_v0_1 (Gate 0)

decision_pack_v0_1 (must include T2/T3/T4)

brms_flags_v0_1 (optional; may be missing/fail-open)

sensor_pack_v0_1 (optional; may be missing)

Core invariants

Block A can veto approval

If A yields a hard reject/veto (T2 or T3 in hard mode), the final outcome cannot be APPROVE.

Discrepancy handling (A vs B)

If A=REJECT and B=PASS/APPROVE ⇒ MVP behavior: REVIEW with reason DISCREPANCY_A_VS_B (policy may choose stricter in future versions).

Fail-open for BRMS

If BRMS missing/unreachable ⇒ continue using A (+ sensors), but add warning BRMS_UNAVAILABLE_FAIL_OPEN.

If A is borderline ⇒ prefer REVIEW over APPROVE.

Priority rules (pyramid)

Eligibility hard stop

If eligibility=false ⇒ REJECT (ELIGIBILITY_BLOCK)

Fraud dominates (T3)

If decision_fraud_norm=HIGH_FRAUD ⇒ REJECT (FRAUD_HARD_BLOCK)

If decision_fraud_norm=REVIEW_FRAUD ⇒ REVIEW (FRAUD_REVIEW)

Default risk (T2)

If T2 indicates hard high risk ⇒ REJECT (DEFAULT_HIGH_RISK)

If moderate risk ⇒ typically REVIEW (policy-dependent)

Payoff (T4) advisory

Rarely blocks; may push to REVIEW or add warnings/docs.

BRMS gates HARD vs SOFT

HARD_BLOCK (compliance/invalid inputs) may force REJECT (BRMS_HARD_BLOCK)

SOFT flags cannot override A veto; can push to REVIEW, add docs/warnings.

Missing signals

If critical inputs missing ⇒ REVIEW (MISSING_SIGNALS) and add warnings.

Output

Must conform to final_decision_v0_1 contract:

final_outcome, final_reason_code

dominant_signals, required_docs, warnings, overrides_applied

audit minimal summaries

10 MVP edge cases (expected behavior)

Eligibility blocks ⇒ REJECT (ELIGIBILITY_BLOCK)

Fraud hard reject (HIGH_FRAUD) ⇒ REJECT (FRAUD_HARD_BLOCK)

Fraud review band (REVIEW_FRAUD) ⇒ REVIEW (FRAUD_REVIEW)

Default high risk ⇒ REJECT (DEFAULT_HIGH_RISK)

Default moderate + clean fraud + BRMS clean ⇒ REVIEW (policy-dependent)

Payoff high only ⇒ REVIEW + warning (advisory)

A rejects, B passes ⇒ REVIEW (DISCREPANCY_A_VS_B)

A clean, BRMS hard-block ⇒ REJECT (BRMS_HARD_BLOCK)

BRMS unreachable, A clean ⇒ REVIEW + warning (BRMS_UNAVAILABLE_FAIL_OPEN)

Multiple weak warnings ⇒ REVIEW (COMBINED_WEAK_SIGNALS)
