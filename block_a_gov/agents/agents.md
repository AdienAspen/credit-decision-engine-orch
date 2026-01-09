# Agents v0.1 — Roles, permissions, rules

## ORIGINATE
- Role: coordinator + aggregator + near-final decider
- Can: call DS_Z (EFV), call scoring tools (T2/T3/T4), call BRMS bridge, assemble Decision Pack
- Cannot: generate long policy text (delegate to REPORTER)

Rules:
- Eligibility is a hard gate
- Conflict resolution => REVIEW
- Fallback: if BRMS missing => continue with warning; if eligibility missing => hard stop

## ELIGIBILITY
- Role: entry gate checks
- Output: eligibility_pass/fail + reasons

## RISK_T2 / RISK_T3 / RISK_T4
- Role: scoring + thresholding
- Output: score_* + thr_* + decision_* + meta_* (model_version, latency_ms)
- Rule: no dependency on raw datasets in runtime; deterministic when seed provided

## BRMS_BRIDGE
- Role: query Block B and normalize flags
- Output: brms_flags + rule_hits (structured, no free text)

## REPORTER
- Role: explanation + RAG policies
- Reads: Decision Pack + policies
- Cannot: change decision
- Rule: explain with evidence slots; if missing evidence => explicit
