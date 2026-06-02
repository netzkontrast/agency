---
spec_id: "040"
slug: subagent-decision-heuristics
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [011, 012]
affects:
  - agency/capabilities/delegate.py           # extend dispatch_decision transform + dispatch-decision skill
  - skills/dispatch-decision/                  # NEW skill folder (was a phase-walker on delegate cap only)
  - skills/dispatch-decision/SKILL.md
  - skills/dispatch-decision/references/heuristics.md          # the 11 signals + disqualifiers + algorithm
  - skills/dispatch-decision/references/driver-matrix.md       # 4 drivers × cost-model table
  - skills/dispatch-decision/references/anti-patterns.md       # 5 don'ts
  - skills/dispatch-decision/references/cache-and-budget-model.md  # S9 / S10 / S11 deep dive (context overlap, prompt cache, Jules's separate budget)
  - tests/test_dispatch_decision_extended.py
estimated_jules_sessions: 1
domain: meta
wave: 2
foundation_for: [041, 042, 043, 044]
---

# Spec 040 — Subagent-Decision Heuristics (Token-Aware Dispatch)

## Why

Agency already ships a `delegate.dispatch_decision` transform + a 4-phase
`dispatch-decision` Lifecycle skill (`agency/capabilities/delegate.py:42–93`).
The heuristic today fires on **four signals**: file count, exploration
required, parallelism, and wall-clock. That's a good start, but the new
capabilities planned in Specs 033–036 (`analyze`, `document`, `research`,
plus `reflect.recall`) will each ask the dispatch question **differently**:

- `analyze` runs four pure transforms — likely inline, but a big repo's
  `analyze_architecture` may want to fan-out by subdirectory.
- `document.index_repo` is the textbook subagent case (sc-index-repo's 94%
  token reduction is achieved BY dispatching).
- `research` ALWAYS fans out (lead + N specialists is the shape).
- `reflect.recall` is a graph traversal — never dispatch.

The current heuristic doesn't distinguish these. It also doesn't carry
**token-cost-of-return** (a subagent that returns 10K tokens of raw output
costs more than running inline at 3K), **read-only vs. mutation** (you
shouldn't dispatch mutations without provenance discipline), or
**driver-choice** (inline-claude vs. local subagent vs. Jules vs. future
MCP-client driver — F6 in the audit).

This spec extends the existing heuristic with four new dimensions, splits
the skill out of the capability file into its own folder (so it has
references/ for the depth, per the [`skill-creation`](../../skills/skill-creation/SKILL.md)
pattern), and adds the **return-token-budget** as the most important
single signal (per CLAUDE.md adaptive-disclosure doctrine).

## Done When

- [ ] `delegate.dispatch_decision` transform extended with seven new
  parameters:
  - `expected_return_tokens: int = 0` — estimate of the subagent's return
    payload in tokens. ≥ 5000 favours dispatch (context-protection).
  - `mutates: bool = False` — if True, the task writes graph nodes / disk /
    external state. Mutating tasks STAY inline unless they're an `effect`
    verb that already records `PRODUCES`d artefacts (read the verb's role
    tag if known).
  - `driver_hint: str = ""` — one of `"inline"`, `"local"`, `"jules"`,
    `"mcp"` (future) — caller's preference, treated as a tie-breaker not
    an override.
  - `read_only: bool = True` — orthogonal to `mutates` (e.g. a verb might
    write a `Reflection` but be conceptually read-only for the dispatcher).
  - `context_overlap: float = 0.0` — fraction of files/symbols the task
    needs that are ALREADY in the parent's context (0.0 = nothing loaded,
    1.0 = everything loaded). High overlap STRONGLY favours inline — the
    parent already paid for those tokens; a subagent re-loads them cold.
  - `cache_warmth: float = 0.0` — fraction of the parent's conversation
    prefix that is **prompt-cached** (system prompt + tool definitions +
    prior turns within the 5-minute cache TTL). High warmth favours
    inline because every cached input token costs ~10% of a fresh token
    (Anthropic prompt cache pricing). Dispatch resets the subagent's
    cache to cold.
  - `local_budget_relevant: bool = True` — does this dispatch consume
    the **local interactive agent's token budget**? Defaults True.
    Setting False signals a driver that runs OUTSIDE the local budget
    (Jules — see §"The Jules cost-model footnote", below). When False,
    the heuristic relaxes ALL token-cost disqualifiers — cost is wall-
    clock and Jules's billing, not parent-context tokens.
