---
spec_id: "378"
slug: capability-skill-migration
status: partial
state: draft
last_updated: 2026-06-22
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["371", "373", "374", "377"]
parent_spec: "370"
domain: skills
---

# Spec 378 — Migrate the 33 capabilities + the capability-authored path

> Child 8 of Spec 370 (the long tail). Author real v2 skill data for every existing
> capability, exercise the capability-authored path (A6), then flip the gate to
> repo-wide block.

## Why
The substrate (371–374) + enforcement (377) are inert until the existing 33
capabilities carry v2 `skill.yaml`. This slice does the migration and lands A6.

## Design (sketch)
- For each capability: run `skill.author` (374) to draft a v2 `skill.yaml`, review,
  and commit — or hand-author for the high-value ones. Pillars (375) included.
- **A6 (capability-authored skills):** prove a capability can ship/override its own
  richer skill data (e.g. `music`, `novel`, `develop`) — the schema validates it the
  same as an auto-generated one.
- Batch by cluster (Spec 047) to keep reviews coherent; each batch flips its caps
  from warn to block as it lands.
- Final: flip `check-drift`/lint to **repo-wide block** (377) once all are green;
  prune the legacy single-template path.

## Slices (TDD)
1. Migrate the substrate/meta caps (develop, plugin, intent-adjacent) + pillars.
2. Migrate the domain caps (music, novel, …) incl. an A6 hand-authored override.
3. Migrate the remainder; flip to repo-wide block; remove the legacy path.

## Acceptance
- Every capability ships a schema-valid v2 `skill.yaml`; no capability uses the
  legacy single-template fallback.
- At least one capability demonstrates A6 (a hand-authored/override skill that
  validates).
- Repo-wide lint/schema block is ON; `check-drift` green.

## Followup — Implementation Status (2026-06-22)

**APPROACH CORRECTION (owner directive 2026-06-22): A6 + phase-fill, frugal.**
The spec's literal "commit a `skill.yaml` per capability" predates 375/377 and
COLLIDES with the derive-don't-duplicate doctrine (rule 2) — capability skills
DERIVE from their module docstrings (`emit_skill`); committing 33 hand-authored
`skill.yaml` would duplicate every docstring. A6 was always the OVERRIDE escape
hatch, not a mandate. So 378 is re-scoped: keep derivation the default; author real
inline phase `instructions` (A1 self-containment) for the high-value disciplines —
that IS the capability-authored richer skill data (A6); the v2 schema validates it
the same as an auto-derived one. The committed-`skill.yaml` set stays the pillars
(375). "Repo-wide block" becomes "widen the gate as disciplines become compliant."

**Slice 1 — SHIPPED: the core develop disciplines, phase-filled (A1/A6).**

Done (file:line evidence):
- `agency/capabilities/develop/_main.py` — `debug` · `verify` · `plan` · `execute`
  gained full inline phase content (`goal`/`instructions`/`freedom`, +`example`
  where it sharpens) via the `phase()` builder, joining `tdd` (the 372 exemplar)
  and `brainstorm`'s generative phases. Real discipline judgment (systematic
  debugging, evidence-before-assertion, plan→pre-mortem→approve, executing-plans),
  not filler. Derived rendering unchanged (rule 2) — the content rides the existing
  `ontology.skills` schema, so it's A6 (capability-authored) without a duplicated
  committed file.
- `skills/develop/SKILL.md` — regenerated: the `debug`/`verify`/`plan`/`execute`
  walk rows now inline each phase's goal + instructions (A2 parity via
  `_render_phase_detail`, 373 Slice 2), same source the walker delivers.
- Tests: `tests/acceptance/features/capability_skill_migration.feature` +
  `test_capability_skill_migration.py` — (1) each core discipline passes
  `lint_skill_schema` with NO `phase-self-contained` violation (A1, via the
  `plugin.lint_skill_schema` verb, derived from the live schema — rule 8); (2) the
  rendered develop skill inlines the enriched `debug` instructions (A2 parity).
  2/2 green; 41 across migration/skill_walk/render/lint + 28 develop green;
  install regen + check-drift clean.

Still:
- **Slice 2** — the remaining develop disciplines + other meta/substrate caps;
  a domain-cap A6 exemplar (music/novel).
- **Slice 3** — widen the lint gate (377) to block the compliant disciplines
  (warn the rest); prune the legacy single-template path when all are green.
