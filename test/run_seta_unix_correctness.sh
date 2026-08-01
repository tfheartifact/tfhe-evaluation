#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TFHE_RS_DIR="${TFHE_RS_DIR:-$ROOT/third-party/tfhe-rs}"

if ! command -v cargo >/dev/null 2>&1 && [[ -f "$HOME/.cargo/env" ]]; then
  # shellcheck disable=SC1090
  . "$HOME/.cargo/env"
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo not found in PATH"
  exit 1
fi

cd "$TFHE_RS_DIR"
cargo run --quiet -p tfhe --example unix_pbs_experiment --features shortint,software-prng -- \
  --suite seta-unix \
  "$@"
