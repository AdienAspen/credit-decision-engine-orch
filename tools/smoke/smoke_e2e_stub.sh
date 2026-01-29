#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# --- Python resolver (prefer project venv; allow override via env PY) ---
PY="${PY:-python3}"
VENV_PY="$ROOT/.venv/bin/python3"
if [[ "$PY" == "python3" && -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
fi


cd "$ROOT"

CLIENT_ID="${CLIENT_ID:-100001}"
SEED="${SEED:-42}"

# OFFLINE: no bridge, no curl, no ports, always stub + --no-brms
BRMS_STUB="${BRMS_STUB:-tools/smoke/fixtures/brms_all_pass.json}"

echo "[SMOKE_STUB] root=$ROOT"
echo "[SMOKE_STUB] python=$PY"
echo "[SMOKE_STUB] brms_stub=$BRMS_STUB"
test -f "$BRMS_STUB"

OUT_JSON="$(mktemp)"
echo "[SMOKE_STUB] running originate (offline)..."
"$PY" runners/originate.py \
  --client-id "$CLIENT_ID" \
  --seed "$SEED" \
  --brms-stub "$BRMS_STUB" \
  --no-brms \
  > "$OUT_JSON"

echo "[SMOKE_STUB] validate output..."
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); fd=d.get("decisions",{}).get("final_decision"); print("HAS_FINAL_DECISION", bool(fd)); print("FINAL_OUTCOME", fd.get("final_outcome") if fd else None); print("FINAL_REASON", fd.get("final_reason_code") if fd else None)' "$OUT_JSON"

rm -f "$OUT_JSON"
echo "[OK] smoke_e2e_stub_offline"
