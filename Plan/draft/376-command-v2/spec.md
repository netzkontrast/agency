---
spec_id: "376"
slug: command-v2
status: partial
state: draft
last_updated: 2026-06-22
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

## Followup — Implementation Status (2026-06-22)

**SHIPPED (both slices): the curated selector + the launch-not-stub body.**

The "explosion" the owner wanted gone was the *identical-stub* nature (every
`/agency-<skill>` repeated the same "drive develop.skill_walk" body), not the
count — so the top-N alpha cap (`AGENCY_SKILL_CMD_TOP_N=12`) is replaced by a
principled selector (kind ∈ {discipline, pillar}) where each body LAUNCHES its
skill. Slices 1 + 2 are coupled (a selector that picks pillars but keeps the walk
body would ship a "walk this pillar" lie), so they landed together.

Done (file:line evidence):
- `agency/install.py` — `_CURATED_COMMAND_KINDS = ("discipline", "pillar")` (with an
  `AGENCY-DRIFT` tag) replaces `AGENCY_SKILL_CMD_TOP_N`. `_generate_per_skill_commands`
  now reads `_all_skills(reg)` (the unified listing incl. pillars, Spec 375) and emits
  one `commands/agency-<slug>.md` per discipline + per pillar — the entry commands
  (`agency`, `agency-onboard`) keep their slug. `_discipline_command` inlines the
  phase chain from the live schema and invokes `develop.skill_walk`; `_pillar_command`
  points at the self-contained concept `skills/<slug>/SKILL.md` (a pillar has no phases
  to walk). Bodies are schema-derived ⇒ each differs (no identical stubs) and never
  drifts from its skill. `_prune_orphans` gains a `commands/agency-*.md` block so a
  removed/renamed discipline's command is auto-pruned (the top-N→curated migration
  pruned 8 stale non-curated commands: adr-usage, album-concept, authoring-capabilities,
  branch-usage, character-architect, config-usage, critical-thinking-pass,
  developmental-editor).
- Live counts: 39 disciplines + 3 pillars = 42 per-skill commands (+ the 3 entry
  commands). The set is computed from the live registry — no pinned count (rule 8).
- Tests: `tests/acceptance/features/command_v2.feature` + `test_command_v2.py` — 5
  scenarios: (1) the per-skill command slugs are EXACTLY the discipline+pillar skills
  (no non-curated kind leaks); (2) every discipline command invokes the walk + names
  its real skill; (3) every pillar command points at its concept SKILL.md; (4) no two
  per-skill bodies are byte-identical (no stubs); (5) determinism. All derive from
  `_all_skills` (rule 8). 5/5 command_v2 + 32 across command/install/pillar green;
  install regen (42 commands, 8 pruned) + check-drift clean.
