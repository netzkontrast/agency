---
spec_id: "377"
slug: skill-lint-enforcement
status: draft
state: draft
last_updated: 2026-06-20
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