- [ ] The decision rule becomes the **lexicographic AND** of the existing
  four + the new seven. Specifically: dispatch wins when ANY of the
  positive signals AND none of the disqualifiers (mutates AND not effect-
  with-provenance; high context_overlap with low return_tokens; high
  cache_warmth with cheap inline path; driver_hint=="inline" with no
  overriding signal). **Exception**: when `local_budget_relevant=False`
  (Jules driver), the disqualifiers `context_overlap` and `cache_warmth`
  do NOT fire — those penalise local-budget consumption, which Jules
  doesn't touch.
- [ ] Decision payload returns `{"recommendation": "inline"|"dispatch",
  "driver": "inline"|"local"|"jules"|"mcp", "rationale": str,
  "token_cost_estimate": int, "local_budget_token_estimate": int,
  "signals_fired": [...]}`. `token_cost_estimate` is the total work cost
  (whoever pays); `local_budget_token_estimate` is what comes out of
  the LOCAL parent context's budget (0 for Jules). The split lets the
  caller reason about the two budgets independently.
- [ ] The `dispatch-decision` Lifecycle skill (on `delegate.ontology.skills`)
  acquires a fifth phase **before** the existing four:
  `0. estimate-tokens-and-cache` (outputs `expected_return_tokens` +
  `mutates` + `read_only` + `context_overlap` + `cache_warmth` +
  `local_budget_relevant`). The remaining phases re-index.
