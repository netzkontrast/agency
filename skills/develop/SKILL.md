---
name: develop
description: "Use when building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, running a skill to its first hard gate, reloading edited capability code mid-session, or looking up code (use codegraph)."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# develop capability

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance. For ANY code lookup — where/how a symbol works, a call path X→Y, blast radius — reach for codegraph FIRST (`codegraph explore "<q>"` is the one-call primary: relevant source + call paths + impact; `codegraph node <sym|file>` for one symbol's source + caller/callee trail; `codegraph query <name>` to locate) BEFORE grep/Read — it IS the index, so a grep/Read sweep re-does its work. Full token-efficient guide: `develop.reference("codegraph")`.

## When to use

- About to implement a feature or fix without a discipline
- A new capability needing a skeleton that lints clean
- A multi-phase workflow that should pause at a human gate
- A capability was just edited or scaffolded and needs to go live without a restart
- A 'where/how does X work', call-path, or blast-radius question → `codegraph explore "<q>"` (one call), not a grep/Read sweep

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `checklist` | transform | Project a discipline (skill walk) into a step-by-step checklist. | [details](references/checklist.md) |
| `draft_plan` | act | Author a bite-sized plan as graph provenance (Spec 287; rule 2). | [details](references/draft_plan.md) |
| `estimate` | transform | Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, DECIDABLE only: no LLM, a transparent formula over the inputs you can count). | [details](references/estimate.md) |
| `index` | effect | Index a repo as a token-cheap briefing — the development-workflow entry to the indexer (Spec 292). | [details](references/index.md) |
| `maintain` | act | Drive — and AUTOLEARN — the recurring "Agency Steward" maintenance loop. | [details](references/maintain.md) |
| `mode_select` | effect | Switch session mode + record a ModeShift node (effect). | [details](references/mode_select.md) |
| `optimize_skilldoc` | act | Author an optimized functional doc — flags + candidate, NO rewrite (act). | [details](references/optimize_skilldoc.md) |
| `plan_status` | transform | Roll up a Plan's steps + completion (Spec 287) — the render-on-demand read side (rule 2). | [details](references/plan_status.md) |
| `record_authoring_outcome` | act | Record a Reflection at the end of an authoring-capabilities walk. | [details](references/record_authoring_outcome.md) |
| `record_step_outcome` | act | Mark a PlanStep's execution outcome (Spec 287). | [details](references/record_step_outcome.md) |
| `reference` | transform | Fetch a discipline's heavy how-to on demand (T3 disclosure). | [details](references/reference.md) |
| `reload` | effect | Reload edited capability code into the live session (effect). | [details](references/reload.md) |
| `remediate` | effect | Apply the remedy phase of a prior review — safe fixes auto-applied, risky ones reported as gated (MUTATES → role=effect). | [details](references/remediate.md) |
| `review` | transform | Diagnose code decay using the brooks Iron Law — INTERACTIVE (transform). | [details](references/review.md) |
| `scaffold_capability` | act | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. | [details](references/scaffold_capability.md) |
| `session_check` | transform | Read the current SessionLifecycle state (transform). | [details](references/session_check.md) |
| `session_init` | act | Mint a SessionLifecycle SERVING the intent, detect mode, and suggest the first verb. | [details](references/session_init.md) |
| `session_resume` | transform | Spec 114 Slice 2 — cross-session handoff. | [details](references/session_resume.md) |
| `skill_walk` | act | Walk a registered skill to the first hard gate in ONE call (the atomic walker). | [details](references/skill_walk.md) |
| `validate_skill` | transform | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. | [details](references/validate_skill.md) |

## Example

