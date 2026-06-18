---
spec_id: "318"
slug: scope-boundary-elicitation
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["307", "308", "310", "312"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 318 — Scope-boundary elicitation (`discover.scope`)

> Child of the intent-pillar deep program (Spec 307), **"structure" layer**. It
> elicits IN-/OUT-of-scope boundaries through the AskUser primitive
> (`discover.ask`, Spec 310), recording each as a `ScopeBoundary` node
> `BOUNDS`-edged to the Intent. The out-of-scope set sharpens the deliverable and
> guards against scope creep — and out-of-scope items can seed deferred
> sub-intents (Spec 319).

## Why (evidence + doctrine)

Spec 307 §"Why" lists *"no scope elicitation"* among the gaps that leave an Intent
shallow, and the `ambiguity_kind` enum (Spec 307 ontology) names `vague-scope` as
a first-class ambiguity. A deliverable without a boundary is unbounded: every
session against it risks creep, because "what we are NOT doing" was never written
down. The out-of-scope set is **as load-bearing as the in-scope set** — it is the
explicit fence that lets a session say "that's a different intent" instead of
silently absorbing the work.

The substrate already owns the elicitation engine. Spec 310 ships `discover.ask`
— the well-formed-question primitive (2–4 options, recommended-first, multiSelect
where axes are independent) built on the `AskUserQuestion` harness tool. Spec 307
§"thesis" frames AskUser as the ambiguity-resolution engine: a sharp question
(options *derived* from evidence, never invented — the derivability audit) folded
back into the Intent. The coverage matrix binds the AskUser chain to this child:
*"`scope` composes the AskUser primitive."* Scope elicitation is an interactive
boundary-drawing: for each candidate boundary, ask the user in or out, and record
the answer as provenance (Goal 2). The user stays the decider; the engine captures
every decision as a graph edge.

Doctrine guardrails: `scope` is `role="act"` (it writes `ScopeBoundary` nodes), it
**composes `ask` (310), not raw `AskUserQuestion`** (Spec 307 rule 4, no second
source of truth), and the candidate boundaries are **derived** from the grounding
(312) + decomposition (319), never invented (rule 2).

## Design

**Cluster:** `agency/capabilities/discover/clusters/scope.py` — the
`ScopeCluster` mixin (shared with `acceptance` (317) and `decompose_intent`
(319)) composed into `DiscoverCapability`. Uses Spec 308 `_base.py`
`_recall_intent` + `_record_turn`.

**Verb:**

```python
@verb(role="act")
def scope(self, intent_id: str = "") -> ToolResult:
    """Elicit in-/out-of-scope boundaries via AskUser (act).

    Inputs: intent_id (defaults to ctx.intent_id).
    Returns: {in_scope: list, out_of_scope: list, open: list}.
    chain_next: seed deferred sub-intents from out_of_scope via
                discover.decompose_intent (319).
    """
```

**Deriving the candidate boundaries (derivability audit).** `scope` does NOT
invent boundaries. It draws candidates from two evidence sources already in the
graph:

1. **Grounding (Spec 312, `depends_on`).** The `GROUNDS` citations on the Intent
   (research evidence — adjacent features, prior art, repo neighbours) name things
   that *could* be in scope. Each becomes a candidate boundary ("Does this include
   X, which the grounding found nearby?").
2. **Decomposition (Spec 319).** The sub-problems from a decomposition pass are
   candidate boundaries — the user marks each in or out.

**Composition of the named sibling (Spec 310).** For each candidate, `scope` calls
`discover.ask` to build ONE well-formed question — the options derived from the
candidate (e.g. `[in scope, out of scope, undecided]`, recommended-first per the
evidence), multiSelect where multiple independent boundaries can be asked at once.
The answer is folded back: `scope` records the elicitation turn via `_record_turn`
(an `ElicitationTurn` with `turn_kind="constrain"`, Spec 307 enum) and writes the
boundary node. It never calls `AskUserQuestion` directly — `ask` (310) owns the
well-formed-question contract.

**Spec 307 ontology nodes/edges (BY NAME).** Each decided boundary is a
`ScopeBoundary` node with props `{item, side}` where `side ∈ {in, out}` (the Spec
307 `scope_side` enum, locked there, used here), and a `BOUNDS` edge
**ScopeBoundary → Intent** ("a scope edge on the Intent"). Undecided candidates
are returned in `open` (no node yet — an open boundary is not a fact). The verb
records its `Invocation` SERVES the Intent + the `ELICITS` edges from the session's
turns (provenance moat, Goal 2). The boundary set renders to the `scope-boundary`
schema / Document (Spec 308 schemas, Spec 292 convergence).

**Out-of-scope seeds sub-intents (Spec 319 seam).** The `out_of_scope` list is the
hand-off to `decompose_intent` (319): an out-of-scope item is often a real,
deferred intent. `scope` returns it; `decompose_intent` (319) can mint a deferred
sub-intent tree (`PARENT_INTENT`) from it later. `scope` itself only fences — it
does not mint sub-intents (that's 319's role).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Candidates are derived, not invented (derivability audit):** every candidate
  boundary `scope` asks about traces to a `GROUNDS` citation (312) or a
  decomposition sub-problem (319) on the live Intent — assert each candidate's
  source is one of those live sets, never a fixed string the verb authored.
- **Composition, not reimplementation (rule 4):** `scope` builds its questions via
  `discover.ask` (310) — assert the question shape matches `ask`'s well-formed
  contract (2–4 options, recommended-first), checked against `ask`'s live output
  for the same candidate, so the two surfaces can't diverge. No direct
  `AskUserQuestion` call.
- **`BOUNDS` edge bound + traversed (declare ⇒ traverse, dormant-surface audit):**
  every decided `ScopeBoundary` node has exactly one `BOUNDS` edge to the draft
  `Intent`; the count of `BOUNDS` edges equals `len(in_scope) + len(out_of_scope)`
  — both derived from the live graph, never pinned.
- **Partition invariant:** `in_scope`, `out_of_scope`, and `open` are disjoint and
  cover every candidate — assert `len(in)+len(out)+len(open) == len(candidates)`,
  computed from the live run; an undecided candidate appears ONLY in `open` (no
  `ScopeBoundary` node minted for it).
- **`side` enum honoured:** every minted `ScopeBoundary.side` is a member of the
  Spec 307 `scope_side` enum (`in`/`out`) — assert against the live enum, not a
  literal.

RED: `scope` absent → `capability_discover_scope` unresolved. GREEN: the cluster
lands, the five assertions pass against a live fixture Intent with grounding.

## Acceptance

A caller runs `discover.scope` and is asked — via well-formed `ask` (310)
questions whose candidates are derived from the grounding (312) and decomposition
(319) — to mark each boundary in or out. The decided boundaries land as
`ScopeBoundary` nodes `BOUNDS`-edged to the Intent (`side ∈ {in, out}`), the
undecided ones stay `open` (no node), and the verb returns the three lists. The
out-of-scope set fences the deliverable against creep and is handed to
`decompose_intent` (319) to seed deferred sub-intents. Every decision is a graph
edge the moat (Goal 2) retains, so `replay` (325) can reconstruct *where the
deliverable's fence was drawn and why*.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** "Structure" child of the Spec 307 program; depends on the
  Spec 308 scaffold (shared `scope.py` cluster), Spec 310 (`ask`, the composed
  AskUser primitive), and Spec 312 (`ground`, whose citations seed the
  candidates). Design only — no code.
- **Slice plan:** Slice 1 = derive candidates from grounding, ask via `ask` (310),
  mint `ScopeBoundary` + `BOUNDS` edges, return the three lists with the partition
  + provenance invariants green. Slice 2 = pull decomposition (319) candidates +
  wire the out-of-scope → deferred-sub-intent hand-off, and multiSelect batching
  (one question covering N independent boundaries — the token-economy win, Goal 1).
- **Open question (resolve at build):** when grounding + decomposition surface
  many candidates, does `scope` ask them all (multiSelect batches) or rank and ask
  the top-K to bound the interview? Default: rank by evidence strength, ask the
  top-K as one multiSelect, leave the rest in `open` for a later pass — bounded
  turns over exhaustive ones (Goal 1).
