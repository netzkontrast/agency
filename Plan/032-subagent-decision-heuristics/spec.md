---
spec_id: "032"
slug: subagent-decision-heuristics
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [011, 012]
affects:
  - agency/capabilities/delegate.py           # extend dispatch_decision transform + dispatch-decision skill
  - skills/dispatch-decision/                  # NEW skill folder (was a phase-walker on delegate cap only)
  - skills/dispatch-decision/SKILL.md
  - skills/dispatch-decision/references/heuristics.md
  - skills/dispatch-decision/references/driver-matrix.md
  - skills/dispatch-decision/references/anti-patterns.md
  - tests/test_dispatch_decision_extended.py
estimated_jules_sessions: 1
domain: meta
wave: 2
foundation_for: [033, 034, 035, 036]
---

# Spec 032 — Subagent-Decision Heuristics (Token-Aware Dispatch)

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

- [ ] `delegate.dispatch_decision` transform extended with four new
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
- [ ] The decision rule becomes the **lexicographic AND** of the existing
  four + the new four. Specifically: dispatch wins when ANY of the
  positive signals AND none of the disqualifiers (mutates AND not effect-
  with-provenance; driver_hint=="inline" with no overriding signal).
- [ ] Decision payload returns `{"recommendation": "inline"|"dispatch",
  "driver": "inline"|"local"|"jules"|"mcp", "rationale": str,
  "token_cost_estimate": int, "signals_fired": [...]}`. The `signals_fired`
  list names every rule that voted, so the rationale is machine-checkable.
- [ ] The `dispatch-decision` Lifecycle skill (on `delegate.ontology.skills`)
  acquires a fifth phase **before** the existing four:
  `0. estimate-tokens` (outputs `expected_return_tokens` + `mutates` +
  `read_only`). The remaining phases re-index.
- [ ] A `skills/dispatch-decision/` folder is created with a SKILL.md plus
  three `references/` files (heuristics, driver-matrix, anti-patterns).
  The skill replaces the in-engine `_DISPATCH_DECISION_SKILL` dict on
  `delegate.py` — the dict stays as the Lifecycle template, but the
  SKILL.md (the human-readable discipline) lives in `skills/`.
- [ ] `tests/test_dispatch_decision_extended.py` covers the eight signals
  separately (one test per signal proving it can swing the decision) and
  three end-to-end scenarios (inline-text-task, fan-out-research, single-
  big-analysis).
- [ ] CLAUDE.md Rule #3 updated to reference both the skill folder and the
  extended signal set.

## Design

### The eight signals

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

### Driver-choice matrix

The decision is two-step: **(a) inline vs. dispatch**, then if dispatch,
**(b) which driver**.

| Task shape | Driver | Why |
|---|---|---|
| Read-only single-pass exploration | `local` subagent | Fast, fresh context, no Jules wake-up cost |
| Multi-step implementation with mutation | `inline` OR `jules` (≥45min wall-clock) | Inline if interactive; Jules if asynchronous |
| Large research with 3+ parallel branches | `local` subagents (fan-out) | Concurrent context isolation |
| Cross-MCP-server tool call (future) | `mcp` | When Spec 032b ships (HTTP MCP-client) |
| Single-file edit, known location | `inline` | No dispatch overhead earned |
| Whole-repo briefing (index_repo) | `local` subagent | Textbook S1 case |

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
def dispatch_decision(s1_tokens=0, s2_files=0, s3_explore=False,
                      s4_parallel=1, s5_dur_min=0, s6_mutates=False,
                      s7_read_only=True, s8_driver_hint=""):
    signals = []
    # disqualifier: mutating + not-effect-with-provenance → inline
    if s6_mutates and not _is_effect_with_provenance(s8_driver_hint):
        return {"recommendation": "inline", "driver": "inline",
                "rationale": "mutating task without effect-provenance",
                "signals_fired": ["S6:mutates"]}

    if s1_tokens >= 5000: signals.append("S1:tokens")
    if s2_files >= 4:     signals.append("S2:files")
    if s3_explore:        signals.append("S3:explore")
    if s4_parallel >= 3:  signals.append("S4:parallel")
    if s5_dur_min >= 15:  signals.append("S5:duration")
    if s7_read_only and signals:
        signals.append("S7:read_only_amplifies")

    if not signals:
        return {"recommendation": "inline", ...}

    # driver selection
    if s4_parallel >= 3:
        driver = "local"   # fan-out
    elif s5_dur_min >= 45 and not _interactive_required():
        driver = "jules"
    elif s8_driver_hint and not _conflicts_with(s8_driver_hint, signals):
        driver = s8_driver_hint
    else:
        driver = "local"
    return {"recommendation": "dispatch", "driver": driver,
            "rationale": _compose(signals, driver), "signals_fired": signals}
```

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
`dispatch_decision` at the appropriate phase**:

- **Spec 034 `analyze.run`** — phase 2 dispatches `analyze_architecture` for
  repos with >10 packages (S2:files signal + S1:tokens signal).
- **Spec 035 `document.index_repo`** — ALWAYS dispatches (S1:tokens dominates).
- **Spec 036 `research.lead_research`** — fans out specialists (S4:parallel
  ≥3 + S7:read_only).
- **Spec 037 `reflect.recall_semantic`** — NEVER dispatches (pure graph
  read, return is small, S1:tokens fails).

The benefit of doing 032 first: each downstream spec's walker can just
write `phase "dispatch-or-inline" with gate dispatch_decision(...)` and
trust the heuristic.

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

1. **What's the actual token-cost of one Jules dispatch?** The heuristic
   constant (700 tokens preamble + review-cycle wake budget) is an
   estimate. Worth measuring once and pinning in the rationale.
2. **Should S1 (return-tokens) have a per-driver cutoff?** Maybe inline
   tolerates 8K return (just costs tokens), but Jules's wake-up makes the
   cutoff different. v1 says one cutoff (5000); refine later.
3. **MCP-client driver (`s8_driver_hint="mcp"`)** is named here but
   doesn't exist yet (audit-finding F6, separate spec). Document the
   placeholder; don't ship the driver in this spec.
4. **Should the heuristic auto-fire from inside `delegate.dispatch`?**
   Today the orchestrator calls `dispatch_decision` then `dispatch`. We
   could fold the gate in. v1 keeps them separate — explicit > clever.

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