```bash
await call_tool('capability_develop_checklist', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Writing implementation before a failing test → walk capability_develop_skill_walk with tdd
- Hand-rolling a capability skeleton → use capability_develop_scaffold_capability
- Restarting the session to pick up a capability edit → develop.reload re-imports it in place
- grep/Read loop to understand code while `.codegraph/` exists → `codegraph explore` already indexed it (`develop.reference("codegraph")`)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`authoring-capabilities`** (authoring): research → scaffold → author → lint → token-check → commit
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'authoring-capabilities', 'inputs': {}, 'intent_id': '…'})`
- **`brainstorm`** (discipline): explore → present → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'brainstorm', 'inputs': {}, 'intent_id': '…'})`
  1. **explore** — Surface the sharpest open questions and the load-bearing assumptions.
     List the questions whose answers would CHANGE the design, and name the assumptions the plan rests on. When a sampling host is bound the engine drafts the questions — refine them, don't rubber-stamp; the assumptions are yours to state.
  2. **present** — Present 2–3 design options with their tradeoffs.
     For each viable approach, state the tradeoff and the second-order consequence; steelman the one you'd reject. Recommend one — a brainstorm ends in a direction, not a menu.
  3. **confirm** — Get the owner's design decision before building.
     Present the recommendation and proceed ONLY on explicit confirmation. The design call is the owner's, not the agent's.
- **`debug`** (discipline): gather → hypothesize → trace → fix
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'debug', 'inputs': {}, 'intent_id': '…'})`
  1. **gather** — Collect the hard evidence before theorising.
     Capture the exact error, the input that triggers it, and the last known-good state. REPRODUCE it deterministically — a bug you can't reproduce, you can't fix. Read the full stack/output; don't skim.
  2. **hypothesize** — Form ONE falsifiable hypothesis about the cause.
     From the evidence, state a single most-likely cause and what you'd EXPECT to observe if it's true. One hypothesis at a time — resist shotgun fixes.
  3. **trace** — Confirm or refute the hypothesis at its site.
     Follow the data/call path to where the hypothesis predicts the fault. Prove it with a probe (a log line, a focused assertion) — don't guess. If refuted, return to hypothesize.
  4. **fix** — Fix behind a failing test that reproduces the bug.
     Write a failing test that reproduces the bug FIRST, then fix the root cause (not the symptom). Confirm the new test passes AND the suite stays green. Confirm this gate only on green.
- **`execute`** (discipline): load → execute → checkpoint → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'execute', 'inputs': {}, 'intent_id': '…'})`
  1. **load** — Load the written plan and restate the next step.
     Read the plan + its steps; restate the NEXT step's goal and acceptance in your own words before touching code, so you execute against the plan, not your memory of it.
  2. **execute** — Do exactly ONE step, scoped.
     Implement a single step; keep the change scoped to it (no drive-by edits). Capture what it produced for the checkpoint.
  3. **checkpoint** — Review the step against its goal before moving on.
     Compare the step's result to its stated acceptance. If it drifted, fix before the next step. Confirm the gate only when the step genuinely met its goal.
  4. **verify** — Run the full verification across all steps.
     Run the whole verification (tests + the plan's acceptance checks). Confirm every step's acceptance holds — COMPLETED is not done until the evidence is green.
- **`loop-design`** (discipline): goal → verification → host → council → control → confirm → emit
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'loop-design', 'inputs': {}, 'intent_id': '…'})`
- **`plan`** (discipline): map → self-review → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plan', 'inputs': {}, 'intent_id': '…'})`
  1. **map** — Decompose the work into ordered steps + the files each touches.
     Break the goal into the smallest ordered steps that each produce a checkable deliverable; name the files/symbols each step changes. Use intent.decompose to surface the structure.
  2. **self-review** — Pre-mortem the plan and close the gaps.
     Ask where this plan would FAIL (premortem) and what must NOT break (inversion). Add the missing steps / guards the review surfaces before committing to it.
  3. **approve** — Get explicit sign-off before execution.
     Present the plan and proceed ONLY on the owner's explicit confirmation. A plan is a proposal until approved.
