FinalDecision v0.1 (spec)
Purpose: single, auditable final outcome computed deterministically from Eligibility + DecisionPack(A) + BRMSFlags(B) + SensorPack.
Schema (JSON)
	• meta_schema_version: "final_decision_v0_1"
	• meta_generated_at (ISO8601 UTC)
	• meta_request_id
	• meta_client_id
	• meta_policy_id (from BRMS Context if present, else "unknown")
	• meta_policy_version (else "unknown")
	• meta_validation_mode (else "unknown")
	• final_outcome (enum): APPROVE | REJECT | REVIEW
	• final_reason_code (enum-ish string): e.g. FRAUD_HARD_BLOCK, DEFAULT_HIGH_RISK, BRMS_HARD_BLOCK, MISSING_SIGNALS, DISCREPANCY_A_VS_B, etc.
	• dominant_signals (list of short strings, max ~5)
	• required_docs (list of strings)
	• warnings (list of strings)
	• overrides_applied (list of strings)
	• audit (object):
		○ a_summary: {t2_default:..., t3_fraud:..., t4_payoff:...} minimal
		○ b_summary: {gate_1, gate_2, gate_3} minimal (if present)
		○ sensor_summary: minimal (if present)
		○ confidence (0–1, optional but useful)
		○ latency_ms_total (optional)


