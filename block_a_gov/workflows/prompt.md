# Workflows v0.1 — Execution playbooks

## ORIGINATE_DECISION_FLOW
1) Load Request Core + EFV v0.1 (from DS_Z)
2) Run ELIGIBILITY
   - If fail => final_decision = REJECT + reason_codes; emit Decision Pack; (optional) REPORTER
3) Run risk sub-agents (T2/T3/T4)
4) Fetch BRMS flags via BRMS_BRIDGE
5) Aggregate & resolve conflicts => REVIEW when needed
6) Emit Decision Pack v0.1 (structured)
7) Trigger REPORTER_FLOW if REVIEW/REJECT or requested

## REPORTER_FLOW
1) Read Decision Pack
2) Retrieve policies (RAG) if configured
3) Generate report: decision + motives + evidence + next steps
4) Validate: no hallucinated policies; missing evidence => explicit
