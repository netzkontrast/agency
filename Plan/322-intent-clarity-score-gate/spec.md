---
spec_id: "322"
slug: intent-clarity-score-gate
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["307", "308", "311", "312", "317", "318"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 322 — Intent clarity score + capture gate (`discover.clarity`)

> Child of the intent-pillar deep program (Spec 307), **quality-gate layer**.
> Mirrors `prompt.audit`'s clarity score for the WHY: it scores a captured
> Intent's readiness from live discovery signals, and defines the hard CAPTURE
> GATE the `guided-discovery` discipline (Spec 323) reads before `confirm`.
>
> **★ RELOCATED by Spec 307 §Refinement (2026-06-18).** The gate moves DOWN onto
> the substrate: `confirm` (in `intent/_core.py`) **is** the gate — it raises below
> the clarity threshold unless given an override token — so it is *unbypassable*
> (the canonical `capture_and_confirm`, `intent.py:82`, can no longer mint a
> confirmed-but-shallow Intent, which a `discover`-only gate allowed). The
> `clarity` scoring logic here is retained; its *home* is the substrate, not a
> capability verb. This is the highest-leverage altitude fix.

## Why (evidence + doctrine)

Spec 307 §"verb surface" locks `clarity` to the `refine` cluster as the score the
`confirm` gate reads; §"coverage matrix" assigns it the **Lifecycle (gates)** row.
The program's whole thesis (Spec 307 §thesis) ends at a **clarity gate**: *"The
loop runs until the intent clears a clarity gate, then `confirm` fires."* Without
this verb the gate has nothing to read — an intent could be confirmed while still
underspecified, ungrounded, or missing acceptance, and every downstream `SERVES`
edge would inherit that shallowness. The provenance moat (Goal 2) is only as good
as the intent it attaches to; a clarity gate is what guarantees the root is
*sharp before work serves it*.

The pattern already exists for prompts: `prompt.audit` /
`prompt.audit_gate` (agency/capabilities/prompt/clusters/{engineering,gates}.py)
COMPUTE a 0-100 clarity score from `_score_brief` and gate on `score ≥ min_score`.
This child does the same for an **Intent**, reading the discovery suite's signals
instead of prose heuristics.

**CLAUDE.md rule 8 — the score is COMPUTED, the threshold is a documented
budget.** The clarity score is derived from live graph signals every call (never
a frozen number); the gate threshold is a single documented tunable budget
(like `_DEFAULT_AUDIT_MIN_SCORE`), named and overridable — not a snapshot of the
current surface. This is the explicit reason the verb is read-only and the gate
is a separate, override-able layer.

## Design

**Cluster path.** `agency/capabilities/discover/clusters/refine.py` (shared with
`discover.refine`, Spec 320). Composes the `DiscoverCluster` mixin's
`_clarity_inputs(intent_id)` (Spec 308 §"_base.py") — the signal bag this verb
reads.

**Verb signature.**

```python
@verb(role="transform")          # read-only — no graph mutation beyond the Invocation
def clarity(self, intent_id: str = "") -> ToolResult:
    """Score a captured Intent's clarity/readiness (transform, read-only).

    Inputs: intent_id (defaults to ctx.intent_id).
    Returns: {score, missing, ready}.   # score 0.0-1.0; ready = score >= threshold
    chain_next: resolve a `missing` signal (clarify/acceptance/ground/scope), re-score.
    """
```

**The signals (each COMPUTED from the live graph, derivability audit).** The
score is the normalized sum of independent readiness signals, read from the
discovery suite's own nodes/edges:

| Signal | Source | Read from |
|---|---|---|
| has purpose + deliverable + acceptance | the Intent node | `_recall_intent` props |
| acceptance is measurable | Spec 317 | `AcceptanceCriterion.measurable` via `VALIDATES` |
| ambiguities resolved | Spec 311 | no open `ClarificationQuestion` `CLARIFIES`-linked |
| grounded by ≥1 Citation | Spec 312 | a `Citation` `GROUNDS`→Intent edge exists |
| scope bounded | Spec 318 | a `ScopeBoundary` `BOUNDS`→Intent edge exists |

`missing` lists the unsatisfied signals (so the agent knows the next discovery
step); `ready = score >= threshold`. No new node — `clarity` reads existing
discovery nodes/edges (Spec 307 §coherence rule 3, read-only stays read-only;
rule 4, no second source of truth).

**Spec-307 ontology used (by name).** Reads `AcceptanceCriterion`/`VALIDATES`
(317), `ClarificationQuestion`/`CLARIFIES` (311), `Citation`/`GROUNDS` (312),
`ScopeBoundary`/`BOUNDS` (318). Writes nothing.

**The CAPTURE GATE (the second deliverable).** A `confirm`-time **hard gate** —
the final phase of the `guided-discovery` skill (Spec 323), declared in that
skill's phase as a `gate_verb` (the live-registry phase field,
agency/_skill_parse.py:122) pointing at a composite `clarity_gate` that delegates
to the `gate` capability's `check` (the `prompt.audit_gate` pattern,
agency/capabilities/prompt/clusters/gates.py). It REFUSES to confirm an Intent
whose clarity is below the threshold **without an explicit override token** —
ensuring the intent is "clearly captured" before any work SERVES it. The override
is the documented escape hatch (an agent may knowingly confirm a low-clarity
intent), recorded as a Gate result so the moat shows the bypass.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Monotonicity (the headline invariant):** resolving an ambiguity (Spec 311) or
  adding a measurable `AcceptanceCriterion` (Spec 317) NEVER lowers the score —
  assert `score_after >= score_before` across each signal flip, computed from the
  live graph, never a pinned score.
