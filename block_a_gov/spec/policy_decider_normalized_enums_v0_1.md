# PolicyDecider v0.1 — Normalized enums + aggregation rules (MVP)

Status: Draft (stable for PoC)  
Owner: ORIGINATE / Block A  
Goal: Deterministic, explainable final decision from inputs (Eligibility + A sub-decisions + BRMS flags + Sensors).

---

## 1) Normalized enums (3-state per sub-agent)

Each sub-agent output is normalized into a 3-state enum to make aggregation deterministic:

- **T3 Fraud**: `LOW_FRAUD | REVIEW_FRAUD | HIGH_FRAUD`
- **T2 Default**: `LOW_RISK | REVIEW_RISK | HIGH_RISK`
- **T4 Payoff**: `LOW_PAYOFF | REVIEW_PAYOFF | HIGH_PAYOFF`

These enums are computed inside ORIGINATE (or a dedicated `policy_decider.py`) using the raw runner outputs + BRMS/sensor signals.

---

## 2) Base rule for HIGH vs LOW (one line each)

Let:
- `p_fraud = score_fraud_prob`, `thr_fraud = thr_fraud`
- `p_def   = score_default_prob`, `thr_def  = thr_default`
- `p_pay   = score_payoff_prob`, `thr_pay  = thr_payoff`

Then:

- **T3**: `HIGH_FRAUD` iff `p_fraud >= thr_fraud`, else `LOW_FRAUD`
- **T2**: `HIGH_RISK`  iff `p_def   >= thr_def`,  else `LOW_RISK`
- **T4**: `HIGH_PAYOFF` iff `p_pay  >= thr_pay`,  else `LOW_PAYOFF`

---

## 3) Exact rule for REVIEW_* (zone gray) (one line each)

Let `gap(x, thr) = abs(x - thr)`. Use `EPS = 0.05` (MVP default).

Also define:
- `has_brms_warning(prefix)` = any warning code/message contains that prefix token (case-insensitive)
- `has_sensor_suspect(tag)` = any sensor signal indicates suspicion for that tag

Then:

- **T3 (Fraud)**:  
  `REVIEW_FRAUD` iff (current != `HIGH_FRAUD`) AND (`has_brms_warning("FRAUD")` OR `has_sensor_suspect("behavior")` OR `has_sensor_suspect("device")`)

- **T2 (Default)**:  
  `REVIEW_RISK` iff (current != `HIGH_RISK`) AND (`gap(p_def, thr_def) <= EPS` OR `has_brms_warning("DTI")` OR `has_brms_warning("CAPACITY")` OR `has_brms_warning("POLICY")`)

- **T4 (Payoff)**:  
  `REVIEW_PAYOFF` iff (current != `HIGH_PAYOFF`) AND (`gap(p_pay, thr_pay) <= EPS` OR `has_brms_warning("OFFER")` OR `has_brms_warning("TERM")`)

Notes:
- REVIEW never overrides HIGH. It only upgrades LOW -> REVIEW.
- EPS is intentionally coarse for MVP; tune later.

---

## 4) Aggregation policy (A has veto; BRMS cannot approve against A)

### 4.1 Eligibility (Gate 0)
If Eligibility is false/stop ⇒ **FinalDecision = REJECT** (reason: ineligible).

### 4.2 Hard veto from Block A (no approval if A rejects)
If **T3 == HIGH_FRAUD** ⇒ **FinalDecision = REJECT** (top priority veto).
Else if **T2 == HIGH_RISK** ⇒ **FinalDecision = REJECT**.
Else if **T4 == HIGH_PAYOFF** ⇒ **FinalDecision = REJECT**.

> Interpretation: If any A sub-agent is HIGH, the request cannot be approved.  
> BRMS flags may still trigger REVIEW, but cannot flip REJECT -> APPROVE.

### 4.3 BRMS interaction (Block B is advisory / gating flags)
- If `brms_flags.gate_1 == "BLOCK"` OR `brms_flags.gate_2 == "BLOCK"` OR `brms_flags.gate_3 == "BLOCK"` ⇒ **FinalDecision = REVIEW** (not APPROVE).  
  Rationale: BRMS blocks indicate business-rule conflict; we escalate to manual review instead of approving.

- If BRMS is unavailable / times out ⇒ **fail-open** for MVP:
  - Do NOT block automatically.
  - Add a warning in reporter payload: `BRMS_UNAVAILABLE`.
  - Continue using A decisions + sensors.

### 4.4 REVIEW vs APPROVE when no A veto
If no A veto (no HIGH) then:
- If any of `{T3, T2, T4}` is a `REVIEW_*` ⇒ **FinalDecision = REVIEW**.
- Else if BRMS has any warnings/overrides/required_docs not empty ⇒ **FinalDecision = REVIEW**.
- Else ⇒ **FinalDecision = APPROVE**.

---

## 5) Output contract (minimal fields)

PolicyDecider outputs a `final_decision_v0_1` object:

- `final_outcome`: `APPROVE | REVIEW | REJECT`
- `primary_reason_code`: string (e.g., `FRAUD_HIGH`, `RISK_HIGH`, `PAYOFF_HIGH`, `BRMS_BLOCK`, `GRAY_ZONE`, `INELIGIBLE`)
- `supporting_reasons`: list[string] (short codes)
- `needs_manual_review`: boolean
- `meta_request_id`, `meta_generated_at`, `meta_latency_ms`

---

## 6) Determinism guarantees

Given the same:
- DecisionPack inputs (scores + thresholds),
- BRMS flags,
- sensor flags,
- and Eligibility,

the result must be identical (no external calls, no randomness).
