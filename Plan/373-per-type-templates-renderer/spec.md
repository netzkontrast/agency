---
spec_id: "373"
slug: per-type-templates-renderer
status: partial
last_updated: 2026-06-21
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

Still:
- **Slice 1 — per-type templates** (`render/skill/<type>.md` for
  pillar/capability/discipline driven by the 371 `Skill.type`), replacing the
  single `capability-skill.md` substitution.
- **Slice 3 — converge the two render paths** (`plugin.author_skill` via
  `templates.SKILL_MD` onto the same renderer) and kill the defects
  (`_first_sentence_brief` description truncation; the `_(Tier B…)_` on-disk
  stub → a lint failure per 377).
- Self-containment beyond the walk section (overview / when-to-use / when-not /
  one example / common-mistakes inline; references one-deep, R4) — the rest of
  Slice 2.
