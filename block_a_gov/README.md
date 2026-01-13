# Block A — Gov Layer v0.1 (Spec-first)

This directory is the **source of truth** for Block A behavior.
Runtime (LangGraph + local LLMs) must follow these artifacts.

**Rule:** `.md` governs; runtime can be swapped without breaking contracts.

## Stack v0.1 (PoC)
- Orchestration: LangChain + LangGraph
- ORIGINATE: Qwen2.5-3B-Instruct (local, CPU)
- REPORTER: Qwen2.5-7B-Instruct (local, CPU)

## What is governed here
- **Contracts** (schemas) for runner outputs and orchestration handoffs
- **Decision Pack** contract (what ORIGINATE must assemble)
- **Canonical aliases** to swap model/threshold pointers without rewriting runtime

## Specs (v0.1)
Located in `spec/`:
- `spec/spec.md` — Gov conventions, rules, and spec-first workflow
- `spec/decision_pack_v0_1.md` — Decision Pack contract (ORIGINATE output)
- `spec/risk_decision_t2_v0_1.md` — T2 runner output contract
- `spec/risk_decision_t3_v0_1.md` — T3 runner output contract
- `spec/risk_decision_t4_v0_1.md` — T4 runner output contract

## Canonical aliases (swap-friendly)
Runners must read **only** these aliases by default:
- `artifacts/t2_default_canonical.json` — T2 model + feature list + operating pick (op_a/op_b)
- `artifacts/t3_fraud_canonical.json` — T3 model + thresholds alias
- `artifacts/t4_payoff_canonical.json` — T4 model + feature list + thresholds panel

## Versioning rules
- v0.1 contracts are **strict**: do not rename existing fields.
- Additive changes only (new fields → v0.2+).
- Aliases can change pointers (model/threshold files) without breaking runtime.
