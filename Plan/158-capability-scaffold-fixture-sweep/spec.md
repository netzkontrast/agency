---
spec_id: "158"
slug: capability-scaffold-fixture-sweep
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "024"
depends_on: ["024", "016", "054", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/*/  (scaffold markers)
  - scripts/check-drift
  - tests/test_scaffold_markers.py   # Slice 1 SHIPPED 2026-06-12 (replaces planned test_scaffold_sweep.py)
---

# Spec 158 — Capability scaffold + fixture sweep

## Why

Spec 024 (capability-authoring-discipline) is Partial — block-mode lint
fires only when `# agency-scaffold: v1` is present, and its Followup
names the remaining task: "Sweep of existing capabilities for marker
addition". Spec 016's Phase 5 fixture cleanup is also Partial. Both are
mechanical sweeps that should be DONE and then GUARDED so new
capabilities can't ship without the marker (the drop-in-capability bar,
CLAUDE.md).

## Done When

- [ ] **Every capability carries `# agency-scaffold: v1`** (sweep),
      so block-mode lint (Spec 024) applies uniformly.
- [ ] **`scripts/check-drift` gains a marker-presence check** (Spec 054
      family) — a new `capabilities/<name>/` with no scaffold marker
      fails CI. Returns typed `ScaffoldReport{capabilities_total: int,
      capabilities_marked: int, unmarked: list[str],
      orphan_fixtures: list[Path]}`.
- [ ] **Spec 016 Phase-5 fixture cleanup completed** — orphan fixtures
      removed (derived inventory, not a hand list).
- [ ] **Measurable invariants** (rule 8):
      (a) `capabilities_marked == capabilities_total` (no unmarked,
      ever — closed set, no monotone floor needed once green);
      (b) `len(orphan_fixtures) == 0` against the live capability set
      — a fixture without a matching capability fails CI;
      (c) every capability with `# agency-scaffold: v1` exposes the
      block-mode lint contract (verb count, ontology presence,
      docstring shape) — marker presence implies lint applicability;
      (d) the unmarked inventory is DERIVED on every check run, never
      a checked-in list (rule 8 — no pinned counts).
- [ ] Test: a capability fixture missing the marker trips check-drift;
      the live sweep reports 0 unmarked.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a new capability `agency/capabilities/example/_main.py` is added
        without `# agency-scaffold: v1` at the top of the module
When:   scripts/check-drift runs in CI
Then:   ScaffoldReport.unmarked == ["example"];
        check-drift exits 1 with Codes.SCAFFOLD_MARKER_MISSING;
        PR blocked; reviewer prompted to add the marker

Given:  tests/fixtures/old_capability/ remains after the capability was deleted
When:   scripts/check-drift runs
Then:   ScaffoldReport.orphan_fixtures contains the path;
        check-drift exits 1 with Codes.FIXTURE_ORPHAN
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Marker copy-paste lies | marker present, capability shape broken | invariant (c) — marker implies lint pass | block-mode lint AFTER marker check, not because of it |
| Sweep drifts post-rename | capability renamed; fixture path stale | derive inventory each run (invariant d) | `scripts/check-drift` recomputes, never reads a snapshot |
| New `v2` marker breaks old caps | future tightening invalidates v1 | open-question 1 — backfill v1, reserve v2 | additive only; v2 implies v1; never silent drop of v1 |

## Interconnects

- **Drift-derivation chain** (149): the unmarked-capability inventory is
  derived.
- Spec 016 (authoring doctrine) is the parent discipline.
- Spec 054 (drift management) hosts the new check.
- Spec 151 (Codes coverage) supplies `Codes.SCAFFOLD_MARKER_MISSING`
  and `Codes.FIXTURE_ORPHAN`.
- Spec 157 (architecture-drift gate) consumes the scaffold marker as
  one of its standing invariants — marker presence implies architecture
  compliance.
- Spec 153 (schema coverage) shares the "every capability has X" sweep
  posture — schemas + markers tracked uniformly.

## Open questions

1. Backfill `v1` or introduce `v2` with stricter rules? **Recommend**:
   backfill `v1` (matches existing lint), reserve `v2` for a future
   tightening.
2. Where does the orphan-fixture inventory live? **Recommend**: derived
   per-run from `glob(tests/fixtures/*) - live capability set`; never a
   checked-in allowlist.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

The typed shape this spec carries was shipped as part of the wave-1+2
batch (intents trackable in graph). See TODO.md row + the corresponding
test module under `tests/`.

