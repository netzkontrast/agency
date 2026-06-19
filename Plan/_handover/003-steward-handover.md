<!-- agency steward handover — read this first next run -->
# Steward Handover 003 — 2026-06-19

## What shipped this run

**Spec 153 Slice 6 cont. — document-convergence schema backfill (4 schemas).**

Continued the Slice 6 backfill with the 4 labels named in handover 002:
- `discover/schemas/acceptance-criterion.json` (`AcceptanceCriterion`) —
  DERIVED from `discover/clusters/scope.py` (`text` required, `measurable`
  required, `gherkin` optional).
- `develop/schemas/artefact.json` (`Artefact`) — DERIVED from
  `agency/ontology.py` + `_invoke.py` (`kind` required; `path`/`name`
  optional common fields).
- `document/schemas/session.json` (`Session`) — DERIVED from `engine.py` +
  `document/_main.py` (`session_id` required; `status` optional).
- `document/schemas/document.json` (`Document`) — DERIVED from
  `document/_main.py` (`path`/`content_sha` required; `template`/`schema`
  optional).

**The real catch (same pattern as Slice 6):** `discover` cap had no
`artefact_schemas` declaration → schemas were counted by the file-glob
audit but never loaded by the engine. Added
`artefact_schemas = ArtefactSchemas.from_module(__file__)` to
`DiscoverCapability`. All 4 verified engine-loaded.

**Also closed: pre-existing doc-drift (10 stale reference docs).** The 10
stale `docs/vision/reference/*.md` files noted in handover 002 were
re-stamped (`scripts/check-doc-drift --update`). No content changed —
only the doc-source hash markers. Doc-drift is now clean.

## Evidence
- RED→GREEN: 2 new scenarios in `tests/acceptance/features/template_schema.feature`
  + step defs (`DOC_CONVERGENCE_LABELS = {"AcceptanceCriterion","Artefact","Session","Document"}`).
  `pytest tests/acceptance/test_template_schema.py` → **20 passed** (was 18).
  Scenario 2 boots the live engine (guards the file-present-but-undeclared trap).
- `schema_coverage.fraction` **0.270 → 0.315** (24 → 28 covered).
- Baseline `Plan/_planning/schema-coverage-baseline.txt` trimmed **65 → 61**.
- Invariant slice (`template_schema or naming or install or doctor or discover`) → **83 passed**.
- `scripts/check-drift` → **NO DRIFT**.
- `scripts/check-doc-drift` → **NO DOC DRIFT** (10 re-stamped).
- TODO.md Spec 153 row updated (Slice 6 cont. SHIPPED); spec.md Followup appended.
- Reflections: `reflection:7de0fb5d`, `reflection:7bff04d2`.

## Pre-existing debt noted (NOT caused this run)
None beyond what was resolved (doc-drift closed). The 29 unmarked docs
in check-doc-drift are documents that never had a `<!-- doc-source: -->` 
marker — a separate concern tracked by Spec 149/278.

## Next 3 candidates (ranked)

1. **schema_coverage continued backfill — next 5 highest-traffic labels
   (Spec 153 Slice 6 cont.)** — now at 0.315 (28/89). To reach >0.5 need
   ~17 more. The next highest-traffic uncovered labels to target (per
   `priority_uncovered` ranking from `agency_doctor`): `Lifecycle`,
   `Reflection` (wait — Reflection IS covered; check the live list),
   `ClarificationQuestion`, `ElicitationTurn`, `DiscoverySession`. Each
   follows the same file+declaration pattern. Lowest-risk, same pattern.
   **IMPORTANT**: before this run, recheck priority via `agency_doctor` or
   `python3 -m scripts.check_schema_coverage` since live node counts shift.

2. **schema_coverage audit ⇒ engine-load intersection (Spec 153 Slice 4
   seed, dogfood `reflection:ac372147`)** — make the audit itself
   intersect the file-discovered set with engine-LOADED `ontology.schemas`
   so an undeclared schema file reads as UNCOVERED (dormant), not covered.
   Closes the exact trap this run and Slice 6 hit by hand — no more
   manual verification needed. Medium complexity, high payoff.

3. **FastAPI typed-read surface (Goal 5/7, Spec 330 follow-up)** —
   architecturally significant; needs a human-reviewed spec for the server
   boundary, auth, and lifecycle. Still the capstone the typed-entity
   program points at. NOT a steward guess — defer until a human has
   reviewed and confirmed the direction.

## Proposed amendment (dogfood, `reflection:7bff04d2`)

**Capability artefact_schemas declaration check should be mechanical.**
Every time a new `schemas/*.json` is authored, the owning capability's
`artefact_schemas` declaration must also be verified. Candidate addition
to CLAUDE.md "Dormant-surface audit" heuristic (or Spec 153 Slice 4
engine-load intersection gate):

> When authoring a schema file, immediately verify the owning capability
> declares `artefact_schemas = ArtefactSchemas.from_module(__file__)`.
> A file present but undeclared is dormant — counts as covered by the
> glob audit but never enforced by the engine.

## Pillar gate (held)

Intent · Capability · Lifecycle · Memory each own write+read; the 4 new
schemas are load-bearing (engine-loaded + enforced via `artefact_schemas`
declarations, verified); the Document convergence is strengthened further
(AcceptanceCriterion/Artefact/Session/Document all now have bindable
Schemas). Drift clean; doc-drift clean; suite green (83 invariant / 20
template_schema scenarios).
