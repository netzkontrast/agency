---
spec_id: "233"
slug: worldbuilding-slice2-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "123"
depends_on: ["123", "138", "147", "150"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_worldbuilding_slice2.py
---

# Spec 233 — worldbuilding Slice 2 (Conflict/Theme/PlantedElement)

## Why

Spec 123 ships World sub-graph Slice 1; its Followup names Slice 2:
Conflict + Theme tracking + PlantedElement foreshadowing + skill
rewiring + `developmental_gate` extension. The PsychProfile carve-out
is superseded by Spec 138 (plural-character) — but Conflict/Theme/
PlantedElement remain. Plus an optional Spec 147 judgement pass for
axiom contradictions Open Q2 deferred.

## Done When

- [ ] **Conflict + Theme nodes + 4 verbs** (novel-scoped per Open Q1) —
      verbs return typed shapes: `add_conflict(novel_id, …) -> Conflict`,
      `track_theme(novel_id, …) -> Theme`, where `Conflict = {id, kind,
      parties: list[CharacterId], stakes, status}` and `Theme = {id,
      statement, expressions: list[SceneId]}`. Invariant: every Conflict
      has `len(parties) >= 2`; every Theme has `len(expressions) >= 1`
      after a `developmental_gate` pass on a covered fixture.
- [ ] **PlantedElement + Chekhov's-gun audit** — invariant:
      `planted_count == fired_count + outstanding_count`; the audit
      returns `{planted, fired, outstanding: list[PlantedElementId]}`
      and outstanding is the gate's failing set (relation, not pinned
      count). Complement to Spec 140's named Anchor.
- [ ] **`developmental_gate` extension** — invariant: gate FAILS iff any
      Conflict carries `status="unresolved"` past the final beat OR any
      Theme has zero scene expressions OR `outstanding_count > 0` at
      story end. Each failure returns the offending node-id, never a
      bare count.
- [ ] **Optional judgement pass** via `thinking.red_team` (Spec 147)
      for axiom contradictions (Open Q2 closed) — judged findings are
      ADVISORY (severity ≤ WARN) per Spec 232 pattern, never raise the
      decidable gate verdict.
- [ ] **Failure modes** — Driver unavailable → judgement pass SKIPPED
      with `Codes.DRIVER_UNAVAILABLE` recorded as a WARN; malformed JSON
      → `Codes.JUDGE_PARSE_FAILED` logged, decidable result stands;
      planted-element without a fired-or-outstanding tag → gate raises
      `Codes.CHEKHOV_UNTAGGED` (decidable, blocks).
- [ ] Test: Chekhov audit + theme coverage on a fixture novel.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with 3 PlantedElements (gun, letter, ring), 2 fired
        by the climax, 1 outstanding; 2 Themes both with scene
        expressions; all Conflicts resolved
When:   developmental_gate(novel_id) runs
Then:   gate.outstanding == ["ring"] AND
        gate.passed is False AND
        the failure reason names the outstanding PlantedElement id,
        never a literal count

Given:  same novel, the ring is tagged fired in the epilogue scene
When:   developmental_gate(novel_id) re-runs
Then:   gate.outstanding == [] AND gate.passed is True AND
        planted_count == fired_count (invariant holds)
```

## Interconnects

- Spec 138 supersedes PsychProfile; Spec 140 (Anchor) sibling.
- **LLM-driver chain** (147) for the judgement pass.
- Spec 232 (editorial judge) — same advisory-only judge pattern.
- Spec 235 (typed paths) — Conflict→PARTY→Character traversal builds
  on `neighbors_path` rather than ad-hoc joins.
- Spec 238 (story-time query) — PlantedElement→FIRED_IN edge is one of
  the relational time queries.

## Open questions

1. **Theme expression minimum.** How many scene expressions count as
   "covered"? **Recommend:** ≥1 expression per act (derived from
   StructuralBeat count), not a pinned absolute.
2. **Conflict status enum.** Closed enum or open? **Recommend:** closed
   — `{"open","resolved","abandoned"}` — gate semantics require it.
3. **Judged-pass cost.** Run on every gate? **Recommend:** opt-in via
   `judge=True`, parity with Spec 232.
