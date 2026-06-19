<!-- agency steward handover — read this first next run -->
# Steward Handover 002 — 2026-06-19

## What shipped this run
**Spec 153 Slice 6 — backfill the highest-traffic provenance-spine schemas.**

Authored 5 JSON schemas (title = ontology label, properties DERIVED from the
live node-creation sites, not invented), one per highest-traffic uncovered
label the doctor's `priority_uncovered` ranked:
- `agency/capabilities/intent/schemas/intent.json` (`Intent`) ← `agency/intent.py`
- `agency/capabilities/intent/schemas/invocation.json` (`Invocation`) ← `agency/_invoke.py`
- `agency/capabilities/jules/schemas/agent.json` (`Agent`) ← `_invoke`/`lifecycle`/`delegate`
- `agency/capabilities/develop/schemas/maintenance-run.json` (`MaintenanceRun`) ← `develop._main`
- `agency/capabilities/gate/schemas/gate.json` (`Gate`) ← `gate._main`/`_substrate_tools`

**The real catch (not just file authoring):** the file-glob coverage audit
(`schema_paths`) counts a `schemas/*.json` as covered even when the owning
capability never declares `artefact_schemas` — so the **engine never loads or
enforces it**. `intent` and `develop` caps lacked the declaration; I added
`artefact_schemas = ArtefactSchemas.from_module(__file__)` to both. Verified all
5 now live in `Engine().ontology.schemas`.

**Why (impact ranking):** handover 001's ranked candidate #2. Bounded, testable,
strengthens the Document-convergence pillar (a Document `CONFORMS_TO` a Schema),
and reclaims the highest-traffic dormant labels first. #1 (FastAPI surface) was
deferred per the rail — architecturally significant, needs a human-reviewed spec.

## Evidence
- RED→GREEN: 2 new scenarios in `tests/acceptance/features/template_schema.feature`
  + step defs. `pytest tests/acceptance/test_template_schema.py` → **18 passed**
  (was 16). Scenario 2 boots the live engine to guard the
  file-present-but-undeclared dormant trap.
- `schema_coverage.fraction` **0.213 → 0.270** (19 → 24 covered); core set
  `{Intent, Agent, Invocation, MaintenanceRun, Gate}` all covered AND engine-loaded.
- Baseline `Plan/_planning/schema-coverage-baseline.txt` trimmed **70 → 65**
  (the live-baseline invariant scenario enforces the trim — no drift).
- Invariant slice (`-k "template_schema or naming or install or drift or surface
  or doctor"`) → **63 passed**.
- `scripts/check-drift` → **NO DRIFT** (schemas load at bootstrap; install regen
  produces no diff — no wire-surface change).
- TODO.md Spec 153 row updated (Slice 6 SHIPPED); spec.md Followup appended.
- Reflection + dogfood observation `reflection:ac372147` recorded.

## Pre-existing debt noted (NOT caused this run)
`scripts/check-doc-drift` flags 7 stale `docs/vision/reference/*.md` — confirmed
identical on the base commit (stash-diff), so this slice added ZERO new doc drift.
The CI doc-drift step is WARN-only ("Does not fail"). A future run should
re-stamp them (`scripts/check-doc-drift --update`) as a dedicated docs slice.

## Next 3 candidates (ranked)
1. **schema_coverage to >0.5 + re-floor (Spec 153 Slice 6 cont.)** — continue the
   backfill with the next highest-traffic uncovered labels
   (AcceptanceCriterion / Artefact / Session / Document); then promote the audit
   to a monotone floor gate. Bounded, same pattern as this run — lowest-risk.
2. **schema_coverage audit ⇒ engine-load intersection (Spec 153 Slice 4 seed,
   dogfood `reflection:ac372147`).** The audit over-counts undeclared schema
   files as covered. Make the audit (or doctor) intersect file-discovered schemas
   with engine-LOADED `ontology.schemas` so an undeclared file reads as uncovered
   (dormant), not covered. Closes the exact trap this run hit by hand. Medium.
3. **FastAPI read surface (Goal 5/7)** — still the capstone the typed-entity
   program points at; STILL needs a human-reviewed spec for the server boundary,
   auth, lifecycle. Highest reach, but a decision, not a steward guess.

## Proposed amendment (dogfood)
Coverage audits that walk FILES must intersect with the engine's LOADED set —
a "covered" file that no capability declares is dormant surface, not coverage.
Candidate addition to CLAUDE.md heuristic "Dormant-surface audit" / the Spec 153
audit definition (recorded as `reflection:ac372147`).

## Pillar gate (held)
Intent · Capability · Lifecycle · Memory each own write+read; the 5 new schemas
are load-bearing (engine-loaded + enforced, verified — no dormant surface); the
Document convergence is strengthened (5 more labels now have a bindable Schema).
Drift clean; suite green.
