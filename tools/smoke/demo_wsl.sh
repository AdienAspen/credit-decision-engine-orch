#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${PY:-$ROOT/.venv-recovery/bin/python}"
if [[ ! -x "$PY" ]]; then
  echo "[DEMO_WSL] recovery env not found; creating .venv-recovery"
  uv venv .venv-recovery
  uv pip install --python .venv-recovery/bin/python -r requirements.txt
  PY="$ROOT/.venv-recovery/bin/python"
fi

LOG_DIR="$ROOT/tools/smoke/_logs"
mkdir -p "$LOG_DIR"
OUT_JSON="$LOG_DIR/demo_latest.json"

echo "[DEMO_WSL] root=$ROOT"
echo "[DEMO_WSL] python=$PY"
echo "[DEMO_WSL] output=$OUT_JSON"

"$PY" runners/originate.py --demo > "$OUT_JSON"
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); fd=d["decisions"]["final_decision"]; print("FINAL_OUTCOME", fd["final_outcome"]); print("FINAL_REASON", fd["final_reason_code"]); print("BRMS_GATES", d["decisions"].get("brms_flags", {}).get("gates"))' "$OUT_JSON"

echo "[OK] demo_wsl_complete"
