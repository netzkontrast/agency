---
spec: 301
title: superpowers-coverage-and-extension
status: Partial (Slice 1 shipped)
state: done
depends_on: [294, 295, 296, 297, 298, 300]
clusters: [develop]
vision_goals: [4]
---

# Spec 301 — superpowers → agency: coverage + extend the SuperClaude caps

> User directive: apply the same extract→spec→reimplement loop to **superpowers**,
> and **extend the SuperClaude-reimplemented capabilities** with what superpowers
> offers.

## Superpowers → agency (already first-class)

Agency was built on the superpowers pattern, so its 14 disciplines are already
first-class agency **skills** (walkable disciplines on capabilities):

| Superpowers skill | Agency home |
|---|---|
| using-superpowers | `using-agency` skill |
| brainstorming | `develop.brainstorm` discipline |
| writing-plans | `develop.plan` / `writing-plans` skill |
| executing-plans | `develop` plan-execute (Spec 287) |
| test-driven-development | `develop.tdd` discipline |
| systematic-debugging | `develop.debug` discipline |
| verification-before-completion | `verification-before-completion` skill |
| requesting/receiving-code-review | `code-review` skill |
| writing-skills | `skill-creation` / `skill_generator` |
| subagent-driven-development | `subagent` capability + skill |
| dispatching-parallel-agents | `delegate.fan_out` + `dispatch-decision` |
| using-git-worktrees | `workspace.isolate` |
| finishing-a-development-branch | `branch.finish_branch` |

So superpowers needs no *new* port — it is the substrate's own discipline layer.

## Extension — superpowers' gift applied to the SuperClaude caps

Superpowers' signature is **skills-as-walkable-disciplines** (phases + hard
gates). The SuperClaude reimplementations (294-298) were flat verb sets; this
spec gives them disciplines:

- `panel` → **`strategic-analysis`** discipline: frame → convene → challenge →
  synthesize (hard gate). Multi-expert analysis becomes a guided walk.
- `persona` → **`specialist-dispatch`** discipline: match → brief → dispatch →
  verify (hard gate). Wraps specialist dispatch in subagent-driven-development +
  verification-before-completion.

Both are walkable via `develop.skill_walk` and pause at their hard gate — the
superpowers discipline shape, native.

## Done-When

- [x] Superpowers' 14 disciplines mapped to their agency homes.
- [x] `panel` gains a walkable `strategic-analysis` discipline (gated).
- [x] `persona` gains a walkable `specialist-dispatch` discipline (gated).
- [x] Both walk to their hard gate via `develop.skill_walk`; scenarios green.
- [ ] **Follow-up:** disciplines for `mode`/`select`/`recommend` where a guided
  walk adds value; wire `verification-before-completion` into the new caps'
  effect verbs.

## Followup — Implementation Status (2026-06-16)

**Done.** Superpowers coverage map + two walkable disciplines extending the
SuperClaude capabilities with the superpowers skills-as-disciplines pattern.

**Still.** Disciplines for the remaining new caps; deeper verification wiring.
