# `analyze.improve` vs. `analyze.cleanup`

Both produce an improvement-plan Reflection node. The difference is
SCOPE.

## `analyze.improve(analysis_id, axes=None, apply=False)`

Reads a prior `analyze.run` Analysis, clusters its findings, and drafts
a prioritised improvement plan. Operates over **any** axis (default:
all). Used when:

- "Here are the findings from this PR — give me a plan to address them."
- "Fix the security findings only" → `axes=['security']`.

The plan is a Reflection node with `kind=improvement-plan` and an
IMPROVES edge to the Analysis. v1 ships **planning-only**
(`apply=False` is the only supported value); the apply path is v2 and
runs under a `gate.check` per cluster.

## `analyze.cleanup(path, dry_run=True)`

Focused mode: runs `analyze.quality` and keeps ONLY the Q001 (unused-
import) findings. Used when:

- "Tidy up the obviously dead stuff in this file."
- "Pre-commit cleanup before the real review."

Doesn't read a prior Analysis — runs fresh against `path` because the
"obviously dead" category is small enough to be cheap. v1 ships
**dry_run=True only**; the apply path is v2.

## When to pick which

| Situation | Pick |
|---|---|
| You ran `analyze.run` and want a plan | `improve` |
| You want JUST the cleanup of the dead | `cleanup` |
| You want a plan for security findings only | `improve(axes=['security'])` |
| You don't yet have an Analysis | `cleanup` (it scans fresh) or `run` first then `improve` |

## Why not just one verb?

Three reasons:
1. **Token-economy.** `cleanup` returns ≤ 100 tokens (typically a
   handful of unused imports). `improve` may surface dozens of items
   across all axes. Two budgets, two return shapes.
2. **Discoverability.** A user knows what "cleanup" means without
   reading docs. `improve` is more general.
3. **Future-divergence.** v2 `cleanup` may auto-apply with a low-risk
   gate (single-file dead-code is very safe); v2 `improve` always
   needs a per-cluster review. Different gates per verb.

## The acceptance-gate discipline

Neither verb writes to disk in v1. The skill walker's phase 5
(`apply`) is the hard gate. When the apply path lands in v2:

```
[analyze.run] → [analyze.improve] → walker phase 5 (apply, hard) →
[gate.check per cluster] → orchestrator writes
```

The agency-native answer to SC's "STOP AFTER analysis" prompt-text
discipline — same goal (no surprise mutations), different mechanism
(hard-gate Lifecycle phase, not LLM-side prose).
