#!/usr/bin/env bash
# agency SessionStart hook — Spec 062.
#
# Idempotently ensure `agency-mcp` is on PATH so the .mcp.json shim
# (${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp, which routes to the pipx-
# installed console-script) can find the binary on first MCP boot.
#
# Without this hook, fresh marketplace installs (especially Claude
# Code Web environments) silently fail: the plugin appears installed
# but the MCP server never connects because nothing has run pipx yet.
#
# Idempotency: early-exit when agency-mcp is already on PATH so
# subsequent sessions don't reinstall. Editable mode means future
# marketplace updates flow through without a second pipx call.
set -e

if command -v agency-mcp >/dev/null 2>&1; then
  exit 0
fi

if command -v pipx >/dev/null 2>&1; then
  echo "agency: installing via pipx (one-time) — this may take ~5s" >&2
  pipx install --editable "${CLAUDE_PLUGIN_ROOT}" >&2
elif command -v pip >/dev/null 2>&1; then
  echo "agency: pipx not found; falling back to pip --user" >&2
  pip install --user --editable "${CLAUDE_PLUGIN_ROOT}" >&2
else
  echo "agency: neither pipx nor pip on PATH — install one and retry" >&2
  # Don't block session start; the MCP shim will exit 127 with its
  # own install hint on first call.
fi

exit 0
