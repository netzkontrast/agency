---
capability: workspace
pillar: lifecycle
vision_goals: [2, 3]
status: living
last_generated: 2026-06-19
sources: [18]
---

# workspace — Workspace isolates work in a git worktree and records a green baseline, so risky changes start from a clean, provably-green point that recovery can return to (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Workspace isolates work in a git worktree and records a green baseline, so risky changes start from a clean provably-green point that recovery can return to without touching the main working tree.

## Verbs (generated · 2)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `workspace.baseline` | effect | **vcs** · **workspace** · **command** | Run the baseline test command in the workspace and record the green/red result. |
| `workspace.isolate` | effect | **vcs** · **branch** · base | Create an isolated git worktree on a fresh branch off `base`; record the Workspace. |

## Ontology (generated)

**Nodes:** `Workspace`(path, branch, base) · `Baseline`(command, passed)
**Edges:** `BASELINED`

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/workspace -->
