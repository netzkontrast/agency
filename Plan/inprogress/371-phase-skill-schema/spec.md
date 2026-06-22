---
spec_id: "371"
slug: phase-skill-schema
status: partial
state: inprogress
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["152", "286"]
parent_spec: "370"
domain: skills
---

# Spec 371 — The powerful, layered Phase + Skill schema (the data model)

> Child 1 of the Spec 370 program. The foundation everything else builds on: a
> typed, validated, committed `Skill`/`Phase` schema rich enough to express the
> R1–A7 best-practices (`Plan/370-…/reference/SKILL-BEST-PRACTICES.md`).

## Why
Today a phase is `{index,name,produces,gate?,verbs?,sample?,…}` (no content) and a
skill is `{name,description,body}` (enforces nothing). Neither can hold a good
skill. This slice defines the data model; 372–378 consume it.

## Design (sketch)
- **`Phase`** gains content fields: `goal` (one line), `instructions` (the inline
  steps a read-only agent follows — A1/A2), `example` (R9), `done_when`, plus a
  per-phase `freedom` level (R8). Existing structural fields (`produces`, `verbs`,
  `gate`, `invoke`, `sample`, `requires_input`) preserved (back-compat — new fields
  optional at first).
- **`Skill`** = `{name, type, owner, description, overview, when_to_use, when_not,
  phases:[Phase], references:[{path,title}], common_mistakes:[{symptom,counter}],
  examples:[{input,output}], eval_scenarios?, source_stamp}` where
  `type ∈ pillar|capability|technique|pattern|reference|discipline` (R15),
  `owner ∈ auto|capability` (A6), each field tagged `source ∈ derived|authored|sampled`
  (A4/A5).
- **Layered:** a small required core per `type` (the rest optional) so the schema is
  powerful without being gold-plated (frugal floor).
- **Committed location:** `agency/capabilities/<cap>/skill.yaml` (the drop-in folder
  carries its skill data); pillars + capability-authored skills (A6) use the same.
- **Typed parse:** extend `_skill_parse.py` to validate against the new JSON schemas
  with typed `Codes.*` (Spec 152 boundary), so a malformed skill fails fast.
- JSON schemas under `agency/capabilities/plugin/schemas/` (replace the trivial
  `skill-md.json`): `phase.schema.json`, `skill.schema.json`, per-type required-sets.

## Slices (TDD)
1. The `Phase` + `Skill` JSON schemas + `parse_skill` validation (typed codes).
2. The per-capability `skill.yaml` loader + back-compat shim (a cap with no
   `skill.yaml` derives a minimal one from today's SkillDoc, so nothing breaks).
3. The `source`/`owner`/`source_stamp` metadata fields + a read API.

## Acceptance
- A `skill.yaml` with phases-carrying-`instructions` round-trips through `parse_skill`.
- A malformed skill (missing a per-type required section) fails with a typed code.
- Back-compat: every existing capability still produces a valid (minimal) Skill.
- The schema can express each R1–A7 field (a coverage test maps rule → field).

## Followup — Implementation Status (2026-06-21)

**Slice 1 — SHIPPED.** The v2 layered `Phase`+`Skill` schema is the data model
372–378 consume.

Done (file:line evidence):
- `agency/_skill_parse.py` — `Phase` gains inline content (`goal`,
  `instructions`, `example`, `done_when`, `freedom`) (A1/A2/R8/R9); `Skill`
  gains the best-practices structure (`type`, `owner`, `description`,
  `overview`, `when_to_use`, `when_not`, `references`, `common_mistakes`,
  `examples`, `eval_scenarios`, `source_stamp`) (R1/R15/A4/A6). All fields are
  optional on the dataclass; both `to_dict()` round-trips preserve them.
- Vocabulary: `_SKILL_TYPES` (R15: pillar|capability|technique|pattern|
  reference|discipline), `_OWNERS` (auto|capability), `_FREEDOM` (high|medium|
  low), `_TYPE_REQUIRED` (the layered per-type required CORE).
- `parse_phase` validates `freedom` (closed enum → `PHASE_UNKNOWN_KIND`) +
  the optional content strings; `parse_skill` validates `type`/`owner` (closed
  enums → `SKILL_PARSE_INVALID`), the v2 strings, and the dict-list fields
  (`references`/`common_mistakes`/`examples`/`eval_scenarios` via the new
  `_parse_dict_list` helper). The per-type required CORE is enforced **only**
  when a `type` is declared — legacy skills (no `type`) keep the name+kind
  floor (back-compat).
- Published JSON schemas: `agency/capabilities/plugin/schemas/phase-schema.json`
  + `skill-schema.json` (named to avoid the `skills` cap's graph-node
  `phase`/`skill` schemas + the kebab-stem loader rule). They are
  non-dormant (read by the acceptance suite).
- Tests: `tests/acceptance/features/skill_schema_v2.feature` +
  `test_skill_schema_v2.py` (14 scenarios) — phase round-trip, per-type
  required failures, unknown type/owner/freedom, full round-trip, back-compat,
  live-ontology-clean, R1–A7 rule→field coverage, JSON-schema declaration.
  Existing `test_skill_phase_parse.py` (+ skill_walk / skills_registry /
  skill_generator) stay green; `install regen` clean; schemas non-dormant.

Still (this spec's later slices):
- Slice 2 — the per-capability `skill.yaml` loader + back-compat shim (a cap
  with no `skill.yaml` derives a minimal Skill from today's SkillDoc).
- Slice 3 — the `source`/`owner`/`source_stamp` metadata read API.

Note: the `kind` axis (walk-shape) is kept REQUIRED for back-compat and is
orthogonal to `type` (the R15 classification) — no cross-check between them.
