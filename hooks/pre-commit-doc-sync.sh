#!/usr/bin/env bash
# hooks/pre-commit-doc-sync.sh — Spec 292 C5 (the "hook-later" trigger half).
#
# Round-trips every staged markdown file back into the graph before commit, so
# a human edit to a rendered Document is never lost (document.sync is idempotent:
# unchanged files are skipped, edited files append a DocRevision — keep-both).
#
# OPT-IN — wire it with:
#   ln -s ../../hooks/pre-commit-doc-sync.sh .git/hooks/pre-commit
# or call it from an existing pre-commit hook.
set -euo pipefail

# Only the staged markdown (Added/Copied/Modified) — never deleted paths.
mapfile -t MD < <(git diff --cached --name-only --diff-filter=ACM -- '*.md')
[[ ${#MD[@]} -eq 0 ]] && exit 0

command -v agency >/dev/null 2>&1 || { echo "agency CLI not on PATH; skipping doc-sync"; exit 0; }

for f in "${MD[@]}"; do
  [[ -f "$f" ]] || continue
  agency execute --code "
r = await call_tool('capability_document_sync', {'intent_id': (await call_tool('intent_bootstrap', {'purpose':'pre-commit doc-sync','deliverable':'round-trip staged .md','acceptance':'graph in sync'}))['intent_id'], 'agent_id':'agent:pre-commit', 'path':'$f'})
return r
" >/dev/null || echo "doc-sync: skipped $f"
  # Re-stage in case ingest stamped a fresh anchor into a new file.
  git add "$f"
done
exit 0
