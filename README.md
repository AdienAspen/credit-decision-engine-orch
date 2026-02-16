# Block A — Agentic ML Platform (PoC/MVP)

A **contract-driven, mock-first** agentic ML platform that orchestrates multiple
risk evaluators and optional business rules to produce a **final decision**
(Approve / Review / Reject) with **traceability**.

> ✅ This repository contains **Block A** (the agentic ML engine).  
> 🔌 It can optionally integrate with **Block B** (a BRMS decision platform),
> which typically runs as containerized services.

---

## Why this exists

Most early systems fail because of **integration**, not modeling:
timeouts, missing fields, schema drift, unclear ownership, and
non-auditable decisions.

This repo is built to keep the **interfaces stable** while allowing you to:
- **Prove the end-to-end flow** with deterministic mock data (PoC/MVP)
- **Swap in real connectors** later (production) without rewriting orchestration

---

## What it does (in plain language)

Given an incoming application request, the system:

- runs a **workflow** that coordinates agents
- fetches **dynamic signals** (mock or live)
- runs specialized **risk sub-agents**
- optionally calls a **rules engine** (Block B) for governance gates
- produces a **final decision artifact** with reasons, warnings, and timing

---

## Architecture overview

### Block A — Agentic ML Platform (this repo)

Block A is the core engine that coordinates:
- **workflow agents** (routing and orchestration)
- **risk sub-agents** (default, fraud, payoff/affordability)
- **dynamic signals** (transaction anomaly, device/behavior, bureau, macro)
- **final reporting** (decision + trace)

### Block B — Decision Platform (BRMS)

Block B is an optional, external decision platform that provides:
- auditable governance rules (decision tables + rule sets)
- containerized runtime (typically Docker + a decision server)
- a stable API surface exposed to Block A via a thin **bridge**

---

## System flow (global)

```text
+-------------------------------+
| Incoming Application          |
| (request / applicant context) |
+---------------+---------------+
                |
                v
+-------------------------------+
| Block A: Agentic ML Platform  |
| - Workflow Agent              |
| - Eligibility Agent           |
| - ORIGINATE (orchestrator)    |
| - Risk Sub-Agents             |
| - Final Reporter              |
+---------------+---------------+
                |
                | (optional)
                v
+-------------------------------+
| Block B: Decision Platform    |
| (BRMS / DMN / Rule Sets)      |
| - container runtime           |
| - bridge API                  |
+---------------+---------------+
                |
                v
+-------------------------------+
| Final Decision Artifact       |
| (decision + reasons + trace   |
|  + warnings)                  |
+-------------------------------+
```

---

## Block A in detail (agents and responsibilities)

### Core agents

- **Workflow Agent**
  - Routes the request through the correct path.
  - Ensures a consistent order of operations.

- **Eligibility Agent**
  - Runs early screening to stop invalid or obviously risky requests.
  - Keeps the rest of the pipeline efficient.

- **ORIGINATE (Orchestrator Agent)**
  - Fetches/consumes dynamic signals (mock or live).
  - Calls risk sub-agents and collects outputs.
  - Optionally calls Block B for governance rules.
  - Produces the unified decision payload.

- **Final Reporter Agent**
  - Finalizes the output contract.
  - Ensures traceability: reasons, warnings, timing, sources.

### Risk sub-agents

- **Default Risk Sub-Agent**
  - Estimates probability of non-payment / default.

- **Fraud Risk Sub-Agent**
  - Estimates likelihood of fraud or identity misuse.

- **Payoff / Affordability Sub-Agent**
  - Estimates repayment capability and affordability risk.

---

## Dynamic signals (what they are, and how they behave)

Dynamic signals are small checks that return extra context.

Typical signals include:
- **Transaction anomaly**
  - Unusual patterns that can indicate fraud or instability.
- **Device / behavior**
  - Suspicious sessions, device changes, automation-like behavior.
- **Bureau spike**
  - Sudden credit bureau changes or new risk events.
- **Market / macro**
  - Environment regime (calm vs stress), used as a soft factor.

### Mock-first, live-later

The system treats live as an **interface**, not a fixed provider:
- PoC/MVP: signals come from deterministic placeholder datasets
- Production: signals come from real connectors (HTTP / DB / API)

### Reliability rule: fallback is mandatory

When a live signal fails (timeout / error), Block A:
- falls back to deterministic mock data
- records the degradation in the final output

Each signal should be traceable with:
- **mode**: mock or live
- **status**: ok / fallback / missing
- **as-of timestamp**
- **source type**
- **latency**
- **warnings**

---

## ASCII: Block A internal workflow

```text
Incoming Request
      |
      v
+---------------------------+
| Workflow Agent            |
+-------------+-------------+
              |
              v
+---------------------------+
| Eligibility Agent         |
+------+--------------------+
       |
       | APPROVED
       v
+---------------------------+
| ORIGINATE (Orchestrator)  |
+------+--------------------+
       |   fetch/consume dynamic signals
       |   - transaction anomaly
       |   - device / behavior
       |   - bureau spike
       |   - market / macro
       |
       |   run risk sub-agents
       |   - default risk
       |   - fraud risk
       |   - payoff / affordability risk
       |
       |   optional BRMS call via bridge
       v
+---------------------------+
| Final Reporter            |
+-------------+-------------+
              |
              v
+---------------------------+
| Final Decision Artifact   |
+---------------------------+
```

---

## Repository structure (high-level)

- **Root directory**
  - Everything needed to run Block A and validate end-to-end flows.

- **Governance directory**
  - Contracts, schemas, versioning rules, canonical references.

- **Runners directory**
  - Stable command-line entrypoints for agents and workflows.

- **Core source directory**
  - Orchestration logic, adapters, validation, utilities.

- **Testing directory**
  - Unit tests, contract tests, lightweight integration tests.

- **Tools directory**
  - Smoke tests, debugging helpers, persistent logs.

- **Configs / Docs / Reports**
  - Configuration, docs, and run outputs.

---

## Stable runtime via canonical references

To avoid changing code to change models, Block A relies on stable pointers:
- active model file reference
- selected operating threshold
- expected contract versions

This supports controlled swaps without rewriting orchestration.

---

## Roadmap (high-level)

- **Production connectors**
  - Standardized adapters (HTTP / file / DB) with consistent
    timeouts and retries.

- **Stronger contract validation**
  - Strict schema checks and additive-only interface evolution.

- **Promotion gates (PoC to production)**
  - A checklist that ensures reliability before turning on live mode.

- **Better reason codes**
  - More structured outputs for audits and stakeholders.

---

## Contribution guidelines

- Prefer **additive** interface changes.
- Treat governance specs as the source of truth.
- Keep commits small and reproducible with smoke runs.
- Never hide failures: record them via warnings and trace fields.

---

## README maintenance policy (canonical root README)

This root `README.md` is a controlled artifact and the canonical repository overview.

Rules:
- evolve with **additive, non-destructive** updates
- preserve scope, style, and architectural intent
- avoid destructive rewrites or accidental resets
- manage changes through intentional Git commits (with review when needed)

---

## License

TBD
