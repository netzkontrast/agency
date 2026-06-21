---
spec_id: "376"
slug: command-v2
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1]
depends_on: ["148", "371", "373"]
parent_spec: "370"
domain: skills
---

# Spec 376 — Command v2 (curated, launch-not-stub)

> Child 6 of Spec 370. Rethink the generated slash-commands: a curated few that
> each LAUNCH their skill, instead of the top-12 near-identical "walk the skill"
> stubs.

## Why
`_generate_per_skill_commands` emits up to 12 `/agency-<skill>` commands, each a
fixed stub repeating the same "drive develop.skill_walk" body. That is the command
explosion the owner wants gone.

## Design (sketch)
- **Curated set:** `/agency`, `/agency-onboard`, `/help` + one command per
  **discipline** skill + one per **pillar** (intent/lifecycle/memory). The rest are
  discoverable via `agency search` — no per-every-skill command.
- **Launch-not-stub:** each command body launches its skill — for a read-only host it
  points at the self-contained SKILL.md (A1); for a skill-walk host it invokes the
  walk. Generated from the same schema (371) so the command and its skill never drift.
- Replace `_generate_per_skill_commands`' top-N loop with a curated selector keyed on
  `type ∈ {discipline, pillar}`.

## Slices (TDD)
1. The curated command selector (discipline + pillar, not top-N).
2. The launch-not-stub command body (read-only path + walk path), rendered from schema.

## Acceptance
- The generated command set = entry (3) + one per discipline + one per pillar; no
  `/agency-<every-capability>` commands.
- A command body launches its skill (no identical-stub duplication); it references a
  real skill that exists.
