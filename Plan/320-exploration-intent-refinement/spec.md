---
spec_id: "320"
slug: exploration-intent-refinement
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["048", "307", "308", "312", "314"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 320 — Exploration-driven intent refinement (`discover.refine`)

> Child of the intent-pillar deep program (Spec 307), **lifecycle layer**. When
> exploration reveals the intent was wrong or incomplete, this BI-TEMPORALLY
> supersedes it and records WHY the WHY changed — the provenance moat for intent
> evolution, not a silent overwrite.

## Why (evidence + doctrine)

Spec 307 §"thesis" is explicit: *"A shallow intent is a guess. A discovered
intent is grounded."* But grounding can also **invalidate** the guess. The
feasibility probe (Spec 314) returns a `no-go`; the grounding pass (Spec 312)
surfaces a `Citation` proving the thing already exists; the clarify loop
(Spec 311) exposes a contradiction in the stated purpose. In every case the
*right* move is not to abandon the Intent but to **refine** it — change the WHY
while keeping the history of what it used to be and what discovery triggered the
change.

The substrate already supports this: `agency/intent.py:amend` calls
`memory.supersede` (agency/memory.py:139) — append-only, the prior version keeps
its valid window, latest `recorded_at` wins on read, and as-of reconstruction
returns the old purpose. What is **missing** is the discovery-side provenance:
*why* did the supersede happen and *which exploration finding* triggered it.
Spec 307 §ontology answers this with the `IntentRefinement` node and the
`REFINES` edge. Without them the moat (Goal 2) records that the intent changed
but not *why* — and "the WHY changed" is the single most important fact about an
evolving intent.

## Design

**Cluster path.** `agency/capabilities/discover/clusters/refine.py` (shared with
`discover.clarity`, Spec 322, per Spec 307 §"Architecture"). Composes the
`DiscoverCluster` mixin for `_recall_intent`.

**Verb signature.**

```python
@verb(role="act")
def refine(self, intent_id: str = "", trigger: str = "") -> ToolResult:
    """Supersede an Intent from an exploration finding, bi-temporally (act).

    Inputs: intent_id (defaults to ctx.intent_id), trigger (the finding text/id).
    Returns: {old_version, new_version, trigger, delta}.
    chain_next: discover.clarity on the new version; discover.confirm via the gate.
    """
```

**Substrate composition.**

1. **Capture before-state.** Read the live Intent via `_recall_intent` — its
   `{purpose, deliverable, acceptance}` is the `before`.
2. **Supersede (bi-temporal).** Call the substrate `intent.amend(intent_id,
   **changes)` → `memory.supersede`. The prior version's `vto` closes to *now*;
   a new `{id}#{now}` version opens with `vfrom=now, vto=OPEN`; the substrate
   links the **`SUPERSEDED_BY`** edge (agency/memory.py:157). The old version
   keeps its valid window — nothing is overwritten (CLAUDE.md rule 2, keep-both).
3. **Record the WHY.** Mint an **`IntentRefinement`** node (Spec 307 ontology:
   props `trigger`, `before`, `after`) and link it to the Intent with the
   **`REFINES`** edge — **PAIRED** with the substrate `SUPERSEDED_BY` edge so the
   graph carries both "the version forked" (substrate) and "this discovery
   finding caused it" (discover). The `trigger` is derived from the exploration
   source: a Spec 314 `FeasibilitySignal` (`verdict="no-go"`), a Spec 312
   `Citation` via `GROUNDS`, or a Spec 311 `ClarificationQuestion` contradiction.

**Spec-307 ontology used (by name).** `IntentRefinement` node; `REFINES` edge
(IntentRefinement→Intent), explicitly *paired with the substrate `SUPERSEDED_BY`*
per Spec 307 §ontology ("a supersession trigger, paired with the substrate
`SUPERSEDED_BY`"). No new enum. The `delta` in the return is computed from
before/after, not stored redundantly (derivability audit).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Bi-temporal retention (the headline invariant):** capture the pre-refine
  timestamp `t0`; after `refine`, an as-of(`t0`) reconstruction of the Intent
  still returns the OLD purpose — assert the old purpose is recoverable, proving
  nothing was overwritten. (Spec 307 §coherence rule 6.)
- **Latest wins on read:** an as-of(now) / current read returns the NEW purpose.
  Both assertions are computed from the live graph, not pinned strings beyond the
  fixture's own inputs.
- **Paired edges (invariant):** the new version has BOTH a substrate
  `SUPERSEDED_BY` edge (from the old) AND an `IntentRefinement`—`REFINES`→Intent
  edge — assert both exist for the same refinement (the moat is whole).
- **Trigger provenance:** the `IntentRefinement.trigger` is non-empty and traces
  to a real exploration finding (a Spec 314 `FeasibilitySignal` / Spec 312
  `Citation` id when one is passed) — derivability, not a free string.
- **Delta correctness:** the returned `delta` equals the field-diff of
  before→after, computed live (no frozen delta).

## Acceptance

When exploration invalidates an intent (a 314 no-go, a 312 grounding find, a 311
contradiction), `discover.refine` supersedes it bi-temporally, the old purpose is
still reconstructable as-of its valid window, and the graph carries an
`IntentRefinement`/`REFINES` record paired with the substrate `SUPERSEDED_BY`
edge — so a later reader can answer *"why did the WHY change, and what discovery
triggered it."* No silent overwrite; history is retained.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Lifecycle-layer child of Spec 307. Sits directly on shipped
  substrate (`intent.amend` → `memory.supersede`, agency/memory.py:139); the new
  surface is the `IntentRefinement`/`REFINES` provenance pairing.
- **Naming note:** the live substrate emits **`SUPERSEDED_BY`**
  (agency/memory.py:157); Spec 307 §ontology and this child both pair `REFINES`
  with that live edge name. The substrate emit is the ground truth (no second
  source — rule 4).
- **Slice plan:** Slice 1 — supersede + `IntentRefinement`/`REFINES` with the
  trigger as a typed shape; Slice 2 — wire the trigger sources (314/312/311) so a
  refinement can cite the finding id that caused it.
