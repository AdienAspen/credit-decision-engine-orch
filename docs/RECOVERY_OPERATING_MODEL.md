# Recovery Operating Model

## Policy

This repository is stored on Windows-backed storage and is intended to be operated from WSL.

- Code and scripts live under `C:\...` and are used from Ubuntu as `/mnt/c/...`.
- Heavy datasets, checkpoints, models, artifacts, generated logs, and runtime environments live under `E:\...` and are used from Ubuntu as `/mnt/e/...`.
- WSL is runtime, tooling, and environment only.
- Critical project files must not live inside the WSL filesystem under `/home`.

## Practical Result

If WSL is damaged, reset, or reinstalled, the repository and data remain intact on the Windows volumes.

## Current Allocation

Repository root:

```bash
/mnt/c/Users/User/Coding-2025/BankLoan_Approval/ia-ml-credit-decision-engine
```

Operational heavy/runtime root:

```bash
/mnt/e/CODING-2025/Bank-Loan-Approval/BlockA-Ops
```

The repository keeps compatibility paths in place, while heavy/runtime directories are externalized to `BlockA-Ops`.

## Preferred Execution Pattern

```bash
cd /mnt/c/Users/User/Coding-2025/BankLoan_Approval/ia-ml-credit-decision-engine
./tools/smoke/demo_wsl.sh
```

Equivalent manual flow:

```bash
cd /mnt/c/Users/User/Coding-2025/BankLoan_Approval/ia-ml-credit-decision-engine
uv venv .venv-recovery
uv pip install --python .venv-recovery/bin/python -r requirements.txt
.venv-recovery/bin/python runners/originate.py --demo
```

## Notes

- Running through WSL is the preferred operating model for this recovery phase.
- Running directly from native Windows Python is optional, not required.
- The legacy `Data-Sets` corpus on `E:` is preserved untouched.
