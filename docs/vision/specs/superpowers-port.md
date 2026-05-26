---
slug: superpowers-port
type: roadmap
status: draft
summary: DRAFT — what a COMPLETE port of the superpowers plugin into Agency looks like. Maps every superpowers skill (14 + the using-superpowers meta-skill + its reference files) to an Agency target — a gated `develop` skill, a capability verb, or a composition — with porting approach, status, and CORE fidelity. The thesis: superpowers' system-prompt pressure becomes Agency's STRUCTURAL enforcement (ordered phases + hard gates + judgment-as-code), and discovery becomes code-mode.
---

# Porting superpowers into Agency (draft)

## What "a complete port" means

superpowers is, at heart, **process discipline delivered as documents** that lean
on system-prompt pressure ("you MUST invoke the skill", rationalization tables,
the Iron Law). Agency delivers process discipline as **walkable, gated Lifecycle
templates recorded as provenance**, where the discipline is enforced *structurally*
(phase ordering + hard gates + judgment-as-code) rather than by exhortation.

A complete port therefore means: **every superpowers skill is reachable in Agency**
as one of —
- **a `develop` skill** (a gated phase-graph) — for pure disciplines;
- **a capability verb** — for the skills that *do* something (worktrees, branches);
- **a composition** over existing capabilities (esp. `delegate`) — for the
  subagent/review skills;
- **the engine itself** — for the discovery meta-skill.

…and that the *pressure machinery* (red-flag tables, rationalization tables) is
re-expressed as **gates and checks**, not prose.

## Porting principles

