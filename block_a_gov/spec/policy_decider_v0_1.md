PolicyDecider v0.1 (spec)

Role: deterministic policy engine. No HTTP, no file I/O, no LLM, no narrative.
Input → Output (pure function).

Inputs

eligibility_signal_v0_1 (Gate 0)

decision_pack_v0_1 (must include: T2/T3/T4)

brms_flags_v0_1 (optional; may be missing/fail-open)

sensor_pack_v0_1 (optional; may be missing)

Core priority rules (your “pyramid”)

0) Eligibility hard stop

If eligibility = false ⇒ final_outcome = REJECT (final_reason_code = ELIGIBILITY_BLOCK)

1) Fraud dominates (T3)

If t3_fraud indicates HIGH_FRAUD / HARD_BLOCK ⇒ final_outcome = REJECT (FRAUD_HARD_BLOCK)

If t3_fraud is ambiguous but sensors raise fraud suspicion ⇒ final_outcome = REVIEW (FRAUD_REVIEW)

2) Default risk (T2)

If t2_default indicates HIGH_RISK / HARD_BLOCK ⇒ final_outcome = REJECT (DEFAULT_HIGH_RISK)

If moderate risk ⇒ typically REVIEW unless everything else is clean and policy allows approve.

3) Payoff (T4) is advisory (lowest veto power)

Payoff rarely blocks; it can push:

to REVIEW (e.g., “high early payoff risk” conflicts with product economics)

or add warnings / required_docs

4) BRMS gates: split into HARD vs SOFT

Treat BRMS outputs as:

HARD_BLOCK signals (compliance/invalid inputs) ⇒ can force REJECT even if A says approve.

SOFT_FLAGS ⇒ cannot override A veto; they can push REVIEW, add docs, warnings.

Mapping example:

If gate_1/2/3 == "BLOCK" and code is compliance-like ⇒ BRMS_HARD_BLOCK

Else discrepancy handling (below)

5) Discrepancy policy (A vs B)

If A = REJECT and B = PASS/APPROVE ⇒ final_outcome = REVIEW + final_reason_code = DISCREPANCY_A_VS_B
(or REJECT directly if you want strict “A veto always final”—tu decides, pero REVIEW suele ser más realista)

6) Missing signals / fail-open

If BRMS is missing/unreachable ⇒ continue with A + sensors, but add warning:

warnings += ["BRMS_UNAVAILABLE_FAIL_OPEN"]

If A is borderline ⇒ prefer REVIEW (not approve).

Sensor influence (lightweight, supports fraud priority)

Fraud-related sensors (behavior/device/bureau anomalies) can:

escalate LOW_FRAUD → REVIEW

strengthen HIGH_FRAUD → REJECT reason confidence

Market sensor generally affects pricing/risk appetite, not fraud veto.


