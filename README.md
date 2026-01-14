# Block A — Agentic Platform (PoC)

This repo owns **Block A**: ORIGINATE + sub-agents (T2/T3/T4) + (future) REPORTER.

**Methodology:** spec-first. The Gov Layer (`block_a_gov/`) defines contracts and canonical pointers.
Runtime can evolve (LangGraph, different LLM backends) without breaking those contracts.

## What is implemented (current)
### Gov layer (source of truth)
- `block_a_gov/spec/` — v0.1 contracts:
  - `decision_pack_v0_1.md`
  - `risk_decision_t2_v0_1.md`
  - `risk_decision_t3_v0_1.md`
  - `risk_decision_t4_v0_1.md`
- `block_a_gov/artifacts/` — canonical aliases (swap-friendly):
  - `t2_default_canonical.json`
  - `t3_fraud_canonical.json`
  - `t4_payoff_canonical.json`

### Sub-agent runners (stable CLIs)
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

Milestone (S1.4): ORIGINATE MVP assembles Decision Pack v0.1 with end-to-end traceability (single request_id) and T2/T3/T4 sub-agents decoupled via canonical aliases.


## ORIGINATE wiring (v0.1) — inputs / outputs (text diagram)


Eligibility (Gate 0)
└─ eligibility_signal_v0_1 (start/stop / minimal request validity)
|
v
ORIGINATE (core orchestrator)
Inputs:
A) decision_pack_v0_1 (T2/T3/T4 runner outputs via canonical aliases)
B) sensor_pack_v0_1 (dynamic sensors: market/behavior/device/bureau, etc.)
C) brms_flags_v0_1 (Block B rules/gates/warnings fetched via API/MCP)
D) request_context_v0_1 (meta: request_id, client_id, trace, timestamps)

Output:
final_decision_v0_1 ──> REPORTER input payload (narrative + audit-ready summary)
Notes:
- ORIGINATE is the integration brain: it **consumes** signals from A (ML), sensors, and B (BRMS rules).
- Block B is not fed by Block A; Block B is queried by ORIGINATE for business-rule signals.

