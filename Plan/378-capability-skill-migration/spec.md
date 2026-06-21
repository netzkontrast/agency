---
spec_id: "378"
slug: capability-skill-migration
status: draft
last_updated: 2026-06-20
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
