#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$ROOT_DIR"

if ! "$PYTHON_BIN" -m ruff --version >/dev/null 2>&1; then
    echo "ERROR: Ruff is not available in this environment."
    exit 1
fi

if ! "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
    echo "==> Installing pytest"
    "$PYTHON_BIN" -m pip install \
        --root-user-action=ignore \
        "pytest>=8,<10"
fi

echo "==> Checking formatting"
"$PYTHON_BIN" -m ruff format --check .

echo "==> Running Ruff"
"$PYTHON_BIN" -m ruff check .

echo "==> Compiling integration, scripts and tests"
"$PYTHON_BIN" -m compileall -q custom_components tests

echo "==> Validating JSON files"
"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("hacs.json"),
    Path("custom_components/trovis557x/manifest.json"),
    Path("custom_components/trovis557x/strings.json"),
    *Path("custom_components/trovis557x/translations").glob("*.json"),
]

for path in paths:
    with path.open(encoding="utf-8") as file:
        json.load(file)
    print(f"OK: {path}")
PY

echo "==> Running repository tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON_BIN" -m pytest tests

echo "==> All local checks passed"
echo "==> Next: restart Home Assistant and perform the live integration test"