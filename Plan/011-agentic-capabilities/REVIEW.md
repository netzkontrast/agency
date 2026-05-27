# REVIEW — Spec 011 Agentic Capabilities (spec-panel)

Reviewers (simulated): Wiegers (requirements), Adzic (executable examples), Fowler
(interface/duplication), Nygard (failure modes/wiring), Cockburn (actor/goal),
Crispin (testability). Grounded in the real source — every correction cites
`path:line`.

---

## Verdict

**APPROVE WITH MUST-FIX (status: keep `draft`).** The spec is unusually
well-grounded: it correctly reads Agency's composition surface, the four decidable
`agentic` verbs are genuinely decidable, and the decision to *not* edit any engine
file is **correct** (see below — the file the research proposed editing does not
even exist). The `pressure` framework is a faithful port of Plan 133's pure rubric.

But two things are not yet real: (1) `pressure.run` asserts a **"transcript"**
concept that exists nowhere in Agency — neither `delegate.fan_out` nor the only
LLM-bearing driver (`jules`) produces one, so the wet path is undefined, not merely
unwired; and (2) the `agentic` ontology extension is internally inconsistent about
whether invariants are core `Gate`s or new `Invariant` nodes. Both are fixable in
the spec without touching the engine. There is also real, unacknowledged overlap
with `develop`'s already-shipped `testing-skills` reference and `review` discipline.

Quality scores: grounding 9/10 · decidability 8/10 · wiring-honesty 5/10 ·
duplication-awareness 6/10 · testability 8/10.

---

## Source-grounded corrections (path:line)

1. **"leaves `core.py` untouched" — `core.py` never existed.** Spec L199, L204,
   L223 and the migration table treat avoiding a `core.py` edit as a live design
   choice. The engine has **no `core.py` and no `core/` package**; the substrate is
   `agency/engine.py` + `agency/capability.py` (`ls agency/agency/*.py`). The
   `core.py` edit comes from the *research* draft
   (`research/capability-specs/specs/agentic.md:8` `affects: agency/core.py`,
   and "Modify: `agency/core.py`"). **Fix:** reword to "the research draft proposed
   a `core.py`/middleware edit against a file that does not exist; the depth guard
   already lives in `CapabilityContext.spawn` (`agency/capability.py:49-55`,
   `MAX_DEPTH=16` at `:47`), so no engine edit is needed." Avoiding the edit is the
   right call, but the spec must not imply `core.py` is a real file it is sparing.

2. **`pressure.run` "captures the transcript" — there is no transcript anywhere.**
   Spec L82-85, L160, L197. `delegate.fan_out` returns
   `{"result": {... "children": [{"lifecycle", "result"}]}}` — the child carries the
   driver verb's raw `result` dict, never a "transcript"
   (`agency/capabilities/delegate.py:52-56`). The string "transcript" appears in
   **zero** files under `agency/` (grep). `score_transcript` (a pure string-pattern
   verb) therefore has no defined input on the wet path. **Fix:** define precisely
   what `run` feeds to `score_transcript` — e.g. `json.dumps(child["result"])`, or a
   named field the driver must return — and say so in the Done-When bullet.

3. **`agentic.verify_invariants` ontology is double-booked (Gate vs Invariant).**
   Spec L63/L149 say it records "a `Gate` via `gate.check`"; L118/L123-124 *also*
   declare an `Invariant` node type with an enum
   `("Invariant","name"):{depth_bound,quota_respected,no_orphans}` and say
   "`Invariant` nodes recorded." But `gate.check` only ever records a `Gate`
   (`agency/capabilities/gate.py:28`, fields `name/passed/evidence`) and edges
   `PASSED`/`BLOCKED_ON` (`:29`). Nothing records an `Invariant`. **Fix:** pick one —
   either (a) drop the `Invariant` node and use `gate.check(name="depth_bound", …)`
   with the enum applied to `Gate.name` (but note `Gate.name` is currently an
   *open* string, so widening its enum would constrain `spec-review`/`quality-review`
   too — so prefer not enum-constraining `Gate`), or (b) keep `Invariant` as a
   recorded node and have `verify_invariants` `ctx.record("Invariant", …)`
   *in addition to* the gate. State which, and which edge links it (only core
   `SERVES`/`PASSED`/`BLOCKED_ON` are available unless you add one).

