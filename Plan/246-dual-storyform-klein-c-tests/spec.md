---
spec_id: "246"
slug: dual-storyform-klein-c-tests
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "136"
depends_on: ["136", "120", "147", "219", "246", "149", "150"]
vision_goals: [4]
affects:
  - tests/test_klein_c_property.py
---

# Spec 246 — dual-storyform Klein-c property tests

## Why

Spec 136 ships StoryformSet + Klein-c inversion check + Vortex
transitions. The Klein-c check is decidable but currently tested on a
single canonical KP fixture. As more dual-storyform novels are
authored, the inversion check needs property-level tests: every legal
StoryformSet satisfies Klein-c by construction; an illegal pair fails
with a precise diagnostic. The V₄ structure (two Z₂ flips) is testable
as an algebraic property, not just a fixture.

## Done When

- [ ] **Property test over the Klein-c V₄ structure** — Hypothesis
      generator builds legal StoryformSet pairs from the slot taxonomy;
      `check_klein_c(set) -> KleinCheckResult{ok: bool, flip_a:
      Literal["preserved","broken"], flip_b: Literal["preserved",
      "broken"], offending_slots: list[SlotId], diagnostic: str}` is
      asserted `ok=True` over ≥ 200 generated pairs. Single-slot
      mutation injected → `ok=False` AND `offending_slots == [mutated]`.
- [ ] **Invariant: closure under V₄** — for any legal pair `(A,B)`,
      `flip_a∘flip_a == identity` AND `flip_b∘flip_b == identity` AND
      `flip_a∘flip_b == flip_b∘flip_a`; property test asserts this
      algebraic relationship, not a pinned table of pairs.
- [ ] **Invariant: diagnostic identifies the FLIP, not just the slot** —
      `result.flip_a` and `result.flip_b` each independently report
      preserved/broken; `result.diagnostic` names which Z₂ generator
      was violated. Test: a fixture broken on flip_b only returns
      `flip_a="preserved", flip_b="broken"`.
- [ ] **Invariant: suggest_storyform (219) gates on property test** —
      every proposed inversion partner passes `check_klein_c` before
      surfacing; relationship `proposals_surfaced ==
      check_klein_c.ok_count`. Spec 219 imports the property gate.
- [ ] **Failure modes**: degenerate StoryformSet (single slot) → check
      returns `ok=False, diagnostic="insufficient_slots"`, never
      crashes; unknown slot id → `ok=False, diagnostic="unknown_slot:
      <id>"`; property test fixture drift (slot taxonomy renamed) →
      caught by Spec 149 derived-doc lint, NOT a silent test pass.
- [ ] Test: property test green over 200 generated pairs; mutated
      fixture fails with named slot AND named flip.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a legal StoryformSet pair (Storyform-A: protagonist-driven,
        Storyform-B: antagonist-driven) with V₄ inversion on the
        "driver" + "limit" axes
When:   check_klein_c({A, B}) runs; then we mutate Storyform-B's
        "limit" slot from "optionlock" to "timelock" and re-run
Then:   first call returns ok=True, flip_a="preserved",
        flip_b="preserved"; second call returns ok=False,
        flip_b="broken", offending_slots=["limit"],
        diagnostic="Z2 generator on limit-axis violated: optionlock
        vs timelock not inverted under flip_b"
```

## Interconnects

- Spec 120 (coherence check) is the algebraic sibling — both express
  invariants as group-structure properties, not fixtures.
- Spec 219 (suggest_storyform) uses these as the surface gate.
- Spec 147 (AnthropicDriver) — when 219 proposes partners via LLM, the
  property check is the post-LLM filter; refusals/malformed shapes
  fail closed.
- **Drift-derivation chain** (149) — slot taxonomy + flip definitions
  re-derive from the canonical Dramatica reference; rename triggers
  lint.
- **Dogfood-loop chain** (150) — repeated check failures on the same
  axis classify into amendment proposals (e.g. "limit-axis flip rule
  underspecified").

## Open questions

1. **Hypothesis example budget.** How many generated pairs per CI run?
   **Recommend**: 200 by default, 1000 with `--exhaustive` for
   release-gate runs — keeps per-PR cost sub-second while giving the
   slot taxonomy room to widen without flaking.
2. **Partial inversions.** Surface "flip_a preserved, flip_b broken"
   as a usable proposal, or reject? **Recommend**: reject — partial
   inversion is NOT Klein-c by definition; surface the diagnostic to
   the author, but Spec 219 never proposes it.
3. **Slot-taxonomy versioning.** Pin tests to a slot-taxonomy version,
   or always live? **Recommend**: live, with the taxonomy hash recorded
   in the test artefact; Spec 149 flags if a taxonomy bump invalidates
   the property fixtures.
