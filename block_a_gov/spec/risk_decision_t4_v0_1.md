# RISK_T4 — Output contract (v0.1)

## Schema
- meta_schema_version: risk_decision_t4_v0_1

Required:
- meta_schema_version
- meta_generated_at (ISO-8601 UTC)
- meta_request_id (string|null)
- meta_client_id (string)
- meta_model_tag
- meta_model_file
- meta_threshold_mode
- meta_latency_ms (int)

Scores/threshold/decision:
- score_payoff_prob (float [0,1])
- thr_payoff (float [0,1])
- decision_payoff (LOW_PAYOFF | HIGH_PAYOFF)