- **`plan-execute`** (discipline): frame → draft-plan → plan-signoff → execute-step → checkpoint → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plan-execute', 'inputs': {}, 'intent_id': '…'})`
- **`quality-audit`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-audit', 'inputs': {}, 'intent_id': '…'})`
- **`quality-debt`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-debt', 'inputs': {}, 'intent_id': '…'})`
- **`quality-health`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-health', 'inputs': {}, 'intent_id': '…'})`
- **`quality-review`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-review', 'inputs': {}, 'intent_id': '…'})`
- **`quality-sweep`** (discipline): scope → decidable → judgment → score-report → remedy
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-sweep', 'inputs': {}, 'intent_id': '…'})`
- **`quality-test`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-test', 'inputs': {}, 'intent_id': '…'})`
- **`review`** (discipline): request → dispatch → resolve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'review', 'inputs': {}, 'intent_id': '…'})`
  1. **request** — Frame what to review and gather the diff.
     State the scope and the acceptance to review AGAINST, then collect the diff + context the reviewer needs. A review with no stated bar drifts into bikeshedding.
  2. **dispatch** — Dispatch a reviewer over the diff.
     The walker dispatches a reviewer via delegate.fan_out (a child Lifecycle + Invocation); with no driver it degrades to a document phase. Review for correctness first, then the Iron Law (over-engineering, duplication).
  3. **resolve** — Work through the findings with technical rigor.
     Triage each finding; FIX it or justify skipping with a technical reason — never performative agreement. Confirm this gate only when every blocking finding is addressed.
- **`session-driver-pass`** (workflow): init → mode-select → work-loop → synthesize → archive
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'session-driver-pass', 'inputs': {}, 'intent_id': '…'})`
- **`spec-panel`** (discipline): review → synthesize → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'spec-panel', 'inputs': {}, 'intent_id': '…'})`
  1. **review** — Convene the expert panel over the spec.
     Run the critical-thinking methods as panel voices — steelman the design, list its assumptions, pre-mortem its failure modes — and capture each expert's findings against the spec.
  2. **synthesize** — Fold the findings into a revised spec.
     Resolve the panel's findings into concrete spec edits; where experts disagree, weigh the tradeoff and decide. The output is a sharper spec, not a list of comments.
  3. **approve** — Owner sign-off on the revised spec.
     Present the revised spec and proceed ONLY on explicit confirmation.
- **`tdd`** (discipline): red → green → refactor → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'tdd', 'inputs': {}, 'intent_id': '…'})`
  1. **red** — Write ONE failing test that pins the behaviour before any production code.
     State the behaviour as a single, clearly-named test. Use real calls, not mocks. Run it and watch it FAIL for the right reason (feature missing, not a typo). If it passes, you are testing existing behaviour — fix the test.
  2. **green** — Write the simplest code that makes the failing test pass.
     Implement the minimum to go green — no extra features, no refactor yet (YAGNI). Re-run the test; it must pass.
  3. **refactor** — Clean up while staying green.
     Remove duplication, improve names, extract helpers. Keep every test green; add no new behaviour.
  4. **verify** — Confirm the suite is green before claiming the phase done.
     Run the focused slice, then the suite. Read the output — it must be pristine (no errors/warnings). Confirm this gate ONLY when tests actually pass; COMPLETED != done.
- **`verify`** (discipline): identify → run → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'verify', 'inputs': {}, 'intent_id': '…'})`
  1. **identify** — Name the exact check that proves the change works.
     State the single command or observation whose result is the acceptance evidence (the test, the run, the API call). Pick the check that would FAIL if the change were wrong.
  2. **run** — Run the check and capture its full output.
     Execute it and keep the COMPLETE output — never truncate the tail (a dropped error is a missed failure). Don't interpret yet; just capture.
  3. **confirm** — Confirm the output matches the expectation.
     Read the captured output against what success looks like. Confirm this gate ONLY when it actually matches — evidence before assertion; COMPLETED is not done.