- **Computed, not frozen:** an Intent with all five signals scores higher than one
  missing two — assert the *relationship* (`full > partial`), not a magic 0.8.
- **`missing` is accurate:** every signal in `missing` is genuinely unsatisfied in
  the graph, and resolving it removes it from `missing` on re-score.
- **Read-only:** `clarity` adds zero domain nodes (delta == the Invocation) —
  asserted against a live census (Spec 307 §coherence rule 3).
- **Gate refuses below threshold:** confirming an Intent with `ready=False`
  through the `clarity_gate` fails (typed `GATE_FAILED`) WITHOUT an override
  token; WITH the override it passes and records the bypass as a Gate result.
- **Threshold is a documented budget:** the gate reads an overridable
  `min_clarity` (default named, like `_DEFAULT_AUDIT_MIN_SCORE`) — assert the gate
  flips when the threshold is overridden, proving it is config not a constant
  (CLAUDE.md #8).

## Acceptance

`discover.clarity` returns a `{score, missing, ready}` computed live from the
discovery suite's signals; the score is monotone in resolved ambiguities and
added measurable criteria. The `guided-discovery` discipline's final phase reads
it as a hard gate that refuses to confirm a below-threshold Intent without an
explicit, recorded override — so an Intent is *clearly captured* before work
serves it. The threshold is a documented tunable budget, not a snapshot.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Quality-gate-layer child of Spec 307. Mirrors the shipped
  `prompt.audit`/`audit_gate` pattern; the new surface is the Intent-signal
  scorer + the `clarity_gate` the Spec 323 skill phase reads via `gate_verb`.
- **Slice plan:** Slice 1 — `clarity` reading the five signals from `_clarity_inputs`
  (typed bag) and returning `{score, missing, ready}`; Slice 2 — the `clarity_gate`
  composite + the override token + Gate-result recording; Slice 3 — Spec 323 wires
  it as the discipline's final phase `gate_verb`.
- **Open question (resolve at build):** weight the five signals equally vs.
  weight acceptance-measurable + grounded higher. Default equal weights (simplest
  monotone), documented + overridable, per CLAUDE.md #8.
