#!/usr/bin/env bash
set -uo pipefail

# Run a command and ALWAYS persist stdout/stderr + exit code to disk.
# Never exits non-zero (prevents VSCode terminal from dying with exit code 1).

NAME="${1:-unnamed}"
shift || true

TS="$(date +%Y%m%d_%H%M%S)"
LOG="tools/smoke/_logs/${TS}__${NAME}.log"
RCF="tools/smoke/_logs/${TS}__${NAME}.rc"

{
  echo "[RUN] name=${NAME}"
  echo "[RUN] ts=${TS}"
  echo "[RUN] pwd=$(pwd)"
  echo "[RUN] python=$(command -v python3)"
  echo "[RUN] cmd=$*"
  echo "------------------------------------------------------------"
  "$@"
} >"$LOG" 2>&1
RC=$?
echo "$RC" >"$RCF"

echo "[DONE] rc=${RC}"
echo "[DONE] log=${LOG}"
echo "[DONE] rc_file=${RCF}"
echo "[TAIL] last 80 lines:"
tail -n 80 "$LOG" || true

# Always succeed so VSCode terminal does not terminate.
exit 0
