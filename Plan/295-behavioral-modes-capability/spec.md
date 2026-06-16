---
spec: 295
title: behavioral-modes-capability
status: Partial (Slice 1 shipped)
depends_on: [294]
clusters: [thinking, develop]
vision_goals: [4]
---

# Spec 295 — `mode`: SuperClaude behavioral modes, first-class

> Second extract→spec→reimplement slice (after Spec 294 `panel`).

SuperClaude's distinctive **behavioral modes** — postures that change *how* the
agent operates — reimplemented as a native, decidable agency capability. Agency
had no first-class "mode" concept; modes are now provenance (a `ModeActivation`
node records which posture a session adopted, and why).

## Extracted understanding (from `modes/MODE_*.md`)

Five core behavioral modes (Business Panel is already Spec 294's `panel`;
Deep Research maps to the existing `research` capability):

| Mode | Posture | Decidable triggers |
|---|---|---|
| `brainstorming` | collaborative discovery — Socratic, surface hidden requirements, don't assume | brainstorm, explore, "not sure", maybe, vague, idea, "thinking about" |
| `introspection` | meta-cognitive self-analysis — expose reasoning chain, question own logic | "analyze my reasoning", reflect, why, unexpected, error, recurring |
| `orchestration` | tool/resource optimization — pick the strongest tool, parallelize | multi-tool, parallel, performance, resource, routing, coordinate |
| `task_management` | hierarchical multi-step — decompose into phases, persist state | phases, dependencies, refine, polish, "multi-step", delegate |
| `token_efficiency` | compressed output — symbols, abbreviation, 30-50% reduction | --uc, ultracompressed, brevity, large-scale, "context high" |

## Design — decidable, provenance-recording

`mode` follows the `panel`/`thinking` pattern: decidable, no LLM.

- `mode.list()` — the roster (name · purpose · behaviors · triggers · flags).
- `mode.detect(context)` — score each mode by trigger-term overlap; returns
  ranked matches (read-only).
- `mode.activate(mode="auto", context="")` — resolves the mode (auto = top
  `detect`), returns its **behavioral rules** (the posture to adopt), and
  records a `ModeActivation` node SERVING the intent. So a session's adopted
  postures are queryable (e.g. via `manage.timeline`).

## Done-When

- [x] 5-mode roster with purpose + behaviors + triggers + flags.
- [x] `detect` ranks modes by decidable trigger overlap.
- [x] `activate` resolves (auto or explicit), returns posture rules, records a
  `ModeActivation` node + enum; auto-registers.
- [x] Acceptance scenarios (roster, auto-detect per trigger, activation
  provenance).
- [ ] **Follow-up:** the next SuperClaude part (own spec). Optional: surface
  `mode.activate` via the UserPromptSubmit injection so a detected posture is
  auto-suggested.

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/mode/` — `list`/`detect`/`activate`; 5 modes;
`ModeActivation` node + `(ModeActivation, mode)` enum.

**Still.** Injection hook-up + subsequent SuperClaude parts.
