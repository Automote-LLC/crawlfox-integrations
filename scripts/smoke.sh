#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/.venv"

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "==> JS SDK (crawlfox)"
cd "$ROOT/packages/js"
npm install --silent
npm test
npm run build

echo "==> Python SDK (crawlfox-py)"
"$PIP" install -e "$ROOT/packages/python[dev]" -q
cd "$ROOT/packages/python"
"$PY" -m pytest -q

echo "==> All smoke tests passed"
