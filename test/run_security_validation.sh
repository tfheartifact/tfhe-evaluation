#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECURITY_SCRIPT="$ROOT/src/security/unix_parameter_security.py"

if command -v python3 >/dev/null 2>&1; then
  ESTIMATOR_RUNNER=(python3 -B)
elif command -v python >/dev/null 2>&1; then
  ESTIMATOR_RUNNER=(python -B)
else
  echo "Python runtime not found"
  exit 1
fi

"${ESTIMATOR_RUNNER[@]}" "$SECURITY_SCRIPT" validate-seta-unix \
  "$@"
