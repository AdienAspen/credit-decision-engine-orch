# STUB→LIVE Promotion Gates v0.1

## Purpose
Define operational gates that keep STUB deterministic and promote LIVE to the primary lane only when integration is stable and auditable.

## Scope
Applies to ORIGINATE + T2/T3/T4 + BRMS bridge integration.

## Definition of Lanes
- **STUB**: deterministic/offline, uses local fixtures, no external dependencies.
- **LIVE**: real integration with BRMS bridge and external services.

## Promotion Gates (Checklist)

### Gate A — Canonical Aliases (source of truth)
- ✅ T2/T3/T4 runners read canonical aliases by default.
- ✅ ORIGINATE uses canonical BRMS policy snapshot.
- ✅ No hardcoded model paths in orchestration.
- Evidence: `block_a_gov/artifacts/*.json`, runner CLI defaults, `meta_brms_policy_snapshot` in pack.

### Gate B — Contract Validation (minimal required fields)
- ✅ T2/T3/T4 outputs validated.
- ✅ `brms_flags_v0_1` validated in STUB and LIVE.
- ✅ `final_decision_v0_1` validated.
- Evidence: `runners/contract_validate.py`, runner/originate validations, smoke outputs.

### Gate C — Meta Homogeneity (observability)
- ✅ `meta_request_id`, `meta_client_id` aligned across pack + decisions.
- ✅ `meta_latency_ms` present for pack + final_decision.
- ✅ `brms_flags.meta_generated_at` aligned to pack in STUB; live uses real values.
- Evidence: `tools/smoke/_logs/last_decision_pack.json`, `tools/smoke/_logs/last_decision_pack_live.json`.

### Gate D — E2E Smokes Green (with evidence)
- ✅ STUB smoke passes with deterministic outcome.
- ✅ LIVE smoke passes with BRMS bridge health + POST OK.
- ✅ Snapshots captured for DMN + BRMS flags.
- Evidence: `tools/smoke/_logs/last_dmn_context.json`, `tools/smoke/_logs/last_dmn_eval.json`, `tools/smoke/_logs/last_brms_flags.json`.

### Gate E — Fail-Open Behavior Controlled
- ✅ If LIVE fails, ORIGINATE falls back to STUB without breaking contracts.
- ✅ Fail-open is explicit in `final_reason_code`.
- Evidence: smoke logs + final decision outputs.

## Promotion Decision
LIVE becomes primary only when all gates A–E are ✅.

## Operational Notes
- STUB remains as a deterministic fallback for regression and outage isolation.
- No mixing: avoid ad-hoc hacks that bypass contracts or aliases in LIVE.

