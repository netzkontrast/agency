---
capability: branch
pillar: lifecycle
vision_goals: [2, 3]
status: living
last_generated: 2026-06-19
sources: [18]
---

# branch — Branch inspects the working tree and remote state and finishes the branch the appropriate way — merge when clean, a PR when review is needed, or a clear report of what blocks completion (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Branch detects working-tree and remote state then finishes the branch the appropriate way — commit when clean, open a PR when review is needed, or report what blocks — so development work lands decisively and provably.

## Verbs (generated · 3)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `branch.assess` | transform | **vcs** · **branch** · base | Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard. |
| `branch.commit_smart` | transform | **summary** · paths | Compose a conventional-commit message from a change summary + the changed paths |
| `branch.finish` | effect | **vcs** · **branch** · **action** · base | Finish the branch by the chosen action (merge/pr/keep/discard); record the outcome. |

## Ontology (generated)

**Nodes:** `BranchOutcome`(branch, action, ok)

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/branch -->
