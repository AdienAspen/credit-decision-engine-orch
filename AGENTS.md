# AGENTS.md — Working rules for this repo (Adien)

## 0) Mission
Help Adien ship changes **fast, safely, and reproducibly**.
Primary goals:
1) Keep changes **auditable** (scripts + logs + versioned artifacts).
2) Avoid time sinks (anti-loop rules).
3) Prefer minimal, correct edits over big refactors.

## 1) Ground rules (non-negotiable)
- **BASH-first:** Any operational step must be runnable from terminal using a bash block/script.
  - If Python is needed, call it from bash (e.g., `python3 ...`), still BASH-first.
- **Spec-first:** Treat repo `.md` under governance/spec as source-of-truth when present.
- **Mode debug corto:** When debugging, propose **one micro-step at a time**.
- **Anti-loop:** If the same failure repeats, **declare the loop** and change tactics:
  - Reduce surface area (one file / one command),
  - Capture logs persistently,
  - Avoid repeating the same recipe.

## 2) How to operate in this codebase
### 2.1 Terminal conventions
- If a service must be running, label commands clearly as:
  - **Terminal SERVER**: keep server running
  - **Terminal WORK**: run client/smokes/tests
- If possible, offer an alternative single-terminal approach using background `&` and `kill`.

### 2.2 Always include positioning inside bash
All “positioning” must be included **inside the bash block**:
- `cd <repo_root>`
- `source .venv/bin/activate` (if needed)
Do not assume current directory or env.

### 2.3 Logging policy (persistent)
- Prefer persistent logs to avoid losing failures when terminals close.
- If repo has `tools/smoke/_logs/`, use it.
- Always print the path to the log file produced.

## 3) Default workflow
When asked to implement something:
1) Identify the **minimal file(s)** to change.
2) Propose **one** bash block that:
   - positions correctly,
   - applies changes,
   - runs a verification command (lint/test/smoke).
3) Summarize expected output and where logs/artifacts land.

## 4) Safety rails for changes
- Keep diffs small and reversible.
- Prefer adding new files over risky in-place rewrites (unless explicitly requested).
- When modifying scripts, avoid breaking offline/stub flows.
- If there are canonical aliases (e.g., `*_canonical.json`), update them carefully and keep backward compatibility.

## 5) Repo-specific context (short)
- Repo root (typical): `/home/adien/loan_backbone_ml_BLOCK_A_AGENTS`
- There is an E2E split concept:
  - **STUB**: deterministic/offline
  - **LIVE**: real integration
- Smokes/logging often live under `tools/smoke/` (and `_logs/`).

## 6) What to ask the user (only if truly blocking)
Avoid questions unless needed to proceed.
If blocked, ask for **one** of:
- the exact command output/error,
- the path of the file involved,
- whether we are in STUB or LIVE mode.

## 7) Definition of Done (DoD)
A change is “done” when:
- It runs via bash exactly as written,
- Produces expected artifacts/logs,
- Does not break STUB determinism (unless requested),
- Minimal documentation update if behavior changed.
