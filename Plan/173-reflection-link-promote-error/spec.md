---
spec_id: "173"
slug: reflection-link-promote-error
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "058"
depends_on: ["058", "150", "159", "149"]
vision_goals: [2, 6]
affects:
  - agency/_lints/_reflection_links.py
  - tests/test_reflection_link_error.py
---

# Spec 173 — reflection-link lint promotion to error

## Why

Spec 058 ships a WARN-only `_check_reflection_links` lint (a Reflection
write must link BOTH SERVES + OBSERVED_DURING) and migrated the audit
sites. The dogfood-loop closure (Spec 150) makes Reflections
load-bearing — the amendment classifier reads them — so an unlinked
Reflection is now a silent provenance hole that breaks the loop. The
lint should promote to error.

## Done When (measurable invariants — rule 8)

- [ ] **Typed lint finding: `LinkFinding{reflection_id, missing_edge:
      Literal["SERVES", "OBSERVED_DURING"], severity: Literal["error",
      "warn"], file, line}`** — uniform shape across the promotion.
- [ ] **Invariant: `unlinked_reflections == ∅`** across the live
      graph — every Reflection has BOTH `SERVES` (Intent) AND
      `OBSERVED_DURING` (phase/skill walk) edges. Derived from a
      graph query, not pinned.
- [ ] **Invariant: lint severity is `error` iff sweep is clean** —
      relationship; the promotion is gated on zero live violations
      (Spec 056/058 non-negotiable).
- [ ] **Invariant: Spec 150 classifier's attribution rate ==
      `len(proposals) / len(linked_reflections)`** — every classified
      proposal traces back to its OBSERVED_DURING source; orphan
      proposals are impossible post-promotion.
- [ ] **Invariant: Spec 159 `note(auto_scope)` writes BOTH edges
      atomically** — a partial write (one edge present, one missing)
      fails `Codes.REFLECTION_PARTIAL_LINKS` at write time, never
      surfaces to the classifier.
- [ ] **Relationship: a fixture Reflection missing OBSERVED_DURING
      trips the post-promotion lint** — proves the gate; not pinned
      to a specific verb.
- [ ] **Failure mode (write path):** a Reflection write with no
      open Intent in scope cannot satisfy SERVES → write fails fast
      with `Codes.REFLECTION_NO_INTENT` + a hint pointing at
      `intent_bootstrap` (Spec 176 onboarding flow).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  live registry sweep reports zero unlinked Reflections;
        lint WARN-only
When:   PR promotes lint → error AND adds a fixture verb that
        emits a Reflection via the raw `graph.write` (bypassing
        Spec 159 `note(auto_scope)`)
Then:   lint emits LinkFinding{missing_edge="OBSERVED_DURING",
        severity="error"}; CI fails the PR

Given:  same PR fixes the fixture to route through `note(auto_scope)`
When:   lint reruns
Then:   findings == [] AND Spec 150's classifier can attribute
        the Reflection's proposal to its originating phase
        (OBSERVED_DURING edge resolves)

Given:  a verb tries to write a Reflection with no open Intent in
        the AGENCY_INTENT env (rare; pre-bootstrap)
When:   write executes
Then:   raises REFLECTION_NO_INTENT pointing at intent_bootstrap;
        no half-linked Reflection lands in the graph
```

## Failure modes

| Failure | Linter / write response |
|---|---|
| Reflection with only SERVES | `LinkFinding{missing_edge="OBSERVED_DURING", severity="error"}` |
| Reflection with only OBSERVED_DURING | `LinkFinding{missing_edge="SERVES", severity="error"}` |
| Atomic write fails mid-way | rollback both edges; `REFLECTION_PARTIAL_LINKS` |
| No open Intent at write time | `REFLECTION_NO_INTENT` + bootstrap hint |
| Spec 150 classifier receives an orphan (legacy data) | classifier silently skips + emits a `CLASSIFIER_ORPHAN_SKIPPED` Reflection (which itself must be linked) |

## Interconnects

- **Dogfood-loop chain** (150/159): makes the loop's provenance whole;
  Spec 150's classifier depends on the OBSERVED_DURING invariant.
- **LLM-driver chain** (147): the classifier's Driver call routes
  through the typed envelope; orphan-proof attribution.
- **Drift-derivation chain** (149): sweep result derived per-PR.
- Spec 058 is the parent; Spec 171 the parallel promotion (node-id
  guards); both follow the WARN→error promotion discipline.
- Spec 164 (implementation-discipline wet) emits Reflections from
  failed gate verifies — relies on this promotion.
- Spec 170 (doctor) reports `reflection_link_coverage`.
- Spec 176 (SessionStart Intent capture) ensures an open Intent
  exists by the time any verb writes a Reflection.
- Spec 151 (Codes coverage) supplies `REFLECTION_PARTIAL_LINKS` +
  `REFLECTION_NO_INTENT` + `CLASSIFIER_ORPHAN_SKIPPED`.

## Open questions

1. Promote before or after the sweep? **Recommend**: after — the
   non-negotiable promotion rule (zero known violations first).
2. Migrate legacy orphan Reflections in place, or quarantine?
   **Recommend**: quarantine in a `legacy_orphan` partition; classifier
   skips them; a one-shot script can re-link by walking adjacent
   Intent edges.
3. Edge-strictness — both required, or one-of? **Recommend**: both
   strictly. Goal 6 (dogfood) depends on the classifier's full
   provenance; loosening one half hollows the loop.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the typed-shape wave-1 batch (intent:ba14917e tdd walk).

### Done — Slice 1

Typed frozen dataclass + `__post_init__` invariants — see
`agency/_link_finding.py` (Spec 173) and `agency/_typed_shapes_wave1.py`
(Specs 171/175/176). 19 tests in `tests/test_link_finding.py` +
`tests/test_typed_shapes_wave1.py`. The data shape is the Slice 1
contract; Slice 2 wires it into the live verb / gate / hook layer.

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections. The Slice 2
wiring path (graph query, CI gate, sessionstart hook, install
generator) is the next step.

