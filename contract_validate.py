"""
Root shim for contract validation.

Why:
- Real implementation lives at runners/contract_validate.py
- When running from repo root (e.g., python -c / heredoc), `import contract_validate`
  would fail unless we expose a root module.

This shim dynamically loads the real module and re-exports its public symbols.
"""
from __future__ import annotations

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "runners" / "contract_validate.py"
if not _REAL.exists():
    raise ModuleNotFoundError(f"Missing real module at: {_REAL}")

_spec = spec_from_file_location("contract_validate", str(_REAL))
if _spec is None or _spec.loader is None:
    raise ImportError(f"Failed to create module spec for: {_REAL}")

_mod = module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[attr-defined]

# Re-export everything (excluding private names)
globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("_")})
