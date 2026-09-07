#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${OPENREEF_APP_ROOT:-/Users/rof011/openreef}"
LEGACY_RUNTIME="/Users/rof011/.codex/.chatgpt-projects/g-p-6a8dd74eb34481919430c60f20d420b8/openreef/.venv"
OPENMVS_BIN="/Users/rof011/vcpkg/installed/arm64-osx/tools/openmvs"

if [[ -x "$APP_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$APP_ROOT/.venv/bin/python"
elif [[ -x "$LEGACY_RUNTIME/bin/python" ]]; then
  PYTHON_BIN="$LEGACY_RUNTIME/bin/python"
else
  echo "ERROR: OpenReef Python environment not found." >&2
  exit 1
fi

export PATH="/opt/homebrew/bin:$OPENMVS_BIN:$PATH"
export PYTHONPATH="$APP_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" -m openreef.pipeline.cli "$@"
