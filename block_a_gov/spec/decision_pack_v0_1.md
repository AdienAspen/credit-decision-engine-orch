# Decision Pack v0.1 — Contract (PoC)

**Scope:** Block A (agentic runtime).  
**Owner:** ORIGINATE (aggregator / coordinator).  
**Goal:** Produce a single, structured payload that is traceable, auditable, and stable for PoC demos.

---

## 1) Inputs (to ORIGINATE)

### A) Request Core (minimum)
- `client_id` (string)
- `request_id` (string)
- `as_of` (ISO-8601, optional)
- `seed` (int, optional, for deterministic mocks)

### B) EnrichedFeatureVector (EFV) v0.1 (from Z)
ORIGINATE is the **only** component that calls dynamic sensors and builds EFV.

EFV v0.1 provides:
- `static_*` minimal backbone fields (may be null in PoC)
- `dyn_*` sensor scores (transaction anomaly, device behavior, bureau spike, market stress)
- `dyn_sensor_source_map`, `dyn_sensor_latency_ms_map`
- `meta_*` tracing fields

---

## 2) Outputs (Decision Pack v0.1)

Decision Pack is emitted by ORIGINATE after running:
- ELIGIBILITY
- Risk sub-agents (T2/T3/T4)
- (Optional) BRMS flags bridge
- (Optional) REPORTER flow (does NOT change decisions)

### A) Top-level envelope (minimum)
- `meta_schema_version` = `decision_pack_v0_1`
- `meta_generated_at` (ISO-8601 UTC)
- `meta_request_id` (string)
- `meta_client_id` (string)
- `efv` (object, EFV v0.1)
- `risk_t2` (object, see contract below)
- `risk_t3` (optional, v0.1)
- `risk_t4` (optional, v0.1)
- `brms_flags` (optional)
- `final_decision` (optional in v0.1; may be produced later)

---

## 3) Sub-agent contract — RISK_T2 (Default)

### Purpose
Given EFV + static/backbone features, RISK_T2 emits:
- a probability score
- an operating threshold (OP_A or OP_B)
- a discrete decision for T2 risk

### Output payload (exact fields v0.1)
**Schema version:** `risk_decision_t2_v0_1`

Required:
- `meta_schema_version` (string) = `risk_decision_t2_v0_1`
- `meta_generated_at` (ISO-8601 UTC)
- `meta_request_id` (string|null)
- `meta_client_id` (string)
- `meta_model_tag` (string) — e.g. `t2_default_xgb_v3a_microA`
- `meta_model_file` (string) — path or logical URI
- `meta_operating_point` (string) — `op_a_best_f1_under_flag` | `op_b_max_recall_under_flag`
- `meta_latency_ms` (int)

Scores/threshold/decision:
- `score_default_prob` (float in [0,1])
- `thr_default` (float in [0,1])
- `decision_default` (string) — `LOW_RISK` | `HIGH_RISK`

Operating point reference (for audit):
- `op_ref.threshold` (float)
- `op_ref.precision` (float)
- `op_ref.recall` (float)
- `op_ref.f1` (float)
- `op_ref.flag_rate` (float)

### Insertion point (where it lives)
In Decision Pack:
- `decision_pack.risk_t2 = <RISK_T2 payload above>`

Optional convenience mapping (if we later want flattened fields):
- `decision_pack.score_t2_default_prob = risk_t2.score_default_prob`
- `decision_pack.thr_t2_default = risk_t2.thr_default`
- `decision_pack.decision_t2_default = risk_t2.decision_default`

---

## 4) Notes (PoC constraints)

- RISK_T2 must be deterministic when inputs are deterministic (seed/request_id), when applicable.
- RISK_T2 must not call dynamic sensors directly (ORIGINATE only).
- Threshold choice is controlled via `operating_pick.json` (OP_A / OP_B).

---

## RISK_T3 (Fraud) — Output payload (exact fields v0.1)
**Schema version:** `risk_decision_t3_v0_1`

Required:
- `meta_schema_version` (string) = `risk_decision_t3_v0_1`
- `meta_generated_at` (ISO-8601 UTC)
- `meta_request_id` (string|null)
- `meta_client_id` (string)
- `meta_model_tag` (string) — e.g. `fraud_t3_ieee_xgb_bcd_best`
- `meta_model_file` (string) — path or logical URI
- `meta_threshold_mode` (string) — e.g. `thr_valid_recall_ge_0_90` | `thr_valid_recall_ge_0_95` | `thr_valid_precision_ge_0_70`
- `meta_latency_ms` (int)

Scores/threshold/decision:
- `score_fraud_prob` (float in [0,1])
- `thr_fraud` (float in [0,1])
- `decision_fraud` (string) — `LOW_FRAUD` | `HIGH_FRAUD`

## RISK_T4 — PAYOFF (v0.1)

### Output payload (exact fields v0.1)
**Schema version:** `risk_decision_t4_v0_1`

Required:
- `meta_schema_version` (string) = `risk_decision_t4_v0_1`
- `meta_generated_at` (ISO-8601 UTC)
- `meta_request_id` (string|null)
- `meta_client_id` (string)
- `meta_model_tag` (string) — e.g. `t4_payoff_xgb_v1_guarded`
- `meta_model_file` (string) — path or logical URI
- `meta_threshold_mode` (string) — e.g. `thr_valid_best_f1` | `thr_valid_recall_ge_0_90` | `thr_valid_recall_ge_0_95`
- `meta_latency_ms` (int)

Scores/threshold/decision:
- `score_payoff_prob` (float in [0,1]) — P(TARGET_PAYOFF=1)
- `thr_payoff` (float in [0,1])
- `decision_payoff` (string) — `LOW_PAYOFF_RISK` | `HIGH_PAYOFF_RISK`

<!-- RISK_T4_PAYOFF_BLOCK_START -->
## RISK_T4 — PAYOFF (v0.1)

### Output payload (exact fields v0.1)
**Schema version:** `risk_decision_t4_v0_1`

Required:
- `meta_schema_version` (string) = `risk_decision_t4_v0_1`
- `meta_generated_at` (ISO-8601 UTC)
- `meta_request_id` (string|null)
- `meta_client_id` (string)
- `meta_model_tag` (string) — e.g. `t4_payoff_xgb_v1_guarded`
- `meta_model_file` (string) — path or logical URI
- `meta_threshold_mode` (string) — e.g. `thr_valid_best_f1` | `thr_valid_recall_ge_0_90` | `thr_valid_recall_ge_0_95`
- `meta_latency_ms` (int)

Scores/threshold/decision:
- `score_payoff_prob` (float in [0,1])
- `thr_payoff` (float in [0,1])
- `decision_payoff` (string) — `LOW_PAYOFF` | `HIGH_PAYOFF`
<!-- RISK_T4_PAYOFF_BLOCK_END -->

