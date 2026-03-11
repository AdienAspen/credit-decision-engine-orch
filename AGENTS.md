# AGENTS.md

**Agent Development Rules — Agentic Credit Risk Platform**

This document defines the **operational rules for AI agents working in this repository**.
All automated agents (Codex, AI coding assistants, or autonomous engineering agents) must follow these guidelines.

This repository represents the **Block A — Agentic Orchestration Layer** of a credit-risk decision platform.

---

# 1. Development Philosophy

The project follows a **spec-first / contract-driven engineering model**.

Implementation must always respect the **governance layer**.

System behavior must be derived from:

```
block_a_gov/
```

This directory defines:

* system contracts
* decision schemas
* canonical artifacts
* governance documentation

These files represent the **source of truth** for the system.

Implementation must **never contradict existing contracts**.

---

# 2. Contract-Driven Development

All features must follow this workflow:

```
specification
→ contract
→ interface
→ implementation
```

Agents must inspect:

```
block_a_gov/
```

before implementing new behavior.

If a contract does not exist, the agent must:

1. propose a contract
2. define the interface
3. implement the feature

Never bypass this process.

---

# 3. Non-Destructive Editing (Mandatory)

Agents must perform **safe modifications**.

Forbidden actions:

* large file rewrites
* deleting unknown modules
* removing historical code
* altering contracts
* rewriting repository structure

Preferred strategy:

```
minimal diff
incremental patch
isolated modification
```

If unsure:

```
add new adapter
wrap existing logic
create mock implementation
```

Do not modify existing logic unless necessary.

---

# 4. Architecture Preservation

The repository represents an **agentic decision architecture**.

The conceptual pipeline must remain visible:

```
ORIGINATE
   │
   ├── Dynamic Sensors
   │
   ├── Risk Models
   │      T2 — Default Risk
   │      T3 — Fraud Detection
   │      T4 — Payoff Prediction
   │
   └── Decision Layer (BRMS)
```

Even when using mock components, this architecture must remain intact.

---

# 5. Mock Demonstrator Mode

The current project phase focuses on restoring a **demonstrable architecture**.

Original production components may not exist anymore.

Therefore:

| Component | Replacement           |
| --------- | --------------------- |
| ML models | mock predictors       |
| BRMS      | mock decision service |
| sensors   | synthetic generators  |

The objective is **architectural demonstration**, not production accuracy.

---

# 6. Storage and Execution Model

This repository follows a **Windows-backed storage + WSL runtime model**.

That means:

- repository code and scripts live on Windows-backed storage such as `C:\...`
- heavy datasets, checkpoints, models, and large artifacts live on `E:\...`
- WSL is used for runtime, tooling, automation, and execution
- critical project files must not live inside the WSL filesystem under `/home`

Operationally, this means the repository is expected to be used from Ubuntu/WSL through mounted paths such as:

```
/mnt/c/Users/User/Coding-2025/BankLoan_Approval/ia-ml-credit-decision-engine
/mnt/e/...
```

This policy preserves the Linux developer workflow while protecting project assets if WSL is reset, damaged, or replaced.

---

# 7. Path Independence

Legacy paths referencing the original WSL environment may exist:

```
/home/adien/loan_backbone_ml_BLOCK_A_AGENTS/
```

Agents must replace these assumptions with **project-relative paths** or with the new mounted execution model under `/mnt/c/...` and `/mnt/e/...`.

Example repository layout:

```
repo-root/
block_a_gov/
runners/
tools/
testing/
```

All commands must run from the repository root.

---

# 8. Reproducible Environment

The repository should support **portable environment reconstruction**.

Recommended tooling:

```
uv
```

Target workflow:

```
uv venv
uv pip install -r requirements.txt
```

Preferred execution context:

```bash
cd /mnt/c/Users/User/Coding-2025/BankLoan_Approval/ia-ml-credit-decision-engine
uv venv
uv pip install -r requirements.txt
python runners/originate.py --demo
```

Agents may add:

* `pyproject.toml`
* `requirements.txt`

if missing.

---

# 9. Debugging Rules

Debugging must follow a **minimal-surface approach**.

Procedure:

1. isolate failure
2. inspect input/output
3. patch the smallest component
4. retest

Avoid large refactors during debugging.

Preferred pattern:

```
small fix
targeted patch
pipeline test
```

---

# 10. Language Policy (Strict)

Language usage rules:

### Chat / discussion

Allowed:

* Spanish
* English
* Spanglish

### Repository content

All repository artifacts must use **American English**.

This includes:

* source code
* comments
* documentation
* commit messages
* scripts

Example comment format:

```
## Validate request payload against decision contract
```

Spanish must **never appear inside repository files**.

---

# 11. Git History Integrity

This repository contains **milestone tags** representing project evolution.

Agents must **never rewrite history**.

Forbidden actions:

```
git rebase -i on historical tags
tag deletion
history rewriting
```

Tags must remain preserved.

---

# 12. Documentation Preservation

Documentation must never be deleted.

Allowed actions:

```
append
annotate
extend
```

Never overwrite historical content unless the user explicitly asks for it.

Documentation represents the **development history of the project**.

---

# 13. Demonstration Command

The final system should support a simple demonstration entrypoint.

Example:

```
python runners/originate.py --demo
```

This command should execute the full decision pipeline using mock services.

The goal is **architecture demonstration**.

---

# 14. Decision Priority

When making engineering decisions, prioritize:

```
contract integrity
architectural clarity
reproducibility
minimal modification
```

This repository represents the **design blueprint of the system**.

Agents must ensure the architecture remains understandable and executable.

---

## AI Agent Guidelines

This repository contains an `AGENTS.md` file describing
the development rules for automated engineering agents.
Any AI agent interacting with the repository must follow
those guidelines.

---

# End of Agent Rules
