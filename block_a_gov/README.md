# Block A — Gov Layer v0.1 (Spec-first)

Source of truth for Block A behavior. Runtime (LangGraph + local LLMs) must follow these artifacts.

Stack v0.1 (PoC):
- Orchestration: LangChain + LangGraph
- ORIGINATE: Qwen2.5-3B-Instruct (local, CPU)
- REPORTER: Qwen2.5-7B-Instruct (local, CPU)

Rule: .md governs; runtime can be swapped without breaking contracts.

## Specs (v0.1)
- spec/decision_pack_v0_1.md — Decision Pack contract + RISK_T2 payload
