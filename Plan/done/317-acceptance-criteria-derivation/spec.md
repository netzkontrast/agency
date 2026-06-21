---
spec_id: "317"
slug: acceptance-criteria-derivation
status: draft
state: done
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["307", "308", "316"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 317 — Acceptance-criteria derivation (`discover.acceptance`)

> Child of the intent-pillar deep program (Spec 307), **"structure" layer**. It
> derives TESTABLE, MEASURABLE acceptance criteria from the captured Intent —
> Gherkin-shaped (Given/When/Then) per the repo's testing doctrine — recording
> each as an `AcceptanceCriterion` node `VALIDATES`-edged to the Intent, and
> sharpening the Intent's `acceptance` field.
>
> **★ FOLDED by Spec 307 §Refinement (2026-06-18).** `acceptance` becomes the
> *gherkin pass* of the merged `sharpen` proposal verb (with `frame`/`examine`) —
> all three propose a triple-delta under the single-writer protocol (master rule
> 3). The `AcceptanceCriterion` node + `VALIDATES` edge survive; the standalone
> verb does not. Retained as the criteria-derivation mechanism record.

## Why (evidence + doctrine)

Spec 307 §"Why" lists *"no acceptance derivation"* among the gaps that make an
Intent born shallow. An Intent's third field — `acceptance` — answers *"are we
there yet?"*, but `intent_bootstrap` (Spec 029) captures whatever sentence the
user typed, which is usually aspirational ("works well", "feels right") rather
than checkable. An unmeasurable acceptance field is worse than none: it lets a
session declare done against a goal that was never testable, and the provenance
moat (Goal 2) then certifies a `done` it can't defend.

The repo's own testing doctrine (CLAUDE.md rule 7) is the template: *"Gherkin
acceptance scenarios (`tests/acceptance/`, pytest-bdd) are the contract."* The
agency tests behaviour through Given/When/Then; an Intent's acceptance should be
shaped the same way — so a confirmed Intent's criteria can, in the limit, seed the
very feature files that validate the work it serves. The Spec 307 coverage matrix
+ flow place `acceptance` (317) right after `scope` (318) and `examine` (316),
deriving the criteria once the deliverable's shape and boundaries are known.

Two doctrine hard contracts govern this verb. **Derivability** (CLAUDE.md
derivability audit, Spec 307 rule 2): criteria are *derived from the intent's
deliverable*, never invented literals. **Invariants, not snapshots** (CLAUDE.md
rule 8): `measurable` is *asserted*, not assumed — a criterion with no observable
check is **flagged, not accepted**. A criterion that can't be checked isn't an
acceptance criterion; it's a wish.

## Design

**Cluster:** `agency/capabilities/discover/clusters/scope.py` — the
`ScopeCluster` mixin (shared with `scope` (318) and `decompose_intent` (319), all
"structure"-layer verbs) composed into `DiscoverCapability`. Uses Spec 308
`_base.py` `_recall_intent`.

**Verb:**

```python
@verb(role="transform")
def acceptance(self, intent_id: str = "") -> ToolResult:
    """Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform).

    Inputs: intent_id (defaults to ctx.intent_id).
    Returns: {criteria: [{text, gherkin, measurable: bool, flagged: bool}],
              acceptance, coverage: {deliverable_parts, covered, gaps}}.
    chain_next: fold `acceptance` into the Intent via intent.amend / refine (320).
    """
```

**Derivation, not invention.** `acceptance` reads the draft Intent via
`_recall_intent`, splits its `deliverable` into sub-parts (each a checkable unit),
and for each sub-part derives one criterion: a `text` statement + a `gherkin`
Given/When/Then triple + a `measurable` bool. The mapping from deliverable
sub-part → criterion is the **driver seam** (Spec 147 structured output) behind
the typed contract — Slice 1 returns the deliverable-tagged scaffold; the wet-LLM
fill (deliverable phrase → Given/When/Then) lands behind it. The premortem
failure-modes surfaced by `examine` (316, the `depends_on`) seed the negative
criteria ("Then it does NOT …"), so examination feeds acceptance.

**The `measurable` contract (hard).** Each criterion is checked for an *observable
assertion*: a `Then` clause naming a concrete, inspectable outcome (a value, a
file, a state, an exit code). A criterion whose `Then` is unobservable
("Then it works well") is returned with `measurable=False` **and** `flagged=True`
— surfaced, never silently accepted. The verb's `coverage` field reports whether
every deliverable sub-part got at least one measurable criterion, and which
sub-parts have a gap.

**Spec 307 ontology nodes/edges (BY NAME).** Each accepted criterion is an
`AcceptanceCriterion` node with props `{text, gherkin, measurable}` (the Spec 307
ontology table, verbatim — props locked by 307, populated here) and a `VALIDATES`
edge **AcceptanceCriterion → Intent** ("a criterion that says 'done' for the
Intent"). The criteria collectively become the Intent's sharpened `acceptance`
field (the caller folds it via `intent.amend` / `refine` (320) — `acceptance` is
`transform`, it proposes; per Spec 307 rule 3, read-only-ish: it MAY mint the
`AcceptanceCriterion` nodes as its structured output, but it does not overwrite
the Intent's field, the caller does). The criteria render to the
`acceptance-criteria` schema / Document (Spec 308 schemas, Spec 292 convergence).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Derived from the deliverable (derivability audit):** every returned criterion
  traces to a sub-part of the Intent's `deliverable` — assert each criterion's
  source sub-part is a substring/token-subset of the live `deliverable`, derived
  from the live Intent, never a fixed sentence the verb authored.
- **`measurable` is asserted, not assumed (the hard contract):** a criterion whose
  `gherkin` `Then` names no observable check is returned with `measurable=False`
  AND `flagged=True` — assert the relationship on a fixture intent with one
  unmeasurable deliverable part (e.g. "works well"), checking that it is flagged,
  not dropped and not silently accepted.
- **`VALIDATES` edge bound + traversed (declare ⇒ traverse, dormant-surface
  audit):** each accepted `AcceptanceCriterion` node has exactly one `VALIDATES`
  edge to the draft `Intent` — assert the edge count equals the accepted-criteria
  count, both derived from the live graph.
- **Coverage relationship:** `coverage.covered + len(coverage.gaps)` equals
  `coverage.deliverable_parts` — assert the partition holds, computed from the
  live deliverable split, never a pinned number; a deliverable with N parts and M
  measurable criteria reports exactly `N - covered` gaps.
- **Gherkin shape:** every criterion's `gherkin` parses into Given/When/Then
  (three clauses) — assert structural validity, not specific text.

RED: `acceptance` absent → `capability_discover_acceptance` unresolved. GREEN: the
cluster lands, the five assertions pass against a live fixture Intent.

## Acceptance

A caller runs `discover.acceptance` against a captured Intent and receives a list
of Gherkin-shaped criteria — each `VALIDATES`-edged to the Intent, each tagged
`measurable` with the unmeasurable ones **flagged rather than accepted** — plus a
coverage note saying whether every deliverable sub-part has a criterion and which
gaps remain. The criteria are derived from the deliverable (and seeded by 316's
failure modes), become the Intent's sharpened `acceptance` field when the caller
folds them, and render to the `acceptance-criteria` Document (Spec 292). The moat
(Goal 2) now holds checkable "done" conditions, not a wish.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** "Structure" child of the Spec 307 program; depends on the
  Spec 308 scaffold (the shared `scope.py` cluster home) and Spec 316 (`examine`,
  whose failure modes seed the negative criteria). Design only — no code.
- **Slice plan:** Slice 1 = split deliverable → criteria scaffolds, mint
  `AcceptanceCriterion` nodes + `VALIDATES` edges, enforce the `measurable`/`flagged`
  contract, return coverage; provenance + flag invariants green. Slice 2 = the
  wet-LLM Given/When/Then fill (Spec 147) behind the same typed signature; the
  measurability heuristic graduates from "Then names a value/file/state/code" to a
  richer observable-check classifier.
- **Open question (resolve at build):** does a `flagged` (unmeasurable) criterion
  still mint an `AcceptanceCriterion` node (with `measurable=False`) so the gap is
  visible in the graph, or stay out of the graph until measurable? Default: mint
  it flagged — a visible unmeasurable criterion is itself a clarity signal (322)
  and a `clarify` (311) trigger; dropping it hides the gap.
