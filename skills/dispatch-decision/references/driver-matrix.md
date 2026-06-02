# Driver matrix — when each of the 4 drivers wins

The decision is two-step: **(a) inline vs. dispatch**, then if dispatch,
**(b) which driver**. Each driver has a **distinct cost model**.

## The 4 drivers — cost models

| Driver | Local-budget cost | Remote/other cost | Cache model | When it wins |
|---|---|---|---|---|
| `inline` | full token cost (cached input @ 10%, fresh @ 100%) | — | shares parent cache — hot | high context_overlap OR high cache_warmth OR cheap task |
| `local` subagent | dispatch envelope + return summary | — | subagent starts cold | needs context isolation; parent shouldn't carry the load |
| `jules` | ~500 tokens envelope + ~500 tokens return summary | wall-clock minutes/hours + Jules billing | n/a (remote) | heavy compute that doesn't block local; auditable in PR; async tolerable |
| `mcp` (future, audit-F6) | varies by server | varies (some local, some remote) | varies | cross-MCP integration; depends on the specific server |

## Task-shape → driver (the matchup table)

| Task shape | Driver | Why |
|---|---|---|
| Read-only single-pass exploration of files already in context (S9 high) | `inline` | Cheap; subagent would re-load cold |
| Read-only single-pass exploration of files NOT in context | `local` subagent | Fresh context, no cache penalty either way |
| Multi-step implementation with mutation, interactive | `inline` | Mutations need provenance + the user is waiting |
| Multi-step implementation with mutation, async-OK + ≥ 45min | `jules` | Offloads heavy compute; PR is the deliverable |
| Large research with 3+ parallel branches | `local` subagents (fan-out) | Concurrent context isolation |
| Whole-repo briefing (`index_repo`) at cold-cache session start | `local` subagent | S1:tokens dominates; cache is cold anyway |
| Whole-repo briefing at end of a long session | `inline` | S10 fires — most of the repo is already in parent cache |
| Cross-MCP-server tool call (future) | `mcp` | When the HTTP-MCP-client driver ships (audit F6) |
| Single-file edit, known location | `inline` | No dispatch overhead earned |
| 30-minute pure-research task during user's coffee break | `jules` | S11=False; doesn't compete for the user's interactive budget |

## The selection rules (machine-checked in `dispatch_decision`)

```python
if not local_budget_relevant:
    driver = "jules"                       # caller opted out of local budget
elif parallelism >= 3:
    driver = "local"                       # fan-out, isolated contexts
elif est_duration_min >= 45 and not _interactive_required(driver_hint):
    driver = "jules"                       # heavy + async-OK → offload
elif driver_hint and not _conflicts_with(driver_hint, signals):
    driver = driver_hint                   # caller's tie-breaker wins
else:
    driver = "local"                       # default for dispatched read tasks
```

## When `driver_hint` is honoured vs. ignored

The hint is a **tie-breaker, not an override**. Specifically:

- `driver_hint="inline"` — REJECTED when any positive signal fired
  (`_conflicts_with` returns True). The signals already say dispatch.
- `driver_hint="local"` / `"jules"` / `"mcp"` — HONOURED when the
  decision is already to dispatch AND the hint doesn't conflict with
  a higher-priority rule (parallelism ≥ 3 picks local; ≥ 45min picks
  jules; both win over the hint).

When honoured, `signals_fired` records an `S8:driver_hint=<X>` entry
so the rationale carries the input.

## What about `mcp`?

The MCP-client driver doesn't ship today (audit F6 — separate spec
needed). v1 documents the slot. When the driver lands, the first
adoptee is the Superpowers `episodic-memory` MCP server — a
production-grade complement to `reflect.recall_semantic` (Spec 045),
searching the Claude Code transcript corpus.

Until then, `driver_hint="mcp"` resolves to `local` (the conflict
check rejects unknown drivers).
