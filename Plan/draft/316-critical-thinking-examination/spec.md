---
spec_id: "316"
slug: critical-thinking-examination
status: draft
state: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["091", "110", "307", "308", "311"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 316 — Critical-thinking examination of the draft (`discover.examine`)

> Child of the intent-pillar deep program (Spec 307), **"sharpen the WHY"
> layer**. This is the bridge from the THINKING pillar into Intent: it runs the
> `thinking` methods (Spec 110) over the DRAFT Intent BEFORE confirm, surfacing
> unstated assumptions, failure modes, and whether the goal survives
> first-principles — feeding `clarify` (311) and the clarity score (322).
>
> **★ FOLDED by Spec 307 §Refinement (2026-06-18).** `examine` is a near-duplicate
> of the shipped `thinking.apply_full_review(subject=intent.deliverable)` plus one
> `ANALYZES` edge; it becomes the *thinking pass* of the merged `sharpen` proposal
> (with `frame`/`acceptance`), calling the composite rather than re-sequencing the
> methods. Retained as the mechanism record.

## Why (evidence + doctrine)

Spec 307 §"Why" names the gap precisely: discovery has *"no … exploration …
before the intent is confirmed,"* and the provenance moat (Goal 2) *"records what
was done against an intent that was never sharpened."* A confirmed intent that
rests on an unstated, false assumption poisons every downstream `SERVES` edge.
Critical examination before confirm is the cheapest place to catch that.

The substrate already owns the methods. Spec 110 shipped the `thinking`
capability — 10 critical-thinking methods (`decompose`, `assumptions`,
`premortem`, `first_principles`, `inversion`, `steelman`, `second_order`,
`tradeoffs`, `red_team`, `socratic`) plus `apply_full_review` — each a transform
returning a structured scaffold. Spec 291 **folded the intent critical-thinking
methods (Spec 091) into `thinking`**, so there is exactly one home for these
methods. The Spec 307 coverage matrix binds both the `thinking` capability AND the
Spec-091 intent critical-thinking to this single child: *"`examine` runs
decompose/assumptions/premortem on the draft … folded via `examine` (honours the
291 merge into `thinking`)."*

So `examine` must **compose `thinking.*`, not reimplement it** (CLAUDE.md rule 4
of Spec 307; the dormant-surface + derivability audits). Reimplementing the
scaffolds would be a second source of truth that drifts. The value `examine` adds
is *binding the method outputs to the draft Intent as provenance* — each scaffold
becomes an artefact the moat (Goal 2) retains, and the load-bearing assumptions +
premortem failure-modes become inputs to `clarify` (311) and `clarity` (322).
Examination is where the moat earns its keep: a replayable record of *whether the
WHY survived scrutiny*.

## Design

**Cluster:** `agency/capabilities/discover/clusters/examine.py` — the
`ExamineCluster` mixin composed into `DiscoverCapability` (Spec 308 `_base.py`;
uses `_recall_intent`).

**Verb:**

```python
@verb(role="act")
def examine(self, intent_id: str = "", depth: str = "standard") -> ToolResult:
    """Run thinking methods over the draft Intent before confirm (act).

    Inputs: intent_id (defaults to ctx.intent_id), depth ∈ {standard, deep}.
    standard → decompose · assumptions · premortem · inversion.
    deep adds → first_principles · steelman · second_order · tradeoffs.
    Returns: {assumptions_surfaced, failure_modes, survives_first_principles,
              recommendation}.
    chain_next: discover.clarify (311) on the load-bearing assumptions.
    """
```

**Composition of the named sibling (Spec 110).** For each method in the
depth-selected set, `examine` calls `self.ctx`'s `thinking` surface — invoking
e.g. `thinking.assumptions(subject=<intent.deliverable>)` — and harvests the
returned scaffold. It does NOT re-derive any scaffold; the method set is read
from `thinking`'s live verbs (a `depth` map of method names, not copied bodies).
`subject` defaults to the draft Intent's `deliverable` (the Spec 091 ambient
pattern `_subject_or_default` already uses). The depth tiers mirror Spec 110's own
`ANALYSIS_DEPTH` enum (`standard`/`deep`) — reused, not redefined.

