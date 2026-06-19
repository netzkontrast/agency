<!-- agency steward handover — read this first next run -->
# Steward Handover 004 — 2026-06-19

## What shipped this run

**Spec 153 Slice 6 cont. — workflow-spine schema backfill (5 schemas).**

Targeted the four-pillar surface gap — labels covering all four concepts:

- `develop/schemas/lifecycle.json` (`Lifecycle`) — the Lifecycle pillar's
  own node type; DERIVED from `agency/lifecycle.py`
  (`state` A2A-enum, `phase` int).
- `develop/schemas/event.json` (`Event`) — substrate hook events
  (Spec 076); DERIVED from `agency/engine.py`
  (`name`/`session` required; `tool`/`summary` optional).
- `skills/schemas/phase.json` (`Phase`) — skill-walk phase node; DERIVED
  from `agency/skill.py` + `skills/_main.py`
  (`skill`/`index`/`name` required; `produces` optional).
- `skills/schemas/skill.json` (`Skill`) — Capability pillar skill-surface
  node; DERIVED from `agency/skill.py`
  (`name`/`kind` enum usage|discipline required).
- `discover/schemas/clarification-question.json` (`ClarificationQuestion`)
  — discover/clarify node (Spec 311); DERIVED from
  `discover/clusters/clarify.py` + `discover/ontology.py`
  (`text`/`options`/`ambiguity_kind` required; `status` optional).

**Engine-load fix (skills cap):** `SkillsCapability` had no `schemas/`
directory and no `artefact_schemas` declaration. Created the directory,
added `ArtefactSchemas` to the import, and added
`artefact_schemas = ArtefactSchemas.from_module(__file__)` to the class.
This is the **third time** this trap has occurred across Slice 6 batches —
a strong signal for Slice 4's engine-load intersection gate.

**doc-drift:** `docs/vision/reference/skills.md` went stale immediately
after the `artefact_schemas` addition to `SkillsCapability`. Caught by
`check-doc-drift` and re-stamped in the same PR.

## Evidence

- RED→GREEN: 2 new scenarios in `template_schema.feature`
  + step defs (`WORKFLOW_SPINE_LABELS = {"Lifecycle","Event","Phase","Skill","ClarificationQuestion"}`).
  `python3 -m pytest tests/acceptance/test_template_schema.py` → **22 passed** (was 20).
  Scenario 2 boots the live engine (guards the file-present-but-undeclared trap).
- `schema_coverage.fraction` **0.315 → 0.371** (28 → 33 covered of 89).
- Baseline `Plan/_planning/schema-coverage-baseline.txt` trimmed **61 → 56**.
- Invariant slice (template_schema + naming + install + doctor + discover + skills)
  → **114 passed**.
- `scripts/check-drift` → **NO DRIFT**.
- `scripts/check-doc-drift` → **NO DOC DRIFT** (skills.md re-stamped).
- TODO.md Spec 153 row updated (Slice 6 workflow-spine wave SHIPPED);
  spec.md Followup appended.
- Reflections: `reflection:0871ddf5`, `reflection:14588b5e`,
  `reflection:a291028c`, `reflection:16fdf144`.

## Pre-existing debt noted (NOT caused this run)

None beyond what was resolved (doc-drift closed immediately).

## Next 3 candidates (ranked)

1. **schema_coverage continued backfill — next 5 labels: discover wave
   (Spec 153 Slice 6 cont.)** — now at 0.371 (33/89). Next highest-impact
   uncovered labels to clear the discover cap's remaining gaps:
   `FeasibilitySignal`, `IntentRefinement`, `ScopeBoundary` (discover).
   Plus 2 substrate-adjacent ones: `PromptFramework` (prompt cap —
   already has `artefact_schemas`), `Template` (document cap — already has
   `artefact_schemas`). Same pattern as this run. Lowest-risk.
   **IMPORTANT**: run `agency_doctor schema_coverage` first to confirm
   `priority_uncovered` ranking — node counts shift with usage.

2. **Spec 153 Slice 4 — engine-load intersection gate** — make the audit
   itself flag file-present-but-undeclared as UNCOVERED (not covered).
   Would close the recurring trap that has bitten three Slice 6 batches.
   Medium complexity, high payoff: catches regressions mechanically.
   Approach: `audit_schemas()` gains an optional `engine_loaded_titles`
   param; covered = schemas ∩ ontology ∩ engine_loaded; undeclared files
   show in a new `dormant_schemas` set. The Slice 2 baseline gate runs
   against the tighter covered set.

3. **FastAPI typed-read surface (Goal 5/7, Spec 330 follow-up)** —
   architecturally significant; needs a human-reviewed spec for server
   boundary, auth, and lifecycle. Still the capstone the typed-entity
   program points at. NOT a steward guess — defer until a human has
   reviewed and confirmed the direction.

## Proposed amendment (dogfood, `reflection:14588b5e`)

**Add mechanical `artefact_schemas` check to the drift gate.**
The recurring trap (file present, cap undeclared → glob counts as covered,
engine never loads) has now occurred 3 times. Candidate addition to
`scripts/check-drift` or Spec 153 Slice 4:

> For every `capabilities/<name>/schemas/*.json`, assert that
> `capabilities/<name>/_main.py` (or its cluster files) contains
> `artefact_schemas = ArtefactSchemas.from_module(`. Flag any schema
> whose cap lacks the declaration as DORMANT.

## Pillar gate (held)

Intent (intent.json/invocation.json covered) · Capability (skill.json/phase.json
now covered; Lifecycle node covered) · Lifecycle (Lifecycle.json shipped — the
pillar's OWN node type is now schema-bound) · Memory (session.json covered;
Event.json shipped — substrate hooks recorded).

The Document convergence is now 33/89: ArtefactSchemas declared on
develop/intent/gate/research/document/workspace/jules/discover/plugin/branch/
delegate/reflect/subagent/skills (14 caps). Drift clean; doc-drift clean;
22 acceptance scenarios green.
