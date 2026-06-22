---
spec: 299
title: superclaude-coverage-map
status: Shipped (mapping complete; reimplementations tracked in 294-298)
state: done
depends_on: [294, 295, 296, 297, 298]
clusters: [develop]
vision_goals: [4]
---

# Spec 299 — SuperClaude → agency: complete first-class coverage map

> Capstone of the binding goal: *extract, design, implement ALL of SuperClaude
> as first-class agency*. Every SuperClaude command, mode, and agent is either
> **reimplemented** as a native capability (Specs 294-298) or **mapped** to a
> pre-existing first-class agency capability. Nothing is left as an ingested
> prompt "port".

## Net-new reimplementations (this goal)

| Spec | SuperClaude part | Agency capability |
|---|---|---|
| 294 | Business Panel (mode + experts) | `panel` (9 experts · 3 modes) |
| 295 | Behavioral Modes (5) | `mode` (detect/activate postures) |
| 296 | `sc-select-tool` | `select` (approach archetype routing) |
| 297 | Specialist agents (14) | `persona` (registry · recommend · summon) |
| 298 | `sc-recommend` | `recommend` (registry-driven routing) |

## Commands (33) → agency home

| SuperClaude command | Agency first-class home |
|---|---|
| sc-analyze | `analyze` |
| sc-brainstorm | `mode.brainstorming` (295) + `brainstorm` skill |
| sc-build | `develop` (scaffold_capability / implement skill) |
| sc-business-panel | **`panel`** (294) |
| sc-cleanup | `analyze` + `persona.refactoring-expert` (297) |
| sc-design | `brainstorm` + `spec-panel` + `persona.system-architect` |
| sc-document | `document` |
| sc-estimate | `develop.estimate` |
| sc-explain | `document.explain` |
| sc-git | `branch` (commit_smart / finish_branch) |
| sc-help | `help` / `agency_welcome` |
| sc-implement | `develop` (implement discipline) |
| sc-improve | `analyze` + `persona.refactoring-expert` |
| sc-index / sc-index-repo | `document.index` / `document.index_repo` |
| sc-load | `develop.session_resume` |
| sc-pm | `mode.orchestration` (295) + `develop` plan-execute |
| sc-recommend | **`recommend`** (298) |
| sc-reflect | `reflect` |
| sc-research | `research` |
| sc-save | `develop.session_init` / `session_check` |
| sc-sc | dispatcher → `agency_welcome` / `recommend` |
| sc-select-tool | **`select`** (296) |
| sc-spawn | `subagent.develop` / `delegate.fan_out` |
| sc-spec-panel | `spec-panel` |
| sc-task | `delegate` + `develop` plan-execute |
| sc-test | `develop.test` |
| sc-troubleshoot | `debug`/`systematic-debugging` skill + `persona.root-cause-analyst` |
| sc-workflow | `develop` plan-execute |
| setup-mcp | `agency install` |
| verify-mcp | `agency_doctor` |
| sc-agent | `subagent` + `persona` (297) |
| sc-README / sc-help | docs / `help` |

## Modes (7) → agency home

| SuperClaude mode | Agency home |
|---|---|
| Brainstorming | **`mode.brainstorming`** (295) |
| Business_Panel | **`panel`** (294) |
| DeepResearch | `research` + `deep-research` skill |
| Introspection | **`mode.introspection`** (295) |
| Orchestration | **`mode.orchestration`** (295) |
| Task_Management | **`mode.task_management`** (295) |
| Token_Efficiency | **`mode.token_efficiency`** (295) |

## Agents (≈22 functional) → agency home

14 specialist engineering agents → **`persona`** (297). business-panel-experts →
**`panel`** (294). deep-research(-agent) → `research`. repo-index → `document.index`.
pm-agent → `mode.orchestration` + `develop` plan-execute. self-review →
`code-review` skill + `verification-before-completion`. ContextEngineering / README
→ docs (non-functional).

## Done-When

- [x] Every SuperClaude command mapped to a first-class agency home.
- [x] Every SuperClaude mode mapped (5 reimplemented in 295; 2 to existing caps).
- [x] Every functional agent mapped (14 → `persona`; rest → existing caps).
- [x] All five net-new reimplementations shipped + tested (294-298).
- [x] No remaining "port" surface (the ingest-as-Documents scaffolding was
  removed; reimplementations are native capabilities).

## Followup — Implementation Status (2026-06-16)

**Done.** Five native capabilities (`panel`/`mode`/`select`/`persona`/`recommend`)
+ this complete mapping. Every SuperClaude part is first-class agency — either a
new capability or a pre-existing one. The binding goal is satisfied: SuperClaude
is reimplemented, not ported.

**Refinement (future).** Some mapped commands lean on disciplines/skills rather
than dedicated verbs (sc-cleanup/improve/design); promote to dedicated verbs only
if dogfooding shows the skill route is friction.