**What `examine` produces (the provenance, Goal 2).** Each method's scaffold
output is recorded as an **artefact linked to the Intent**. Concretely, every run
records a `thinking`-derived finding bound to the draft via the `ANALYZES` edge
(Spec 110's edge, `ThinkingMethod`/`ThinkingFinding` → subject), with the subject
being the `Intent` node. The verb then projects the harvest into its four-field
return:

- `assumptions_surfaced` — the load-bearing claims from the `assumptions` method
  (those marked `load_bearing: true`), which become candidate `unstated-assumption`
  ambiguities for `clarify` (311, `ambiguity_kind` enum, Spec 307).
- `failure_modes` — the ranked causes from `premortem` (+ `inversion`'s
  failure-guarantee patterns), feeding the clarity signal bag (322).
- `survives_first_principles` — a bool, present only at `deep` depth, from the
  `first_principles` reconstruction ("does the goal survive?").
- `recommendation` — proceed / clarify-first / refine, derived from the findings
  (high-severity assumption refuted ⇒ `refine` (320); load-bearing-but-untested
  ⇒ `clarify` (311)).

**Spec 307 ontology / seam.** `examine` is `role="act"` (it writes findings), so
it records its `Invocation` SERVES the Intent + the `thinking` findings'
`ANALYZES` edges to the Intent node. It mints **no new `discover` node type** —
the findings live on `thinking`'s existing `ThinkingFinding`/`ANALYZES` ontology
(reuse, like `GROUNDS` reuses research's `Citation` per Spec 307). The
`assumptions_surfaced` / `failure_modes` it returns are consumed by `clarify`
(311) and read by `clarity` (322) via `_clarity_inputs` (Spec 308 `_base.py`).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Composition, not reimplementation (rule 4):** the method set `examine` runs at
  a given `depth` is a SUBSET of `thinking`'s live verb names — assert membership
  against the live `thinking` registry, not a copied list, so adding a thinking
  method never silently desyncs. `standard ⊂ deep` (deep is a superset).
- **Depth monotonicity:** `examine(depth="deep")` runs strictly more methods than
  `examine(depth="standard")` on the same intent — assert
  `len(deep.methods) > len(standard.methods)`, computed from the runs, and
  `survives_first_principles` is present only at `deep` (it comes from the
  first_principles method, deep-only).
- **Provenance bound to the draft (Goal 2):** after `examine`, every harvested
  finding has an `ANALYZES` edge whose target IS the draft `Intent` node — assert
  the edge count equals the methods-run count, both derived from the live graph
  (declare-an-edge ⇒ traverse-it; the dormant-surface audit).
- **Feeds clarify (311):** every `unstated-assumption` candidate `examine` returns
  in `assumptions_surfaced` is a load-bearing assumption from the `assumptions`
  scaffold — assert the surfaced set ⊆ the load-bearing set, derived live, never a
  fixed sentence.
- **Recommendation is derived:** the `recommendation` value is one of the three
  allowed outcomes AND is consistent with the findings (a refuted load-bearing
  assumption ⇒ not `proceed`) — assert the relationship, not a pinned string.

RED: `examine` absent → `capability_discover_examine` unresolved. GREEN: the
cluster lands, the five assertions pass against the live `thinking` surface + live
graph.

## Acceptance

Before an Intent is confirmed, a caller runs `discover.examine` and gets back the
surfaced load-bearing assumptions, the ranked failure modes, whether the goal
survives first-principles (at deep), and a derived recommendation — with every
method's scaffold recorded as a finding `ANALYZES`-edged to the draft Intent, so
`replay` (325) can reconstruct *that the WHY was scrutinised and how*. The methods
are the live `thinking` verbs (Spec 110), composed not copied (honouring the Spec
291 merge of Spec 091's intent critical-thinking). The surfaced assumptions feed
`clarify` (311); the failure modes and survival verdict feed the clarity score
(322). Zero new `discover` node types — the moat is whole on `thinking`'s
existing ontology.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** "Sharpen the WHY" child of the Spec 307 program; depends on
  the Spec 308 scaffold, Spec 110 (`thinking`, the composed sibling), Spec 091 +
  Spec 291 (the intent-critical-thinking merge it honours), and Spec 311
  (`clarify`, the consumer of its surfaced assumptions). Design only — no code.
- **Slice plan:** Slice 1 = run the `standard` method set, harvest scaffolds, bind
  `ANALYZES` edges to the draft Intent, return the four fields with the
  provenance + composition invariants green. Slice 2 = `deep` tier +
  `survives_first_principles` + the derived `recommendation` outcome logic.
- **Open question (resolve at build):** does `examine` call `thinking.apply_full_review`
  (the Spec 110 composite, which itself sequences 8 methods + records a
  `thinking-analysis` artefact) and re-bind that one artefact to the Intent, OR
  call the individual methods to control the depth tiers precisely? Default:
  individual methods (the `standard`/`deep` tiers don't match the composite's
  fixed 8), with `apply_full_review` reserved for a future `depth="full"`.
