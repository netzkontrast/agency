---
spec_id: "377"
slug: skill-lint-enforcement
status: partial
state: draft
last_updated: 2026-06-22
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["032", "054", "371", "373"]
parent_spec: "370"
domain: skills
---

# Spec 377 — Strict per-type lint + schema enforcement (graduated)

> Child 7 of Spec 370. Make the contract enforceable: per-type schema + the new
> quality rules gate generation, graduated warn→block so the existing 33 don't all
> break at once.

## Why
`lint_skill_doc` checks the description/triggers/example shape but passes thin
bodies, stub sections, and missing phase instructions. The schema (`skill-md.json`)
enforces nothing. So low-quality skills ship.

## Design (sketch)
- Extend `lint_skill_doc` with **per-type completeness** (each `type`'s required
  sections present), **self-containment** (every phase has non-empty `instructions`,
  A1), **no-stub** (no `_(Tier B…)_` text), **verb-resolves** (every referenced verb
  exists), and the R1/R3/R4 checks (description-when-not-what, ≤500 lines, refs
  one-deep).
- Validate the `Skill`/`Phase` schema (371) at `install.generate` AND in
  `check-drift` (Spec 054).
- **Graduated rollout** (Spec 032 `AGENCY_BOOTSTRAP_LINT={strict,warn,off}` precedent):
  warn repo-wide; **block** for new/changed skills + the pillars (375) + frugal as
  first exemplars; flip to repo-wide block when 378 finishes the 33.
- Rewrite `docs/vision/SKILL-CONTRACT.md` → v2 (the R1–A7 contract).

## Slices (TDD)
1. The per-type + self-containment + no-stub + verb-resolves lint rules.
2. Schema validation wired into `install.generate` + `check-drift`; the graduated
   warn/block gate.
3. `SKILL-CONTRACT.md` v2.

## Acceptance
- A thin/stub/non-self-contained skill FAILS lint (was passing).
- New/changed skills + pillars + frugal are blocked on failure; legacy caps warn.
- `check-drift` validates every committed `skill.yaml` against the schema.

## Followup — Implementation Status (2026-06-22)

**Slice 1 — SHIPPED: the strict per-type + self-containment + no-stub +
verb-resolves lint rules.** Slices 2 (wire into install.generate + check-drift,
graduated warn/block) and 3 (SKILL-CONTRACT.md v2) remain.

Done (file:line evidence):
- `agency/capabilities/plugin/clusters/lint.py` — `lint_skill_schema(skill,
  verbs_index=None)` validates a 371 Skill dict beyond the SkillDoc shape:
  ``schema`` (via `parse_skill` — structure AND per-type completeness, the R15
  required core; a schema failure short-circuits), ``description-trigger-first``
  (R1 — 'Use when…'), ``phase-self-contained`` (A1 — every phase carries non-empty
  `instructions`), ``no-stub`` (no `(Tier B…)` placeholder), ``verb-resolves`` (a
  phase's `invoke` binding names a LIVE verb — scoped to `invoke`, the executable
  contract; the loose advisory `verbs` list is NOT strictly resolved because it
  legitimately names skills/methods like `develop.brainstorm`, not just verbs —
  avoids false positives). Surfaced as `plugin.lint_skill_schema(skill)` (role=
  transform), which builds `verbs_index` from the live registry.
- Tests: `tests/acceptance/features/skill_lint.feature` + `test_skill_lint.py` — 5
  scenarios: 4 crafted fail cases (one per rule: thin-technique → schema;
  tier-b-stub → no-stub; no-instructions → phase-self-contained; bad-verb →
  verb-resolves) + the live PASS exemplar (every committed pillar passes strict
  lint, derived from `load_pillars()`, rule 8). 5/5 green; 31 across
  skill_lint/plugin_authoring; install regen (the new verb's wrapper + reference +
  help entry) clean.

Still:
- **Slice 2** — validate the `Skill`/`Phase` schema at `install.generate` AND in
  `check-drift`; the graduated `warn`→`block` gate (warn repo-wide; block for
  new/changed skills + pillars + frugal first; flip to repo-wide block when 378
  finishes the legacy caps). Self-containment will warn on the 39 legacy
  disciplines (their phases carry no `instructions` yet) until 378 fills them.
- **Slice 3** — `docs/vision/SKILL-CONTRACT.md` v2 (the R1–A7 contract).
