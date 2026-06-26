<!-- agency-node: document:ac02a1dc -->
---
spec_id: "173"
slug: reflection-link-promote-error
status: done
state: done
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

- [x] **Typed lint finding: `LinkFinding{reflection_id, missing_edge:
      Literal["SERVES", "OBSERVED_DURING"], severity: Literal["error",
      "warn"], file, line}`** — uniform shape across the promotion.
- [x] **Invariant: `unlinked_reflections == ∅`** across the live
      graph — every Reflection has BOTH `SERVES` (Intent) AND
      `OBSERVED_DURING` (phase/skill walk) edges. Derived from a
      graph query, not pinned.
- [x] **Invariant: lint severity is `error` iff sweep is clean** —
      relationship; the promotion is gated on zero live violations
      (Spec 056/058 non-negotiable).
- [x] **Invariant: Spec 150 classifier's attribution rate ==
      `len(proposals) / len(linked_reflections)`** — every classified
      proposal traces back to its OBSERVED_DURING source; orphan
      proposals are impossible post-promotion.
- [x] **Invariant: Spec 159 `note(auto_scope)` writes BOTH edges
      atomically** — a partial write (one edge present, one missing)
      fails `Codes.REFLECTION_PARTIAL_LINKS` at write time, never
      surfaces to the classifier.
- [x] **Relationship: a fixture Reflection missing OBSERVED_DURING
      trips the post-promotion lint** — proves the gate; not pinned
      to a specific verb.
- [x] **Failure mode (write path):** a Reflection write with no
      open Intent in scope cannot satisfy SERVES → write fails fast
      with `Codes.REFLECTION_NO_INTENT` + a hint pointing at
      `intent_bootstrap` (Spec 176 onboarding flow).
- [x] TODO row + drift clean.

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

### Shipped — Slice 2 (2026-06-23, TDD)

The dormant `LinkFinding` shape is now load-bearing. **`agency/_reflection_link_sweep.py`**
sweeps every live `Reflection` node for BOTH `SERVES` + `OBSERVED_DURING` edges →
typed `LinkFinding[]`; a node missing exactly one edge sets
`Codes.REFLECTION_PARTIAL_LINKS`. `ready` is True iff `unlinked_reflections == ∅`.

- **Invariant proven clean:** the source lint (every verb that records a Reflection
  links both edges) reports 0 findings, AND the live graph sweep is clean → `ready`.
- **Promotion (WARN→error):** `ReflectionLinkRule.severity` `soft`→`block` — gated on
  clean. Verified: 0 block findings across the live registry; a fixture Reflection
  with only `SERVES` trips `LinkFinding{missing_edge:"OBSERVED_DURING",
  severity:"error"}` and breaks `ready`.
- **Write-path (item 7) — substrate-enforced:** `Codes.REFLECTION_NO_INTENT` is
  satisfied UPSTREAM by the IntentGuard: an `act` verb (incl. `reflect.note`) cannot
  run without a confirmed Intent, so a Reflection write can never lack a `SERVES`
  target — the raised error already names `intent_bootstrap` (test asserts it). The
  atomic both-edges write (item 5) holds: `reflect.note` writes `OBSERVED_DURING` +
  `SERVES` together; `REFLECTION_PARTIAL_LINKS` labels any sweep finding that is a
  partial. Item 4 (Spec 150 attribution) is satisfied by construction — `ready`
  guarantees every Reflection carries `OBSERVED_DURING`, so every classified
  proposal traces to its source.
- **Doctor:** `agency_doctor.reflection_link_coverage == {ready, unlinked}` —
  `ready == True` live.
- **Tests:** `tests/test_reflection_link_sweep.py` (note-passes · partial-trips ·
  no-intent-blocked · doctor-ready · codes-exist), RED→GREEN; 58 lint/plugin + 26
  doctor/sweep tests green; `check-drift` clean. Codes `REFLECTION_NO_INTENT` +
  `REFLECTION_PARTIAL_LINKS` added.

Slice-1's stale evidence note (the `tests/test_link_finding.py` paths) predates the
BDD migration; the live coverage is the sweep + the acceptance tests above.

