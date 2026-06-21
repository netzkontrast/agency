#!/bin/bash
# Spec 336 — agency tool-call capture (PreToolUse / PostToolUse).
#
# Routes each tool event to `agency hook`, which records it into the engine's
# EPHEMERAL tool-call store (.agency/toolcalls.db) plus the BoundaryUse shadow
# for raw mutating tools — so raw-tool work (Bash/Edit/Read/git) becomes
# provenance-visible instead of invisible to analyze.graph.
#
# Best-effort and NON-blocking: always exits 0, so a capture hiccup can never
# block or fail a tool call. Output is dropped (capture is server-side; the
# engine's stdout/stderr here is advisory-only).
#
# Why a bespoke hook rather than the plugin's hooks/dispatch: the plugin script
# guards on `command -v agency`, but the remote/web harness does not put the
# `agency` CLI on PATH (no venv activation for hooks), so it silently no-ops.
# This bridge invokes the project venv's Python directly.
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT" 2>/dev/null || exit 0

PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 2>/dev/null || true)"
[ -n "$PY" ] || exit 0

# stdin carries the Claude Code event JSON; `agency hook` reads it and records.
cat | "$PY" -m agency.cli hook >/dev/null 2>&1 || true
exit 0
