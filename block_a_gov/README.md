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

## Inventory (live) — status snapshot (2026-01-28)

### 1) ORIGINATE “Function>> as a connector/coordinator” — BRMS Bridge (Block B online-ish)
- ✅ Bridge server FastAPI running locally (`tools.brms_bridge_server`) with:
  - `GET /health`
  - `POST /bridge/brms_flags` -> `brms_flags_v0_1`
- ✅ Smoke E2E script available: `tools/smoke/smoke_e2e_live.sh` (integration) and `tools/smoke/smoke_e2e_stub.sh` (deterministic offline)
- ✅ Robust BRMS flags mapping against DMN gate shape variations (dict/str/null)

Recent commits:
- `4cbd5c1` Smoke: probe bridge /health before POST
- `1c391df` Bridge: make to_brms_flags_v0_1 robust to DMN gate shape (dict/str/null)
- `f8a502f` Chore: ignore smoke logs + backup artifacts

Remaining (cara %):
- 🔴 Formalize “Block B online” as real service: docker/compose, lifecycle, logs, healthcheck, stable URL/auth.

### 2) ORIGINATE “Function >> as a policy supervisor-decision maker” — PolicyDecider + FinalDecision (MVP)
- ✅ T3 adds `decision_fraud_norm` and contract `risk_decision_t3_v0_1`
- ✅ T2 adds `decision_default_norm`
- ✅ T4 adds `decision_payoff_norm`
- ✅ ORIGINATE emits `final_decision_v0_1` via pure `policy_decider_v0_1` (runtime)
- ✅ Specs added:
  - `block_a_gov/contracts/final_decision_v0_1.md`
  - `block_a_gov/contracts/policy_decider_v0_1.md`

Recent commits:
- `c5008a5` ORIGINATE: add pure policy_decider_v0_1 and emit final_decision_v0_1 (MVP)
- `df32483` T2: add decision_default_norm for PolicyDecider v0.1
- `f03c1a3` T4: add decision_payoff_norm for PolicyDecider v0.1
- `21356c7` Gov: add final_decision_v0_1 + policy_decider_v0_1 specs (cara # MVP)
- `581b6ae` Gov: add T3 contract risk_decision_t3_v0_1 (includes decision_fraud_norm)

Remaining (cara #):
- 🟡 Expand PolicyDecider beyond MVP_REVIEW_DEFAULT (real priority rules: Eligibility > BRMS hard blocks > Fraud > Default > Payoff)
- 🟡 Add structured reasons/dominant_signals mapping (still deterministic).

### 3) REPORTER Eligibility + Sensor Pack v0.1
- 🔴 Not started (implementation pending)
- 🔴 Wire Sensor Pack v0.1 into ORIGINATE beyond BRMS flags

