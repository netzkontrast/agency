---
spec_id: "363"
slug: phase-skill-schema
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["152", "286"]
parent_spec: "362"
domain: skills
---

# Spec 363 — The powerful, layered Phase + Skill schema (the data model)

> Child 1 of the Spec 362 program. The foundation everything else builds on: a
> typed, validated, committed `Skill`/`Phase` schema rich enough to express the
> R1–A7 best-practices (`Plan/362-…/reference/SKILL-BEST-PRACTICES.md`).

## Why
Today a phase is `{index,name,produces,gate?,verbs?,sample?,…}` (no content) and a
skill is `{name,description,body}` (enforces nothing). Neither can hold a good
skill. This slice defines the data model; 364–370 consume it.

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
