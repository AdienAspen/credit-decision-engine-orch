10 Edge cases (expected behavior)

Eligibility blocks

Eligibility: false

A/B/sensors: any

⇒ REJECT (ELIGIBILITY_BLOCK)

Fraud hard reject

Eligibility: true

T3: HIGH_FRAUD

⇒ REJECT (FRAUD_HARD_BLOCK) regardless of T2/T4/B.

Fraud low but fraud sensors scream

T3: LOW_FRAUD

Sensors: device anomaly high + behavior bot score high

⇒ REVIEW (FRAUD_REVIEW), required_docs += ["ID_VERIFICATION"] (example)

Default high risk

T2: HIGH_RISK

T3: LOW_FRAUD

⇒ REJECT (DEFAULT_HIGH_RISK)

Default moderate + clean fraud + BRMS clean

T2: MED_RISK

T3: LOW_FRAUD

B gates: PASS

⇒ REVIEW (safe default) or APPROVE if policy says med-risk acceptable. (Define per policy_id)

Payoff high only

T4: HIGH_PAYOFF_RISK (or whatever label)

T2: low, T3: low, B: pass

⇒ REVIEW or APPROVE_WITH_WARNINGS (if you later add), for v0.1 use REVIEW + warning.

A rejects, B approves (your “most important discrepancy”)

A: REJECT (any of T2/T3/T4 in hard mode)

B gates: PASS/Approved

⇒ REVIEW (DISCREPANCY_A_VS_B) + dominant_signals include which agent vetoed.

A approves, BRMS hard-blocks

A: all low

B: gate_1 BLOCK with compliance reason (e.g., invalid employment_status)

⇒ REJECT (BRMS_HARD_BLOCK)

BRMS unreachable

A: low

BRMS: missing/error

⇒ REVIEW (BRMS_UNAVAILABLE_FAIL_OPEN) unless policy allows approve-with-warning (v0.2+).

Multiple weak warnings

A: all low

Sensors: mild anomalies (not enough for fraud)

BRMS: soft warnings present

⇒ REVIEW (COMBINED_WEAK_SIGNALS) with short dominant_signals list.


