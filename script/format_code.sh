#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$ROOT_DIR"

if ! "$PYTHON_BIN" -m ruff --version >/dev/null 2>&1; then
    echo "==> Installing Ruff"
    "$PYTHON_BIN" -m pip install \
        --root-user-action=ignore \
        "ruff>=0.15,<0.16"
fi

echo "==> Applying safe Ruff fixes"
"$PYTHON_BIN" -m ruff check --fix .

echo "==> Formatting files"
"$PYTHON_BIN" -m ruff format .

echo "==> Verifying Ruff checks"
"$PYTHON_BIN" -m ruff check .

echo "==> Formatting completed"
