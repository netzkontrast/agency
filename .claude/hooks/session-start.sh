#!/bin/bash
set -euo pipefail

# Only run in remote (web) environments
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
