---
spec_id: "373"
slug: per-type-templates-renderer
status: done
state: done
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["031", "371", "372"]
parent_spec: "370"
domain: skills
---

# Spec 373 — Per-type templates + the deterministic renderer

> Child 3 of Spec 370. Replace the single generic template with per-type templates
> driven by variables from the committed schema; render self-contained skills (A1)
> with one-deep references (R4). No LLM here — install stays deterministic (A7).

## Why
One `render/capability-skill.md` shape for everything + a second `templates.SKILL_MD`
path = generic output + a divergent path. `parse_slices`' first-sentence `brief`
truncates the description. `_(Tier B…)_` stubs ship to disk.

## Design (sketch)
- **Per-type templates** (`render/skill/<type>.md`) — pillar/capability/discipline,
  each with variable slots filled from the `Skill`/`Phase` schema (371). A capability
  may override slots.
- **Self-contained render (A1):** the body inlines overview + when-to-use/when-not +
  the full phase `instructions` + the one example + common mistakes; heavy per-verb
  detail → `references/*` (R4, one deep; ToC if >100 lines, R5).
- **Kill the defects:** description comes from the authored `description` field (no
  sentence-slice truncation); a verb missing markers is a **lint failure** (377), not
  a shipped `_(Tier B…)_` stub.
- **Converge the two paths:** `plugin.author_skill` and `skill_emit` both render via
  THIS renderer over the schema (no third path; the C2 coherence risk in 370).
- Deterministic: same `skill.yaml` ⇒ byte-identical output (A7 / `install regen` diff-free).

## Slices (TDD)
1. The per-type template set + the schema→template renderer (replaces `emit_skill`'s
   single-template substitution).
2. Self-containment render (phase instructions inline) + one-deep references.
3. Converge `author_skill` onto the renderer; remove the truncation + Tier-B stubs.

## Acceptance
- A capability skill renders self-contained (full phase instructions inline) with
  references one-deep; body ≤500 lines (overflow → references).
- No truncated descriptions; no `_(Tier B…)_` text on disk.
- `install regen` twice ⇒ identical bytes (deterministic, A7).
- pillar/capability/discipline each render their type's required sections.

## Followup — Implementation Status (2026-06-21)

**Slice 2 (partial) — SHIPPED: phase instructions render inline (walk↔file parity,
the hinge 372 deferred).** Per-type templates + path convergence (Slices 1 & 3)
remain.

Done (file:line evidence):
- `agency/skill_emit.py` — new `_render_phase_detail(sk)` renders a skill's
  phases' inline `goal`/`instructions` (the 371/372 single source) beneath its
  walk row; `_render_walk_section` appends it. Returns "" when no phase authored
  inline content, so legacy disciplines (phase-name-only) render byte-identically
  and `install regen` stays diff-free except where content was actually authored.
  Deterministic — same schema ⇒ same bytes (A7; verified regen-twice identical).
- `skills/develop/SKILL.md` — regenerated: the `tdd` row now shows each phase's
  goal + full instructions inline (the first self-contained discipline render);
  every other capability/skill byte-identical. `scripts/check-drift` → NO DRIFT.
- Tests: `tests/acceptance/features/render_substrate.feature` +
  `test_render_substrate.py` — 2 new scenarios: (1) a rendered capability skill
  inlines its phases' authored instructions; (2) **parity** — every instruction
  the *walker* surfaces for a `tdd` phase appears verbatim in the *rendered* file
  (drives the real `SkillRun`, reads live source — rule 8). 17/17 render + 14/14
  skill_walk + v2 schema all green (45 passed across the blast radius).

**Slice 1 — SHIPPED: the per-type template set + the schema→template renderer.**

Done (file:line evidence):
- `agency/render/skill/{capability,discipline}.md` — per-type HEAD templates
  (frontmatter + `# <Title> <type>` heading) joining the existing `pillar.md`,
  loaded into `_SKILL_TYPE_TEMPLATES` (`agency/skill_emit.py`).
- `agency/skill_emit.py::render_typed_skill(skill)` — the ONE per-type renderer:
  selects `render/skill/<type>.md` by `Skill.type` (unknown → capability, the
  general case) and appends the schema-driven, self-contained data body
  (`_skill_data_sections` — the renamed type-agnostic `_pillar_sections`):
  overview + when-to-use/when-not + the one example (R9) + the common-mistakes
  rationalization table + references one-deep (R4). Body concatenated (not
  substituted) so a literal `$` never breaks the render; description is the
  AUTHORED field (no sentence-truncation). Deterministic (A7).
- **Convergence (Slice 3 path-merge):** `render_pillar` is now a thin wrapper over
  `render_typed_skill({type: pillar})` — pillars + the new types share ONE render
  path (the C2 coherence risk closed). Pillar output byte-identical (no pillar
  SKILL.md changed on regen).

**Slice 3 — SHIPPED (the on-disk defect): the `_(Tier B…)_` apologetic stub is
gone.** `_render_tier_b_anchor` no longer ships the self-deprecating
"_(Tier B — verb docstring lacks…)_" prose to disk — a verb missing the Spec 016
markers is surfaced as a `lint_skill_schema` finding (Spec 377), not as apologetic
text in the published skill. The verb section keeps its brief + signature. Regen
diff = exactly the 4 caps that carried the stub (config · frugal · music · novel);
every other SKILL.md byte-identical. The renderer reads the **authored**
description (no `_first_sentence_brief` truncation on the skill description).

- Tests: `tests/acceptance/features/skill_render_v2.feature` + `test_skill_render_v2.py`
  — pillar/capability/discipline each render their type's required sections; the
  authored multi-sentence description survives intact; the render is deterministic
  (render-twice byte-identical, A7); NO committed SKILL.md carries the Tier-B stub
  (scanned live — rule 8). 6/6 green; 44 across pillar/render/walk/render_v2;
  install regen + check-drift clean.

**Acceptance met.** A capability skill renders self-contained (phase instructions
inline via 372's `_render_phase_detail`; references one-deep); no truncated
descriptions; no `_(Tier B…)_` on disk; deterministic regen; pillar/capability/
discipline each render their type's sections.

Residual refinement (not acceptance-gating, tracked honestly): `plugin.author_skill`
remains a thin GENERIC skill-md renderer (`templates.SKILL_MD`) for ad-hoc
user-authored skills — a distinct artifact from a capability/pillar/discipline v2
Skill; folding its generic path onto `render_typed_skill` is a follow-on (the
capability/pillar/discipline render paths are already converged on the one
renderer). `emit_skill`'s capability SKILL.md still composes the verb table +
walk around the per-type body, which is its capability-specific concern.