- [ ] A `skills/dispatch-decision/` folder is created with a SKILL.md plus
  four `references/` files (heuristics, driver-matrix, anti-patterns,
  **cache-and-budget-model** — the new one explaining context-overlap,
  prompt-caching, and Jules's separate budget). The skill replaces the
  in-engine `_DISPATCH_DECISION_SKILL` dict on `delegate.py` — the dict
  stays as the Lifecycle template, but the SKILL.md (the human-readable
  discipline) lives in `skills/`.
- [ ] `tests/test_dispatch_decision_extended.py` covers the **eleven**
  signals separately (one test per signal proving it can swing the
  decision) and **five** end-to-end scenarios: inline-text-task,
  fan-out-research, single-big-analysis, **cache-warm-inline-wins** (S10
  beats S2), **jules-outside-budget-wins** (S11=False relaxes S1+S9+S10
  so a heavy-token task dispatches to Jules where it wouldn't have
  dispatched to local).
- [ ] CLAUDE.md Rule #3 updated to reference both the skill folder and the
  extended signal set (eleven signals, two budget models).

## Design

### The eleven signals

| # | Signal | Type | Dispatch when | Inline when |
|---|---|---|---|---|
| **S1** | `expected_return_tokens` (NEW) | int | ≥ 5000 | < 5000 |
| **S2** | `file_count` | int | ≥ 4 unfamiliar | ≤ 3 known |
| **S3** | `exploration_needed` | bool | True (repeated grep/find) | False |
| **S4** | `parallelism` | int | ≥ 3 sibling tasks | 1–2 |
| **S5** | `est_duration_min` | int | ≥ 15 wall-clock | < 15 |
| **S6** | `mutates` (NEW) | bool | False (read-only is safe to dispatch) | True (mutations stay inline) |
| **S7** | `read_only` (NEW) | bool | True | False |
| **S8** | `driver_hint` (NEW) | str | matches a strong signal | conflicts with signals |
| **S9** | `context_overlap` (NEW) | float | ≤ 0.3 (parent has little of it) | ≥ 0.7 (parent already loaded most) |
| **S10** | `cache_warmth` (NEW) | float | ≤ 0.3 (parent cache cold anyway) | ≥ 0.6 (parent cache is hot) |
| **S11** | `local_budget_relevant` (NEW) | bool | True+positive signals | False (Jules) relaxes S1/S9/S10 disqualifiers |

**The disqualifier rule.** `mutates=True` AND the verb is NOT an `effect`
verb that records `PRODUCES`d artefacts → ALWAYS inline. Mutations without
provenance are how systems silently lose work; we don't dispatch them.

**The token-cost signal.** S1 is the most important addition. A subagent
that returns < 5000 tokens to the main context is a context-tax (you pay
the dispatch overhead AND inflate the parent context). Above 5000 tokens
of return, the dispatch starts amortising because the parent never sees
the raw output (the agent compresses to a summary). This is the 1:1
generalisation of `sc-index-repo`'s 94% reduction — the savings come from
NOT loading the raw scan into the parent context.

**The context-overlap signal (S9).** If the parent context already holds
the files/symbols the task needs (e.g. you just `Read` three files and
the task processes those same three files), dispatching means **the
subagent re-reads them cold**. You pay twice — once to load originally,
once for the subagent to load fresh, plus the dispatch overhead and the
return-summary tokens. High overlap (`≥ 0.7`) is a strong inline signal
that BEATS even S2 (file_count) and S5 (duration) — the parent already
absorbed the load cost; finishing the work inline is cheap. Low overlap
(`≤ 0.3`) is neutral or positive for dispatch.

**The prompt-cache signal (S10).** Anthropic's prompt-cache makes
**cached input tokens cost ~10% of fresh tokens** within the 5-minute
TTL. Continuing inline after a long-running session means most of the
prefix is hot — system prompt, tool definitions, prior turns, prior
file reads — all amortised. A subagent's prompt starts cold: no cache
hit on its first turn (or hits only the system-prompt portion). When
the parent cache is hot (`≥ 0.6` cache_warmth) AND the inline work is
not heavy, **inline wins even against signals that would otherwise
favour dispatch**. When cache is cold anyway (fresh session, just-
compacted history), this signal goes silent — dispatch overhead is
no longer worse than inline overhead.

**The Jules cost-model footnote (S11).** Jules sessions run on a
**separate budget axis** — they don't consume the local interactive
agent's per-turn token budget. The "cost" of dispatching to Jules is:
- wall-clock latency (minutes to hours, async),
- Jules's own billing (independent of the local API key),
- a small token cost in the parent for the dispatch envelope + the
  returned PR/diff summary.

So when `local_budget_relevant=False` (the caller signals "I'm okay with
async + Jules's bill"), the S1/S9/S10 disqualifiers — which all penalise
*local* budget consumption — go silent. A task that would be too cheap
to dispatch locally (S1 fails, S9 fires) can still be a great Jules
candidate if it's heavy compute that the local agent shouldn't block on.
**Inverted rule for Jules**: dispatch wins when wall-clock budget allows
async (≥ 30 min slack) AND the task is read-mostly + auditable in a PR.

### Driver-choice matrix

The decision is two-step: **(a) inline vs. dispatch**, then if dispatch,
**(b) which driver**. Each driver has a **distinct cost model**:

| Driver | Local-budget cost | Remote/other cost | Cache model | When it wins |
|---|---|---|---|---|
| `inline` | full token cost (cached input @ 10%, fresh @ 100%) | — | shares parent cache — hot | high context_overlap OR high cache_warmth OR cheap task |
| `local` subagent | dispatch envelope + return summary | — | subagent starts cold | needs context isolation; parent shouldn't carry the load |
| `jules` | ~500 tokens envelope + ~500 tokens return summary | wall-clock minutes/hours + Jules billing | n/a (remote) | heavy compute that doesn't block local; auditable in PR; async tolerable |
| `mcp` (future) | varies by server | varies (some local, some remote) | varies | cross-MCP integration; depends on the specific server |

| Task shape | Driver | Why |
|---|---|---|
| Read-only single-pass exploration of files already in context (S9 high) | `inline` | Cheap; subagent would re-load cold |
| Read-only single-pass exploration of files NOT in context | `local` subagent | Fresh context, no cache penalty either way |
| Multi-step implementation with mutation, interactive | `inline` | Mutations need provenance + the user is waiting |
| Multi-step implementation with mutation, async-OK + ≥ 45min | `jules` | Offloads heavy compute; PR is the deliverable |
| Large research with 3+ parallel branches | `local` subagents (fan-out) | Concurrent context isolation |
| Whole-repo briefing (index_repo) at cold-cache session start | `local` subagent | Spec 040 S1:tokens dominates; cache is cold anyway |
| Whole-repo briefing at end of a long session | `inline` | S10 fires — most of the repo is already in parent cache |
| Cross-MCP-server tool call (future) | `mcp` | When the HTTP-MCP-client driver ships (audit F6) |
| Single-file edit, known location | `inline` | No dispatch overhead earned |
| 30-minute pure-research task during user's coffee break | `jules` | S11=False; doesn't compete for the user's interactive budget |

### Anti-patterns (when NOT to dispatch even if signals say yes)

| Anti-pattern | Why |
|---|---|
| **Known-path lookup** | If you can name the file and the symbol, just `Read` it. Subagents have setup cost. |
| **One-shot mutation** | A single file edit is cheaper inline than dispatch-and-review. |
| **Loop body** | Dispatching INSIDE a loop is N× overhead. Hoist the dispatch out. |
| **Recursive dispatch** | Subagent dispatching another subagent — Loop-Detection-Middleware (planned in EXTENSION-PLAN.md) will guard this; manually: don't. |
| **Tasks the user asked for an answer to** | The user is waiting on the parent context. Don't punt them to a subagent's queue. |

### Decision algorithm (pseudocode)

```python
def dispatch_decision(
    # work-shape signals
    s1_tokens=0, s2_files=0, s3_explore=False, s4_parallel=1, s5_dur_min=0,
    # role/safety signals
    s6_mutates=False, s7_read_only=True, s8_driver_hint="",
    # cost-model signals (NEW — Spec 040 §"eleven signals")
    s9_context_overlap=0.0, s10_cache_warmth=0.0, s11_local_budget_relevant=True,
):
    signals = []

    # Disqualifier 1: mutating + not-effect-with-provenance → inline
    if s6_mutates and not _is_effect_with_provenance(s8_driver_hint):
        return _inline(reason="mutating task without effect-provenance",
                       fired=["S6:mutates"])

    # Disqualifier 2 (NEW): high context_overlap + parent has cache → inline
    # Only fires when the LOCAL budget matters (Jules side-steps this).
    if s11_local_budget_relevant:
        if s9_context_overlap >= 0.7 and s1_tokens < 5000:
            return _inline(reason="parent already holds the context",
                           fired=["S9:overlap-high"])
        if s10_cache_warmth >= 0.6 and s5_dur_min < 30:
            return _inline(reason="parent cache hot; inline tokens are 10% cost",
                           fired=["S10:cache-hot"])

    # Positive signals
    if s1_tokens >= 5000 and s11_local_budget_relevant: signals.append("S1:tokens")
    if s2_files >= 4 and s9_context_overlap < 0.5:      signals.append("S2:files")
    if s3_explore:                                       signals.append("S3:explore")
    if s4_parallel >= 3:                                 signals.append("S4:parallel")
    if s5_dur_min >= 15:                                 signals.append("S5:duration")
    if s7_read_only and signals:                         signals.append("S7:read_only_amplifies")
    # Jules-specific positive: heavy task that doesn't touch local budget
    if not s11_local_budget_relevant and (s1_tokens >= 2000 or s5_dur_min >= 30):
        signals.append("S11:jules-budget-free")

    if not signals:
        return _inline(reason="no positive signals", fired=[])

    # Driver selection (cost-model aware)
    if not s11_local_budget_relevant:
        driver = "jules"               # caller already opted out of local budget
    elif s4_parallel >= 3:
        driver = "local"               # fan-out, isolated contexts
    elif s5_dur_min >= 45 and not _interactive_required():
        driver = "jules"               # heavy + async-OK → offload
    elif s8_driver_hint and not _conflicts_with(s8_driver_hint, signals):
        driver = s8_driver_hint
    else:
        driver = "local"

    # Estimate the two budgets separately
    local_cost = 0 if driver == "jules" else _estimate_local_tokens(
        s1_tokens, s9_context_overlap, s10_cache_warmth, driver)
    total_cost = _estimate_total_work_tokens(s1_tokens, s5_dur_min, driver)

    return {
        "recommendation": "dispatch", "driver": driver,
        "token_cost_estimate": total_cost,
        "local_budget_token_estimate": local_cost,
        "rationale": _compose(signals, driver),
        "signals_fired": signals,
    }
```

**Estimator helpers** (`_estimate_local_tokens`, `_estimate_total_work_tokens`)
are deterministic: cached input @ 10% of fresh, dispatch envelope at ~700
tokens per local subagent (Open Question 1 measurement), Jules envelope
at ~500 tokens.

### Skill folder layout (after split)

```
skills/dispatch-decision/
├── SKILL.md                       # the discipline; ~120 LOC; "Use when…" trigger
└── references/
    ├── heuristics.md              # the 8 signals, the disqualifier, the algorithm
    ├── driver-matrix.md           # the 4 drivers, when each wins
    └── anti-patterns.md           # 5 don'ts (above)
```

The Lifecycle template stays on `delegate.ontology.skills["dispatch-decision"]`
(5 phases: `estimate-tokens` → `estimate-shape` → `apply-heuristic` →
`assemble-bash-hints` → `decide(hard)`). Skill-walker disclosure and the
`SKILL.md` cross-reference each other.

### Integration with the planned capabilities (032 informs 033–036)

Each of the next four specs will, in its skill walker, **call
`dispatch_decision` at the appropriate phase**, now with the cache-aware
signals:

- **Spec 042 `analyze.run`** — phase 2 dispatches `analyze_architecture`
  for repos with >10 packages (S2:files + S1:tokens fire) BUT inlines
  when the architecture files are already in context (S9 high).
- **Spec 043 `document.index_repo`** — dispatches at cold-cache session
  start (S1:tokens dominates), inlines at end of long session (S10 fires
  — most of the repo is cached anyway).
- **Spec 044 `research.lead_research`** — fans out specialists
  (S4:parallel ≥3 + S7:read_only). For "do this research while I make
  coffee" pattern, sets `local_budget_relevant=False` → Jules driver,
  freeing the local context entirely.
- **Spec 045 `reflect.recall_semantic`** — NEVER dispatches (pure graph
  read, return is small, S1:tokens fails; S9 typically high — caller
  already in the project context).

The benefit of doing 032 first: each downstream spec's walker can just
write `phase "dispatch-or-inline" with gate dispatch_decision(...)` and
trust the heuristic — including the cache and budget-model signals.

## Files

- **Modify:**
  - `agency/capabilities/delegate.py` — extend `dispatch_decision`
    signature + body; refactor `_DISPATCH_DECISION_SKILL` to 5 phases.
  - `CLAUDE.md` Rule #3 — reference the skill folder + 8 signals.
- **Add:**
  - `skills/dispatch-decision/SKILL.md`
  - `skills/dispatch-decision/references/heuristics.md`
  - `skills/dispatch-decision/references/driver-matrix.md`
  - `skills/dispatch-decision/references/anti-patterns.md`
  - `tests/test_dispatch_decision_extended.py`

## Open Questions

1. **What's the actual token-cost of one local-subagent dispatch?** The
   heuristic constant (~700 tokens preamble + return-summary budget) is
   an estimate. Worth measuring once and pinning. The Jules envelope
   (~500 tokens) deserves the same treatment.
2. **Should S1 (return-tokens) have a per-driver cutoff?** Maybe inline
   tolerates 8K return (just costs tokens), but Jules's wake-up makes the
   cutoff different. v1 says one cutoff (5000); refine later.
3. **MCP-client driver (`s8_driver_hint="mcp"`)** is named here but
   doesn't exist yet (audit-finding F6, separate spec). Document the
   placeholder; don't ship the driver in this spec. **First concrete
   adoptee when the driver ships:** the Superpowers `episodic-memory`
   MCP server (TypeScript, exposes `search` + `read` over Claude Code
   transcript corpus). It IS the production-grade complement to
   `reflect.recall_semantic` (Spec 045) — same shape (semantic search),
   different corpus (CC transcripts vs. agency Reflections). Adopting
   it via the driver is the lean call; reimplementing it isn't.
4. **Should the heuristic auto-fire from inside `delegate.dispatch`?**
   Today the orchestrator calls `dispatch_decision` then `dispatch`. We
   could fold the gate in. v1 keeps them separate — explicit > clever.
5. **How does the orchestrator MEASURE `context_overlap` (S9)?** Two
   approaches:
   (a) Caller-provided: the orchestrator estimates "I just Read these 3
   files; the task needs 2 of those 3 → overlap=0.67". Lean: this; the
   caller has the visibility.
   (b) Engine-inferred: parse the agent's recent tool calls for `Read`/
   `Grep`/`Bash` outputs and compute a deterministic overlap. Heavier;
   defer to v2.
6. **How does the orchestrator MEASURE `cache_warmth` (S10)?** The
   Anthropic API exposes cache hit/miss statistics in the response
   `usage.cache_read_input_tokens` / `usage.cache_creation_input_tokens`.
   Track the last-turn ratio: `warmth = cache_read / (cache_read +
   fresh_input)`. v1: caller-provided estimate (rough is fine); v2:
   engine reads from the API usage block automatically. The 5-minute
   TTL means cache_warmth decays — for sessions paused >5 min, treat
   as cold.
7. **Anthropic prompt-cache pricing assumption.** This spec assumes
   cached input = 10% of fresh input (Claude 4.x family default).
   Different cache TTL tiers (5-min vs 1-hour at 25% premium) change
   the math. v1 uses 5-min/10% as canonical; v2 may accept a
   `cache_tier` param.
8. **What is "local_budget" precisely?** Is it the user's per-turn
   token budget visible in the Claude Code UI, the API spend in $, or
   the conversation's context-window utilisation? All three matter;
   `local_budget_relevant=False` for Jules means **none** of them are
   touched (Jules has its own API key + context). The skill doc must be
   precise here.
9. **Hybrid drivers** (Jules dispatching a local subagent for a sub-
   task, etc.) are out of scope. v1 sees Jules as a single opaque
   driver; what happens INSIDE Jules is Jules's concern.

## Evidence

- Existing implementation: `agency/capabilities/delegate.py:42–93` (the
  `_DISPATCH_DECISION_SKILL` template + the `dispatch_decision` verb).
- Token-economics doctrine: CLAUDE.md Rule #3 "Decide before dispatching";
  AGENCY_PROTOCOL.md (Jules-specific behaviour); Spec 023 adaptive-disclosure.
- Cluster-analysis input: PR #17 thread, the three subagent reports
  (SC commands, Superpowers skills, related plugins). Specifically:
  - sc-select-tool's complexity-scoring approach (decision <100ms, >95% accuracy).
  - sc-index-repo's 94% reduction by dispatching the index.
  - superpowers:dispatching-parallel-agents (S4:parallel + isolation).
- Audit finding F6 (HTTP-MCP-client driver) — the future `mcp` driver slot.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted; the current dispatch heuristic
ships the four-signal version.

### Done
- The 4-signal heuristic + 4-phase Lifecycle skill ship today
  (`agency/capabilities/delegate.py`, since `delegate` cap landed).

### Still to implement
- All eight signal extensions.
- The `skills/dispatch-decision/` folder + 3 references.
- The 5th `estimate-tokens` phase in the Lifecycle template.
- Tests covering signal independence + 3 end-to-end scenarios.
- CLAUDE.md doctrine update.

### Refinement needed
- Open Question 1 (Jules dispatch cost measurement) is a one-hour timing
  experiment; do it before pinning the rationale.
- Open Question 3 (mcp driver) defers to the future HTTP-MCP-client spec.