1. **Discipline → gated skill.** A superpowers discipline becomes a skill schema:
   ordered phases, each declaring required `produces`, ending in a hard gate. The
   "Iron Law" pattern (can't reach phase N+1 until phase N produced its outputs)
   is the structural enforcement — already proven in `tdd` (RED→GREEN) and
   `skill-creation`.
2. **Rationalizations → checks.** A skill's "red flags / rationalization table"
   becomes a `transform` verb that returns violations (judgment-as-code), like
   `plugin.lint_skill`. The model can't rationalize past a failing check.
3. **Discovery → code-mode.** `using-superpowers` ("find and invoke the right
   skill before acting") maps to the engine contract: `search` finds skills/verbs,
   `get_schema` discloses them, and walking a skill records the choice as
   provenance. "Invoke before acting" becomes "the action IS a recorded skill walk".
4. **Subagent skills → `delegate`.** Anything that spawns/uses subagents ports onto
   the `delegate` capability (child Lifecycles + quota + join), with the reviewer/
   worker as the driver.
5. **Side-effecting skills → `effect` capabilities.** Worktrees and branch
   finishing become real `effect` verbs with before/after evidence in Memory.
6. **References travel.** A skill's `references/` (heavy how-to) become capability
   reference docs or T3 progressive-disclosure files, loaded on demand.

## The complete mapping

| superpowers skill | kind | Agency target | approach | status |
|---|---|---|---|---|
| using-superpowers | meta | the **engine** — `search`/`get_schema`/`execute` + the `help` macroskill map | discovery is the contract; skill use is a recorded walk | **done (engine)** |
| writing-skills | act/process | `plugin.author_skill` + `lint_skill` + the `skill-creation` skill + `skill_generator` | CSO rules as `lint_skill`; Iron Law as phase ordering | **done** |
| test-driven-development | process | `develop` skill `tdd` (RED→GREEN→REFACTOR→verify gate) | gated phase-graph; ordering = Iron Law | **done** |
| systematic-debugging | process | `develop` skill `debug` | gated phase-graph | **done** |
| verification-before-completion | transform/process | `develop` skill `verify` | gated phase-graph | **done** |
| brainstorming | process | `develop` skill `brainstorm` | gated phase-graph | **done** |
| writing-plans | act | `develop` skill `plan` | gated phase-graph | **done** |
| requesting-code-review | effect | `develop` skill `review` **+** `delegate` (dispatch a reviewer) | compose: review skill drives `delegate.fan_out` to a reviewer | **partial** (skill done; reviewer dispatch TODO) |
| receiving-code-review | transform | folded into the `review` skill (assess/resolve phases) | gated phase-graph | **partial** |
| dispatching-parallel-agents | agent | `delegate.fan_out` (child Lifecycles + quota + join) | the capability | **done** |
| subagent-driven-development | process | composition: `delegate` (per-task child) + `gate` (spec-review then quality-review) | a skill template over `delegate` + the planned `gate` | **planned** (needs `gate`) |
| executing-plans | process | a `develop` skill `execute` that walks a plan's steps with review checkpoints | skill walker over plan steps + gates | **planned** |
| using-git-worktrees | effect | a new **`workspace`** capability (`isolate`/`baseline`) | `effect` verbs; records the workspace + baseline-test result | **new** |
| finishing-a-development-branch | effect | a new **`branch`** capability (`finish`: merge/PR/keep/discard) | `effect` verbs over git/GitHub; records the outcome | **new** |
| writing-skills refs (`testing-skills-with-subagents.md`, `persuasion-principles.md`, `anthropic-best-practices.md`) | reference | capability reference docs under the `plugin`/`develop` capabilities | T3 references, loaded on demand | **planned** |

(Private-journal — a separate plugin — already has its Agency analog in the
`reflect` capability; not part of superpowers proper.)

## Net-new work the complete port requires

1. **`gate` capability** — extract the hard-gate predicate as a reusable
   `transform` (pass/fail + evidence). Unblocks `subagent-driven-development`'s
   two-stage (spec then quality) review and a verified `delegate.join`.
2. **`workspace` capability** (`effect`) — `isolate` (worktree/branch) + `baseline`
   (run tests, record the green baseline) — the using-git-worktrees discipline.
3. **`branch` capability** (`effect`) — `finish` (detect state → merge / open PR /
   keep / discard) — the finishing-a-development-branch discipline.
4. **Bind `develop` skills to verbs.** Today the 7 dev skills are document-only
   phase-graphs. The complete port binds phases to real verbs where one exists
   (e.g. `review`'s dispatch phase → `delegate`; `verify`'s run phase → a test
   runner), so walking the skill *executes*, not just *documents*.
5. **Reviewer/worker drivers for `delegate`** — a local-subagent driver so
   requesting-code-review and subagent-driven-development have a real backend.
6. **Skill references** — carry the heavy how-to files as capability references.

## What deliberately does NOT port

- **System-prompt pressure** ("you MUST", red-flag prose, the EXTREMELY-IMPORTANT
  block). Agency replaces exhortation with **structure**: a discipline you can't
  short-circuit because the phase ordering + hard gates + checks won't let you.
  The rationalization tables become test fixtures / lint rules.
- **The "invoke the skill before responding" reflex.** In Agency the unit of work
  is already a recorded skill walk / capability invocation; there is no separate
  "did you remember to use the skill?" layer.

## Build order

- **Phase 1:** `gate` capability (unblocks the rest). Bind `review`/`verify` dev
  skills to verbs.
- **Phase 2:** `workspace` + `branch` effect capabilities (worktrees, branch finish).
- **Phase 3:** `subagent-driven-development` + `executing-plans` as skill templates
  composing `delegate` + `gate`; add a local-subagent `delegate` driver.
- **Phase 4:** carry skill references; document the discovery mapping in `help`.

## CORE fidelity

Every ported unit stays the open role-tagged craft; code-mode remains the only
contract; each is provenance (a recorded skill walk or Invocation that SERVES the
intent); disciplines own their skill schemas via `OntologyExtension`. Nothing
re-introduces a dropped idea.

> Draft. Each phase runs the design loop (brainstorm → research → design →
> spec-panel → review) before it lands, per [EXTENSION-PLAN.md](../../EXTENSION-PLAN.md).
