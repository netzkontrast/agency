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

**Slice 2 — SHIPPED: the core SDLC develop disciplines (brainstorm · review ·
spec-panel), phase-filled (A1/A6).**

Done (file:line evidence):
- `agency/capabilities/develop/_main.py` — `brainstorm` (explore/present/confirm —
  preserving its generative `sample` + verb cues), `review` (request/dispatch/
  resolve — including inline content on the `delegate.fan_out`-bound dispatch
  phase) and `spec-panel` (review/synthesize/approve) gained full `goal`/
  `instructions`/`freedom`. Real discipline judgment (design-options-not-a-menu,
  fix-or-justify-never-performative, panel-voices-as-methods). With tdd + the Slice
  1 four, the **seven core SDLC develop disciplines are now self-contained**.
- `skills/develop/SKILL.md` — regenerated: those walk rows inline the new content
  (A2 parity).
- Tests: a Slice 2 scenario — brainstorm/review/spec-panel each pass
  `lint_skill_schema` with no `phase-self-contained` violation (rule 8). 3/3
  migration green; 62 across migration/skill_walk/develop/render; check-drift clean.

**Slice 3 — SHIPPED: the remaining develop disciplines — develop is now 16/16
self-contained (A1).**

Done (file:line evidence):
- `agency/capabilities/develop/_main.py` — `_quality_phases(decidable_verbs,
  remedy=)` is ONE shared phase-content source for the six quality modes (Spec 380;
  identical scope→decidable→judgment[Iron Law]→score-report[→remedy] shape, only
  the `analyze.*` axes differ) — the instructions live once (rule 2), not six
  near-identical copies. `plan-execute` (frame/draft-plan/plan-signoff/execute-step/
  checkpoint/synthesize, incl. the `develop.draft_plan`-bound + `dispatch_decision`
  phases) gained full inline content.
- `agency/_loop.py` — `LOOP_DESIGN_SKILL`'s seven phases (goal/verification/host/
  council/control/confirm/emit) gained `goal`/`instructions`/`freedom` grounded in
  the looper doctrine (verdict-source-per-gate, guard-free-loop-refused).
- `skills/develop/SKILL.md` — regenerated (A2 parity for all the new content).
- Tests: a Slice 3 scenario asserts EVERY develop discipline is self-contained
  (derived from the live registry — rule 8); 4/4 migration green; 69 across
  migration/skill_walk/develop/loop_wizard/render; check-drift clean.

**Enforcement blast-radius (surveyed before any block flip).** ~14 disciplines
across OTHER caps (analyze · delegate · discover · document · frugal · intent ·
jules×6 · manage · mode · panel · persona · recommend · research · select · skills ·
subagent · workflow) still lack instructions. A repo-wide block flip would break
them all, so the gate stays GRADUATED — Slice 4 widens it to block the compliant
(filled) disciplines + warn the rest; full repo-wide block waits until those caps
are migrated (the owner can drive that incrementally; the gate now surfaces them).

**Slice 4 — SHIPPED: the graduated discipline gate (block compliant, warn the tail).**

Done (file:line evidence):
- `agency/capabilities/plugin/clusters/lint.py` — `partition_discipline_lint(
  disciplines, verbs_index)` lints every discipline and partitions it: `clean`
  (self-contained AND passes), `blocked` (self-contained but FAILS another rule — a
  regression on a migrated discipline → fail the gate), `warned` (not yet
  self-contained — the migration tail, surfaced not fatal). `ok = not blocked`. The
  block set **self-widens** — a discipline joins it the moment its phases gain
  instructions (no manual list). Surfaced as `plugin.lint_disciplines()`.
- `scripts/check-drift` — new section 2c runs the gate: `blocked` → DRIFT; `clean`
  / `warned` counts printed; skips gracefully without the venv. Live: clean=16
  (all develop), warned=23 (the cross-cap tail), blocked=0.
- Tests: a Slice 4 scenario — no compliant discipline is blocked; every develop
  discipline is reported clean; the migration tail is surfaced as warnings (all
  derived from the live registry — rule 8). 5/5 migration green; 39 across
  migration/plugin/skill_lint; install regen + check-drift clean.

**Spec 378 substrate COMPLETE for the develop layer.** develop is 16/16
self-contained; the gate enforces no regression on any migrated discipline and
surfaces the 23-discipline cross-cap tail as warnings. The full repo-wide block
flip is now a mechanical follow-on (fill each warned discipline's phase
instructions — each auto-joins the gate as it lands); the owner can drive that
capability-by-capability. The legacy single-template prune is 373 Slice 3's
concern (per-type capability/discipline templates), tracked there.

**A6 demonstrated** (acceptance #2): the develop disciplines are capability-authored
richer skill data validating against the v2 schema the same as auto-derived —
no duplicated committed file (rule 2).

**Slice 5 — SHIPPED: the cross-capability "understand" cluster (gate auto-widens
beyond develop).** `code-analysis` (analyze), `critical-thinking` (intent), and
`guided-discovery` (discover) gained full inline phase content — proving the gate
mechanism is NOT develop-specific: each moved warned→clean the moment its phases
were filled, no gate edit. Gate now: clean=19, warned=20, blocked=0. A Slice 5
scenario asserts all three are reported clean (derived from the live gate — rule 8).
The remaining 20-discipline tail is the same mechanical fill, owner-drivable
capability-by-capability; each auto-joins the gate as it lands.

**Slice 6 — SHIPPED: the cross-cap dispatch cluster.** `dispatch-decision` +
`dispatching-parallel-agents` (delegate) and `subagent-driven-development`
(subagent) gained full inline phase content (the eleven-signal heuristic, fan-out/
join, spec→dispatch→review). Gate now: clean=22, warned=17, blocked=0. The
delegation/parallelism doctrine is now self-contained in the skills themselves.
