#!/bin/bash
# .claude/hooks/session-start.sh — install the dev environment for
# Claude Code on the web so tests and linters work out of the box.
#
# Mirrors `scripts/setup`: creates the .venv (if missing) and installs
# agency with every lightweight runtime extra + dev tools (.[dev]), so
# the full suite runs with zero silently-skipped capability tests.
#
# Remote-only (web sessions); idempotent; non-interactive. Persists the
# venv on PATH (+ PYTHONPATH) via $CLAUDE_ENV_FILE so every later command
# in the session resolves the venv's Python and its site-packages.
set -euo pipefail

# Only run in Claude Code on the web; local sessions manage their own venv.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

if [[ ! -d .venv ]]; then
  echo "==> creating .venv"
  python3 -m venv .venv
fi

. .venv/bin/activate

echo "==> pip install -e '[dev]'"
python -m pip install --quiet --upgrade pip
python -m pip install -q -e ".[dev]"

echo "==> scaffold .agency/config.yaml"
python -c "from agency import _config; print('  ' + _config.config_scaffold())" || true

echo "Done."
