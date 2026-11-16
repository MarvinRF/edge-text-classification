#!/usr/bin/env bash
# Local gate: the same steps as CI (.github/workflows/ci.yml), in the same order.
# Exits 1 if any step fails.
set -u
cd "$(dirname "$0")/.." || exit 1
UV=$(command -v uv) || { echo "uv not found: https://docs.astral.sh/uv/"; exit 1; }
rc=0
step() {
  local name=$1 out; shift
  if out=$("$@" 2>&1); then
    echo "$name: ok"
  else
    echo "$name: FAILED"; printf '%s\n' "$out" | tail -20; rc=1
  fi
}
step "dependencies" "$UV" sync --locked
step "lint" "$UV" run ruff check
step "format" "$UV" run ruff format --check
step "types" "$UV" run pyright
step "tests" "$UV" run pytest
exit $rc
