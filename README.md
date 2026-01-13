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

