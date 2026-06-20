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

cd "${CLAUDE_PROJECT_DIR:-/home/user/agency}"

# Create the venv once; re-running just re-resolves the install.
if [ ! -d .venv ]; then
  echo "==> creating .venv"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

echo '==> pip install -e ".[dev]"'
python -m pip install --quiet --upgrade pip
python -m pip install -e ".[dev]"

# Persist the venv for the rest of the session: PATH so `python`/`pytest`/
# `ruff`/`agency` resolve from .venv, PYTHONPATH so `agency` imports resolve.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"${CLAUDE_PROJECT_DIR:-/home/user/agency}/.venv/bin:\$PATH\""
    echo "export VIRTUAL_ENV=\"${CLAUDE_PROJECT_DIR:-/home/user/agency}/.venv\""
  } >> "$CLAUDE_ENV_FILE"
fi

echo "==> dev environment ready"
