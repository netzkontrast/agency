---
spec: 297
title: specialist-personas-capability
status: Shipped
depends_on: [294, 295, 296]
clusters: [develop, delegate]
vision_goals: [4]
---

# Spec 297 — `persona`: specialist engineering personas, first-class

> Fourth extract→spec→reimplement slice (binding goal: all of SuperClaude as
> first-class agency).

SuperClaude ships ~14 specialist agents (architects, engineers, analysts,
mentors). Reimplemented as a native, dispatchable **persona registry** — not
ingested prompt files.

## Extracted roster (from `agents/`)

backend-architect · frontend-architect · devops-architect · system-architect ·
security-engineer · performance-engineer · quality-engineer · python-expert ·
refactoring-expert · requirements-analyst · root-cause-analyst · technical-writer
· learning-guide · socratic-mentor. (business-panel-experts → Spec 294 `panel`;
deep-research → `research`; repo-index → `document.index`.)

## Design — native registry, decidable matching, provenance

Each persona is native data: name · domain keywords · focus · signature approach.

- `persona.list()` — the roster.
- `persona.recommend(task)` — rank personas by decidable domain overlap.
- `persona.summon(persona="auto", task)` — resolve (auto = best match), compose
  a dispatch **brief** (role + focus + approach + task) for `subagent.develop` /
  the Agent tool, and record a `PersonaBrief` node SERVING the intent.

## Done-When

- [x] 14-persona native registry with domain/focus/approach.
- [x] `recommend` ranks by decidable domain overlap; `summon` resolves +
  composes a brief + records `PersonaBrief` provenance.
- [x] `PersonaBrief` node + enum; auto-registers; acceptance scenarios green.
- [ ] **Follow-up:** next SuperClaude part (own spec).

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/persona/` — `list`/`recommend`/`summon`; 14
specialist personas; `PersonaBrief` node.

**Still.** Subsequent SuperClaude parts; LLM-backed persona voices when a
backend is present.