4. **`gate.check` enforces same-intent; `verify_invariants` must pass a lifecycle
   that serves the current intent.** `gate.check` rejects cross-intent lifecycles
   (`agency/capabilities/gate.py:23-27`), and `delegate.fan_out` children all
   `SERVES` the current intent (`delegate.py:49`). Fine — but the spec should state
   that `verify_invariants(lifecycle_id=…)` must be a child of the *current*
   delegation, or the gate call returns `{"error": "...does not serve..."}` rather
   than a PASS/BLOCK. This is a real edge case for the "no orphaned working
   children" check.

5. **`delegate.fan_out` already guards `quota`/admission — "quota respected" is
   tautological post-hoc.** `fan_out` admits `items[:quota]` and rejects `quota<0`
   (`delegate.py:33-39`). A post-hoc `verify_invariants` "quota respected" check can
   never fail for a delegation produced by `fan_out` (the count is capped at write
   time). The genuinely checkable invariant is **"no orphaned `working` children"**
   (children start `working`, `delegate.py:48`, and only `subagent`/`join` move them
   to `completed`, `subagent.py:38`). **Fix:** drop or re-justify `quota_respected`;
   lead with the orphan check, which `delegate`/`join` do *not* already enforce.

6. **`detect_loop` algorithm matches Plan 119 — but verify the pairwise bound.**
   Spec L66/L170-176 ("last 4 msgs + last 5 tool results, pairwise max, 3-char
   shingles, ≥0.7") matches Plan 119 exactly
   (`the-agency-system/Plan/119-loop-detection/spec.md:36,65`). The spec says
   "≤81 pairs" (9² over the pooled 9 strings); Plan 119 also says "≤ 9² = 81"
   (`119:65`). Correct. Keep the `evidence` index-citation requirement (`119:37`,
   anchor 119.1 at `:79-84`) — it is the one part easy to drop.

7. **Migration-table row 119 wiring claim is accurate but understates the gap.**
   Plan 119 is half algorithm, half **hook + session-log source**
   (`119:38-40,57`: `UserPromptSubmit` hook, 2-note cap, state file, and
   `session_log_query` from Spec 100 as the message source). Agency has neither a
   hook layer nor a session-message store. The spec acknowledges this (Open Q1) but
   the Done-When ships only the pure verb with no consumer — see Missing Wiring.

---

## Duplication with existing capabilities

1. **`develop` already ships the pressure-test *concept* as a reference.**
   `agency/capabilities/develop.py:86-94` (`REFERENCES["testing-skills"]`) is
   verbatim the "test a discipline with subagents… turn each rationalization into a
   fixture the gate must reject" doctrine that Plan 133 and this spec's
   `agentic-pressure-test` skill encode. The new `pressure` capability is **not** a
   duplicate (it adds a real loader + rubric + dispatch the reference only
   *describes*), but the spec must (a) cite `develop.py:86-94` as prior art and
   (b) say whether the `agentic-pressure-test` SKILL.md supersedes / cross-links
   that reference, to avoid two divergent statements of the same doctrine.

2. **`develop`'s `review` discipline already binds a phase to `delegate.fan_out`.**
   `develop.py:65-71` — the `dispatch` phase invokes `delegate.fan_out` and "degrades
   to a document phase" without a registry. `pressure.run` is the same
   dispatch-a-child-via-delegate pattern. Not a blocking duplication, but the spec's
   `agentic-pressure-test` skill (L136-138) is a Lifecycle template that overlaps
   `review`'s shape. **Fix:** note the relationship; ideally `pressure.run` reuses
   the *exact* `subagent`/`review` dispatch path rather than a third variant.

3. **`subagent.develop` is the precedent the spec should mirror more closely —
   including its LLM dodge.** `subagent.develop` takes `spec_passed`/`quality_passed`
   as **inputs** (`subagent.py:24-25`) — it does *not* run a real reviewing LLM; the
   verdict is supplied by the caller and only the *gate provenance* is recorded.
   `pressure.run` could resolve its whole "needs an LLM driver" problem the same way:
   accept the transcript (or verdict) as an argument and keep the verb's job as
   *score + record provenance*. This is the cleanest de-risking and is not mentioned.

4. **No duplication of the depth guard or `gate`** — `verify_invariants` correctly
   *asserts against* `MAX_DEPTH` (`capability.py:52-53`) rather than reimplementing
   it, and records through `gate.check` rather than a new gate. Good; keep it.

---

## Missing wiring (the real gaps)

- **Loop detection has no consumer and no message source.** The verb is pure
  (correct), but Plan 119's value is the `UserPromptSubmit` hook + 2-note/3-turn
  throttle + `session_log_query` source (`119:38-40`). Agency exposes only
  `search`/`get_schema`/`execute` (`engine.py:5`, CLAUDE.md) — **no hook layer, no
  message buffer in the graph**. Done-When ships a signal nothing feeds or reads.
  *Decision the spec must force:* either (a) v1 ships the pure verb only and
  explicitly defers the hook to a future hooks spec (state this in Done-When, not
  just Open Q1), or (b) define where `messages`/`tool_results` come from in Agency's
  model (host-supplied buffer vs. a new `Invocation`-result traversal).

- **`pressure.run`'s wet path has no driver that yields a transcript.** This is the
  biggest gap. `run` composes `delegate.fan_out(quota=1)`, which needs a `driver`
  capability/verb that invokes an LLM-bearing subagent and returns scoreable text.
  The **only** shipped effect driver is `jules` (`jules.py:73`,
  `dispatch` at `:79-80`), and it returns Jules *session* JSON (a session id /
  status), **not** a transcript — and requires `JULES_API_KEY` (CLAUDE.md "Jules
  backend"). There is **no local-subagent LLM driver** in the repo (grep: no
  `transcript`, no local `claude -p` shell-out; `subagent` sidesteps it entirely by
  taking verdicts as inputs). So: the `dry_run=True` path is the *only* runnable path
  v1, and the spec should say the wet path is **deferred / requires a future local
  driver**, mirroring how `subagent.develop` keeps the LLM out of the verb. Done-When
  L92-94 (the example) is fine because it is dry-run; Done-When L82-85 (the wet
  `run`) currently over-promises.

- **`OntologyExtension` merge is strict — confirm new nodes/enums are clean.** New
  nodes (`Invariant`, `LoopSignal`, `Scenario`, `PressureRun`) and the `PressureRun.
  verdict` enum are fine (they are new labels; `ontology.py:81-86` allows new
  nodes/enums, raises only on *redefining* a core label). But the `Invariant.name`
  enum is only valid if `Invariant` is actually recorded (see correction #3). The
  two capabilities declare new nodes in *separate* extensions — confirm no label
  collision between them and core (none today).

- **`__init__.py` needs no edit — confirmed.** Spec L219-222 hedges on whether
  `capabilities/__init__.py` needs editing. It does **not**: `discover()` walks the
  package by reflection (`agency/capabilities/__init__.py` `discover()` —
  `pkgutil.iter_modules` + `isinstance`/`issubclass`), and `engine.py:48` registers
  whatever it returns. Dropping `agentic.py`/`pressure.py` self-registers. **Fix:**
  change the hedge to a flat "no edit required."

---

## Open-Questions triage

| # | Question | Triage |
|---|---|---|
| 1 | Loop-detection wiring / message source | **MUST RESOLVE before merge.** Don't ship a signal with no consumer or source. Decide: pure-verb-only v1 (defer hook to a hooks spec) and say so in Done-When. The "where does history come from" sub-question is real — Agency has no message store. |
| 2 | `verify_invariants` post-hoc vs pre-admission in `delegate` | **RESOLVE (cheap).** Post-hoc recorded `act` is the right shape *and* honors "do not modify delegate" (CLAUDE.md). Confirm and close — but fix the tautological `quota_respected` (correction #5). |
| 3 | `pressure.run` worker driver | **MUST RESOLVE — this is the core wiring gap.** Answer: no local driver ships; `jules` returns no transcript. Adopt the `subagent.develop` pattern (transcript/verdict as input) OR explicitly scope the wet path out of v1. |
| 4 | Scope of agentic primitives (4 vs 32) | **ACCEPT as scoped.** Distilling Plan 016's 32 tools (`016:65`) to 4 decidable verbs is defensible; the rest are covered by `develop` (`develop.py:28-80`). Keep `workflow_decompose`/`ralph_render` OUT (they're orchestration disciplines, not decidable transforms). |
| 5 | Core vs `examples/` | **ACCEPT core.** Engine-discipline beside `delegate`/`subagent` is right (CLAUDE.md: domain content → `examples/`, engine → `agency/capabilities/`). `pressure` belongs in core too — it composes `delegate`. |
| 6 | Skill self-test bootstrapping (circular GREEN) | **DEFER / note as known limitation.** Real but not blocking; have `agentic-pressure-test` ship a scenario that tests `develop`'s `tdd` (an *other* skill) for its GREEN baseline, not itself. State this. |

---

## Must-fix list (ordered)

1. **Define `pressure.run`'s transcript contract or scope the wet path out of v1.**
   There is no transcript in Agency and no local LLM driver (`jules` returns session
   JSON; `delegate.fan_out` returns the raw verb `result`, `delegate.py:52-56`).
   Adopt `subagent.develop`'s pattern — verdict/transcript as an *input* — or mark
   the wet path deferred. Done-When L82-85 must change. *(blocking)*

2. **Resolve the `Invariant` vs `Gate` double-booking in the `agentic` ontology**
   (corrections #3): `gate.check` records only a `Gate` (`gate.py:28`). Either drop
   the `Invariant` node + its enum, or have `verify_invariants` also
   `ctx.record("Invariant", …)`. Don't enum-constrain the shared open `Gate.name`. *(blocking)*

3. **Force the loop-detection wiring decision into Done-When** (not just Open Q1):
   ship the pure verb only for v1 and explicitly defer the hook + name the
   (absent) message source. Agency has no hook layer or message store
   (`engine.py:5`; Plan 119 needs `session_log_query`, `119:38`). *(blocking)*

4. Correct the `core.py` framing — the file does not exist; the depth guard is
   `CapabilityContext.spawn` / `MAX_DEPTH` (`capability.py:47-55`). (corrections #1)

5. Drop or re-justify the tautological `quota_respected` invariant; lead with the
   genuinely-checkable "no orphaned `working` children" (`delegate.py:48`,
   `subagent.py:38`). (corrections #5)

6. Cite `develop.py:86-94` (`testing-skills` reference) and `develop.py:65-71`
   (`review` → `delegate.fan_out`) as prior art and state the relationship, so the
   new `pressure` capability and `agentic-pressure-test` skill don't ship a second,
   divergent statement of the same doctrine. (duplication #1, #2)

7. Flatten the `capabilities/__init__.py` hedge (L219-222) to "no edit required" —
   `discover()` is pure reflection (`capabilities/__init__.py`). (Missing wiring #4)

---

## Adzic note — add executable examples to two Done-When bullets

`detect_loop` and `score_transcript` are the most testable verbs but the spec gives
no concrete input/expected pair. Borrow Plan 119 anchor 119.1
(`119:79-84`: "indices 0,2,4 byte-identical → detected, confidence 1.0") and Plan
133 anchor 133.2 (`133:138-143`: transcript with both a compliant hit and "just
this once" → `verdict="rationalised"`) verbatim as Given/When/Then in the spec so
the test author has a fixed target.
