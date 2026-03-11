from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_RUNTIME_DIR = REPO_ROOT / "mock_runtime"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def load_json(value: str | Path) -> Dict[str, Any]:
    return json.loads(resolve_project_path(value).read_text(encoding="utf-8"))


def stable_unit_float(*parts: Any) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    numerator = int.from_bytes(digest[:8], "big")
    return numerator / float((1 << 64) - 1)


def stable_score(*parts: Any, floor: float = 0.05, ceil: float = 0.95) -> float:
    unit = stable_unit_float(*parts)
    return round(floor + (ceil - floor) * unit, 6)
