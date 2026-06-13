#!/usr/bin/env bash
# Review-Partner commit watch (Spec 286 / PR #141).
#
# Emits one line per NEW commit pushed to the refactor branch so the
# review-partner session wakes to review it (see Review.md). Run under the
# Monitor tool (persistent) — stdout is the event stream; each NEW COMMIT
# line becomes a notification. Polls every 90s; tolerant of transient
# fetch failures so one bad request never kills the watch.
set -u
BR="${1:-claude/agency-error-enum-fixes-13tpnf}"
cd "$(dirname "$0")/.." || exit 1

git fetch origin "$BR" -q 2>/dev/null || true
prev="$(git rev-parse "origin/$BR" 2>/dev/null || echo none)"

while true; do
  git fetch origin "$BR" -q 2>/dev/null || true
  cur="$(git rev-parse "origin/$BR" 2>/dev/null || echo none)"
  if [ "$cur" != "$prev" ] && [ "$cur" != none ]; then
    git log --pretty='NEW COMMIT %h | %an | %s' "${prev}..${cur}" 2>/dev/null \
      || echo "NEW COMMIT ${cur} (range unavailable — review HEAD)"
    prev="$cur"
  fi
  sleep 90
done
