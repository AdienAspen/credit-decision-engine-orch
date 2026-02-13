# Block A — Agentic Platform (PoC)

This repo owns **Block A**: WORK-FLOW + ELIGIBILITY + ORIGINATE + sub-agents (T2/T3/T4) + (future) REPORTER.

**Methodology:** spec-first. The Gov Layer (`block_a_gov/`) defines contracts and canonical pointers.
Runtime can evolve (LangGraph, different LLM backends) without breaking those contracts.

## What is implemented (current)
### Gov layer (source of truth)
- `block_a_gov/spec/` — v0.1 contracts:
  - `application_intake_v0_1.md`
  - `eligibility_agent_status_v0_1.md`
  - `eligibility_agent_rules_v0_1.md`
  - `originate_post_eligibility_input_v0_1.md`
  - `originate_dynamic_fraud_signals_v0_1.md`
  - `decision_pack_v0_1.md`
  - `risk_decision_t2_v0_1.md`
  - `risk_decision_t3_v0_1.md`
  - `risk_decision_t4_v0_1.md`
- `block_a_gov/artifacts/` — canonical aliases (swap-friendly):
  - `eligibility_canonical.json`
  - `t2_default_canonical.json`
  - `t3_fraud_canonical.json`
  - `t4_payoff_canonical.json`

### Sub-agent runners (stable CLIs)
- `runners/runner_workflow.py` — emits `application_intake_v0_1` (STUB-first)
- `runners/runner_eligibility.py` — emits `eligibility_agent_status_v0_1` (STUB-first)
- `runners/runner_workflow_eligibility.py` — mini-orchestrator:
  - `APPROVED` -> calls `originate.py`
  - `REJECTED`/`REVIEW_REQUIRED` -> early-cut `final_decision_v0_1`
- `runners/runner_t2.py` — emits `risk_decision_t2_v0_1` (operating point from canonical alias)
- `runners/runner_t3.py` — emits `risk_decision_t3_v0_1` (threshold mode from canonical alias)
- `runners/runner_t4.py` — emits `risk_decision_t4_v0_1` (robust panel_valid thresholds; optional override-thr)

## Quickstart (Terminal WORK)
```bash
cd /home/adien/loan_backbone_ml_BLOCK_A_AGENTS
source .venv/bin/activate

python3 runners/runner_t2.py --client-id 100001 --seed 42 | head
python3 runners/runner_t3.py --client-id 100001 --seed 42 | head
python3 runners/runner_t4.py --client-id 100001 --seed 42 | head
python3 runners/runner_workflow.py --client-id 100001 --seed 42 | head
python3 runners/runner_eligibility.py --intake-json tools/smoke/_logs/last_application_intake_stub.json | head
python3 runners/runner_workflow_eligibility.py --client-id 100001 --seed 42 --brms-stub tools/smoke/fixtures/brms_all_pass.json | head

Milestone (S1.4): ORIGINATE MVP assembles Decision Pack v0.1 with end-to-end traceability (single request_id) and T2/T3/T4 sub-agents decoupled via canonical aliases.


## System wiring (v0.1) — WORK-FLOW -> ELIGIBILITY -> ORIGINATE


WORK-FLOW (runner_workflow.py)
└─ emits `application_intake_v0_1`
|
v
ELIGIBILITY AGENT (runner_eligibility.py)
└─ emits `eligibility_agent_status_v0_1`
|
+-- REJECTED / REVIEW_REQUIRED -> early-cut `final_decision_v0_1` (no T2/T3/T4, no BRMS)
|
+-- APPROVED -> ORIGINATE (core orchestrator)
              Inputs:
              A) T2/T3/T4 decision outputs via canonical aliases
              B) sensor signals for ORIGINATE lane
              C) brms_flags_v0_1 from Block B bridge
              Output:
              `final_decision_v0_1` -> REPORTER input payload

Notes:
- ORIGINATE remains post-gate coordinator (it runs only after `eligibility_status=APPROVED` in the mini-orchestrator lane).
- Eligibility Agent is independent from BRMS Gate_1 naming/logic in this MVP.
- Block B is queried by ORIGINATE for business-rule signals; Block B is not fed by Block A in this PoC.


## Smoke (online BRMS)
```bash
bash tools/smoke/smoke_workflow_stub.sh
bash tools/smoke/smoke_eligibility_stub.sh
bash tools/smoke/smoke_workflow_eligibility_stub.sh
bash tools/smoke/smoke_originate_fraud_signals_stub.sh
bash tools/smoke/smoke_originate_fraud_signals_live.sh
python3 runners/originate.py --client-id 100001 --seed 42 --brms-url http://localhost:8090/bridge/brms_flags | grep -n "brms_flags"
```
