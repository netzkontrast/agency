---
spec_id: "071"
slug: skill-surface-reconciliation
status: draft
state: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
fulfils: "CORE.md §Skills — 'one name per skill across both surfaces'"
depends_on: ["067", "072"]
affects:
  - agency/capabilities/*/                 # ontology.skills keys
  - skills/                                 # SKILL.md folder names
  - tests/test_skill_surface.py             # NEW
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 071 — Skill-surface reconciliation (one name per skill)

## Why

A skill name lives on TWO surfaces — the `ontology.skills` key (walkable Lifecycle
template) and the `skills/<name>/SKILL.md` folder (marketplace doc) — and they
diverge: `tdd` ↔ `test-driven-development`, `plan` ↔ `writing-plans`, `review` ↔
`code-review` (only ~7 of 21 match, Spec 049 §6b). Knowing one name doesn't let
you guess the other — a pure readability tax. CORE.md §Skills (Spec 072) sets the
canonical direction: **one name per skill across both surfaces**. Spec 067's
`skill_name_parity` rule flags the divergences. This spec reconciles them.

## Done When

- [ ] **Decide the canonical name per divergent skill** (record the verdict): the
  default is the SKILL.md folder kebab name (the marketplace-facing one), with the
  ontology key aliased to match — UNLESS the short ontology key is clearly better
  (`tdd`), in which case the folder is the alias. One canonical name, documented.
- [ ] **Alias the old name** for one minor (a walker that requests the old
  ontology key, or a marketplace install of the old folder name, still resolves).
- [ ] Spec 067 `skill_name_parity` goes GREEN, then flips to BLOCK.
- [ ] `tests/test_skill_surface.py`: every ontology key has a matching folder (or a
  recorded alias); the old name still resolves for one minor.
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean.

## Migration

Alias old skill names one minor (both the ontology key and the folder lookup),
deprecate next minor. Walkers, the install regen, and docs move in lock-step.

## Evidence

- `Plan/049-…/naming-audit-report.md` §6b (the divergence list).
- `CORE.md` §Skills (the canonical-name direction); Spec 067 `skill_name_parity`.

## Followup — Implementation Status (2026-06-12)

**Verdict:** Drafted (backlog / WARN-accepted / cluster-master). Tracked
in TODO.md's Verdicts row; no Slice 1 commitment beyond the spec body.
For the autonomous-completion goal stop condition (2), this spec is
classified as drafted-by-doctrine, not pending-implementation.

