---
spec_id: "041"
slug: implementation-discipline-skills
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [011, 012, 023, 040]
affects:
  - skills/executing-plans/SKILL.md                              # NEW skill
  - skills/subagent-driven-development/SKILL.md                  # NEW skill
  - skills/subagent-driven-development/references/implementer-prompt.md
  - skills/subagent-driven-development/references/spec-reviewer-prompt.md
  - skills/subagent-driven-development/references/code-reviewer-prompt.md
  - skills/dispatching-parallel-agents/SKILL.md                  # NEW skill
  - skills/systematic-debugging/                                  # extend existing
  - skills/systematic-debugging/scripts/find-polluter.sh          # NEW script
  - skills/systematic-debugging/references/anti-patterns.md      # NEW reference
  - skills/test-driven-development/                               # extend existing
  - skills/test-driven-development/references/testing-anti-patterns.md  # NEW reference
estimated_jules_sessions: 1
domain: meta
wave: 2
ports_from: [superpowers]
depends_on_spec_032_for: dispatch_decision-callouts
---

# Spec 041 — Implementation-Discipline Skills (Superpowers Ports)

## Why

The deep-dive analysis (PR #17 thread, second-round subagent reports)
revealed that **agency overlaps with Superpowers on 9 of 14 skills**,
but **three Superpowers skills are genuinely additive** with no agency
equivalent:

1. **`executing-plans`** — serial execution of a written plan with
   review checkpoints, alternative to subagent-driven execution.
2. **`subagent-driven-development`** — per-task subagent dispatch with
   a two-stage review (spec then code) gate. Ships three concrete
   subagent-prompt templates: `implementer-prompt.md`,
   `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`.
3. **`dispatching-parallel-agents`** — fan-out for 2+ independent
   problem domains; agency's `delegate` cap is the engine surface but
   no skill formalises the discipline.

Additionally, the analysis showed two agency skills can be **deepened**
with Superpowers material:

- `agency:systematic-debugging` lacks the `find-polluter.sh` script and
  the 3-fix-limit → architecture-escalation pattern.
- `agency:test-driven-development` lacks the `testing-anti-patterns.md`
  reference (mocking pitfalls, Red Flags rationalization table).

This spec ports all three new skills + the two deepening extensions,
**agency-flavored throughout** — every reference to a generic subagent
mechanism becomes a reference to `delegate.dispatch` (Spec 040), every
"git workspace" call lands on `workspace.baseline`, every claim about
parallelism cites the Spec-032 S4:parallel signal.

## Done When

### New skill: `executing-plans`

- [ ] `skills/executing-plans/SKILL.md` exists with the standard
  frontmatter (kebab-case name, "Use when…" trigger).
- [ ] Discipline: 5 phases — LOAD (read the plan), REVIEW (critical
  appraisal), EXECUTE (serial), CHECKPOINT (after each phase),
  FINISH (hand off to `finishing-a-development-branch` discipline).
- [ ] Hands off to `agency:branch` (the `finish` verb on the existing
  `branch` capability) — does NOT duplicate the finish flow.
- [ ] Soft-gate at checkpoint: blocks if `verification-before-completion`
  signals fail.
- [ ] Cites Spec 040 — describes when to switch from `executing-plans`
  to `subagent-driven-development` based on dispatch_decision signals.

### New skill: `subagent-driven-development`

- [ ] `skills/subagent-driven-development/SKILL.md` exists; ≤ 150 LOC.
- [ ] Discipline: EXTRACT-TASKS → for-each-task(DISPATCH-IMPL →
  SELF-REVIEW → SPEC-REVIEW → CODE-REVIEW) → FINAL-REVIEW.
- [ ] Hard gates:
  - No production code without a failing test (cites `test-driven-
    development`).
  - Two-stage review per task: spec-review BEFORE code-review.
  - Never parallelise implementer dispatch within a single feature
    (parallel dispatch is for `dispatching-parallel-agents`, not for
    serialising-within-a-plan).
- [ ] Three references portable subagent prompts:
  - `references/implementer-prompt.md` — the prompt template used to
    dispatch the per-task implementer. Carries the agency
    `intent_id` placeholder and a SERVES-discipline reminder.
  - `references/spec-reviewer-prompt.md` — first-stage reviewer
    prompt: verify the implementation matches the plan's task
    specification.
  - `references/code-reviewer-prompt.md` — second-stage reviewer
    prompt: verify code quality (calls
    `capability_analyze_run(axes=['quality','security'])` when Spec
    034 ships).
- [ ] Each prompt template is agency-flavoured: references
  `mcp__plugin_agency_agency__*` tools, `intent_id` semantics, the
  graph-vs-file doctrine.
- [ ] **Return-shape contract per template** (Wiegers — requirements
  clarity). Each prompt instructs the subagent to return a structured
  payload, not free prose. Shapes:
  - `implementer` returns
    `{intent_id, files_touched: [...], tests_added: [...], summary: str,
      next_step: "ready-for-spec-review"|"blocked"|"needs-clarification",
      blocked_reason?: str}`.
  - `spec-reviewer` returns
    `{verdict: "matches-spec"|"deviates"|"clarification-needed",
      findings: [{kind, file?, line?, evidence, severity}], summary: str,
      next_step: "ready-for-code-review"|"return-to-implementer"}`.
  - `code-reviewer` returns
    `{verdict: "approve"|"request-changes"|"reject",
      findings: [{rule, severity, file, line, message, evidence}] —
      reuses the Spec 042 Finding shape, summary: str,
      next_step: "merge-ready"|"return-to-implementer"}`.
  The orchestrator reads these structured fields; the `summary` is for
  the user, the `findings`/`next_step` drive the loop.

### New skill: `dispatching-parallel-agents`

- [ ] `skills/dispatching-parallel-agents/SKILL.md` exists; ≤ 100 LOC.
- [ ] Discipline: IDENTIFY-DOMAINS → CREATE-TASKS → DISPATCH-PARALLEL
  → REVIEW-EACH-SUMMARY → INTEGRATE.
- [ ] Soft gates: verify domain-independence before dispatch (no
  shared state, no sequential dependencies).
- [ ] Cites Spec 040's S4:parallel signal: "≥ 3 sibling tasks ⇒
  amortise dispatch overhead". Explicitly says: for 1–2 tasks,
  inline; for 3+, dispatch.
- [ ] Cross-reference to agency's `delegate.dispatch` — the engine
  surface this discipline drives.

### Extension: `systematic-debugging`

- [ ] `skills/systematic-debugging/scripts/find-polluter.sh` — ported
  from Superpowers; finds the test that pollutes shared state. Use:
  isolated test runs with timing to detect the culprit.
- [ ] `skills/systematic-debugging/references/anti-patterns.md` — new
  reference covering the Red Flags rationalization table: "this test
  is flaky" (no — it's pointing at real state); "this works locally
  but not in CI" (environment difference is a debug target); "3
  failed fix attempts" → architecture-review-escalation, not 4th
  attempt.
- [ ] SKILL.md updated with a pointer to the new script + reference.
- [ ] **Does not change** the existing 4-phase discipline (Investigate
  → Pattern → Hypothesis → Test).

### Extension: `test-driven-development`

- [ ] `skills/test-driven-development/references/testing-anti-
  patterns.md` — new reference covering: mocking-everything pitfall,
  testing-implementation-not-behaviour, brittleness-by-coupling,
  the Red Flags table (e.g. "I'll add the test after" — STOP, restart
  from RED).
- [ ] SKILL.md updated with a pointer to the new reference.

## Design

### Why port these three, not all 14 Superpowers skills

The deep-dive matrix (PR #17 second-round subagent report) shows
9 of 14 Superpowers skills have agency equivalents (brainstorming,
writing-plans, TDD, systematic-debugging, verification-before-
completion, requesting-/receiving-code-review (split agency code-
review→2 in Spec 046), writing-skills, using-superpowers, using-git-
worktrees). Of those 9, **none of the agency versions is meaningfully
shallower** — porting would be busywork.

The three skills this spec ports are agency gaps. The two extensions
add Superpowers-specific depth (scripts, anti-pattern references) to
existing agency skills without changing their phase structures.

### Agency-flavour of the prompt templates

Superpowers' `subagent-driven-development` ships three prompts that
embody the two-stage-review discipline. Porting them verbatim would
miss the agency-native dispatch shape. Each template is rewritten to:

1. Include the agency `intent_id` placeholder (`SERVES` discipline):
   ```
   You are an implementer. The intent_id is `{intent_id}` — every
   capability_*_* verb you call MUST pass this; substrate tools
   (agency_welcome, agency_install, agency_doctor) don't need it.
   ```
2. Reference `delegate.dispatch_decision` (Spec 040) for the
   sub-decision "should I further-dispatch this task?".
3. End with a structured return shape (the reviewer reads
   `summary`, `evidence`, `next_step` — not free prose).
4. NEVER instruct the implementer to call an LLM directly — the
   implementer uses agency verbs only (which themselves may dispatch
   per Spec 040's heuristic).

### `executing-plans` vs. `subagent-driven-development` — when to pick which

The choice maps directly onto Spec 040's signals:

| Signal | executing-plans | subagent-driven-development |
|---|---|---|
| S1: return tokens per task | < 5000 | ≥ 5000 |
| S4: parallel tasks | 1 (serial) | implicit-parallel via subagent isolation |
| S5: wall-clock | < 60 min | ≥ 60 min OR interactivity tolerable |
| S7: read-only | both work | both work |
| S6: mutates | both work; subagent gives review-rigor | both work |

**Default**: `executing-plans` for small features (1–5 tasks),
`subagent-driven-development` for large plans (6+ tasks) and any plan
where the reviewer pattern (catch regressions before they pile up)
buys more than its dispatch cost.

### `dispatching-parallel-agents` vs. `subagent-driven-development`

These are NOT alternatives:

- `dispatching-parallel-agents` fans out **independent problems** (a
  flaky DB test in one module + a UI regression in another) →
  parallel `delegate.dispatch`.
- `subagent-driven-development` serialises **dependent tasks** of one
  plan, each with its own review gate.

The skills explicitly cross-reference each other so the reader doesn't
conflate.

### Why scripts/, references/, schemata in agency skills

Two patterns Superpowers proved work:
1. **scripts/** — shell helpers a skill body can invoke when needed
   (e.g. `find-polluter.sh`). Agency had no script-carrying skills;
   this spec adds two (one in this spec, the visual-companion in
   Spec 046).
2. **references/** — depth-on-demand markdown (e.g.
   `testing-anti-patterns.md`). Agency already uses this in
   `plugin-development/references/`; extending TDD and debugging
   normalises the pattern.

## Files

- **Create:**
  - `skills/executing-plans/SKILL.md`
  - `skills/subagent-driven-development/SKILL.md`
  - `skills/subagent-driven-development/references/implementer-prompt.md`
  - `skills/subagent-driven-development/references/spec-reviewer-prompt.md`
  - `skills/subagent-driven-development/references/code-reviewer-prompt.md`
  - `skills/dispatching-parallel-agents/SKILL.md`
  - `skills/systematic-debugging/scripts/find-polluter.sh`
  - `skills/systematic-debugging/references/anti-patterns.md`
  - `skills/test-driven-development/references/testing-anti-patterns.md`
- **Modify:**
  - `skills/systematic-debugging/SKILL.md` — add pointer to script + ref.
  - `skills/test-driven-development/SKILL.md` — add pointer to ref.
- **Do not modify:**
  - Existing skill disciplines (phase order, hard-gates) — extensions,
    not rewrites.
  - Any agency capabilities — this is a skill-only spec.

## Open Questions

1. **Subagent-prompt template format.** Should the three templates be
   markdown (human-readable) or JSON (machine-parseable)? Lean
   markdown — they're read by the orchestrator AND by humans during
   review.
2. **Cross-spec dependency timing.** Spec 041's `code-reviewer-prompt.md`
   references `analyze.run` (Spec 042). If 034 ships later, the prompt
   has a "when 034 lands" marker. Acceptable interim solution; the
   prompt today calls `develop.review` or `code-review` skill instead.
3. **Should `dispatching-parallel-agents` be folded into `delegate`?**
   Today the engine surface is `delegate.dispatch`; the discipline
   skill explains when to use it for parallel problems. v1 keeps the
   skill separate (the engine surface and the discipline are different
   concerns). v2 may inline.
4. **Visual-companion for brainstorming** is its own spec (038) — should
   it instead land here? No — visual-companion is about brainstorming,
   not implementation execution; structurally distinct concern.

## Evidence

- Superpowers `subagent-driven-development` skill: three prompt
  references at `…/superpowers/5.1.0/skills/subagent-driven-
  development/references/{implementer,spec-reviewer,code-quality-
  reviewer}-prompt.md`. The ported templates are agency-flavoured but
  the discipline structure is identical.
- Superpowers `executing-plans` skill: 5-phase serial execution
  discipline; the alternative to subagent-driven-development.
- Superpowers `dispatching-parallel-agents`: simpler discipline (5
  phases) focused on independence verification.
- Superpowers `systematic-debugging/scripts/find-polluter.sh`,
  `references/{root-cause-tracing,condition-based-waiting,defense-in-
  depth}.md` — Superpowers has 3 references; we port only
  `anti-patterns.md` (the others are already covered by agency's
  existing systematic-debugging SKILL.md body).
- Superpowers `test-driven-development/references/testing-anti-
  patterns.md` — the mocking-pitfalls + Red Flags table.
- Spec 040 — every cross-reference to "should I dispatch?" decisions
  flows back to the 8-signal heuristic.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted; agency's 12 existing skills
remain unchanged.

### Done
- The dispatch substrate (`delegate.dispatch_decision` from Spec 040
  when it lands) is the heuristic these skills cite.
- The two skills being EXTENDED (`systematic-debugging`,
  `test-driven-development`) already ship with sound phase structures
  — this spec only adds depth.

### Still to implement
- Three new skill folders (`executing-plans`, `subagent-driven-
  development`, `dispatching-parallel-agents`) with SKILL.md.
- Three subagent-prompt templates under
  `subagent-driven-development/references/`.
- One script and one anti-patterns reference under
  `systematic-debugging/`.
- One anti-patterns reference under `test-driven-development/`.
- Pointer updates in the two extended SKILL.md bodies.

### Refinement needed
- Open Question 2 (cross-spec dependency between 033 and 034) is
  cosmetic; templates carry a forward-pointer until 034 lands.
