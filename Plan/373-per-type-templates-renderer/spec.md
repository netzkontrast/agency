---
spec_id: "373"
slug: per-type-templates-renderer
status: draft
last_updated: 2026-06-20
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
