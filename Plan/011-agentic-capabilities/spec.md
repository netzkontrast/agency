---
spec_id: "011"
slug: agentic-capabilities
status: draft
owner: "@agency"
depends_on: [001, 003]
affects:
  - agency/_middleware/loop.py
  - agency/capabilities/gate.py
  - skills/agentic-pressure-test/SKILL.md
  - skills/orchestrator-discipline/SKILL.md
  - docs/examples/pressure_test_a_skill.py
  - tests/test_loop_middleware.py
  - tests/test_gate_predicates.py
  - tests/test_lifecycle_check_invariants.py
  - tests/test_pressure_skill.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 3
domain: engine
wave: 1
---

# Spec 011 — Agentic Guardrails: loop-detection middleware + gate predicates + a pressure-test skill

## Why

`the-agency-system` has a distinct **agentic** layer — the discipline that keeps
multi-agent work honest: spec validation + confidence gating + workflow
decomposition as decidable primitives (Plan 016), loop detection as a fast-twitch
self-interrupt signal (Plan 119), and — most load-bearing — **subagent
pressure-tests** that ask the question neither a frontmatter linter nor a runtime
hook can answer: *does a discipline skill actually change a fresh agent's behaviour
under pressure, or does the agent rationalise it away?* (Plan 133, ported from
Superpowers' "TDD for skills").

The behaviour belongs in Agency. The **packaging does not.** The original draft of
this spec proposed two net-new top-level capabilities (`agentic`, `pressure`). The
canon forbids that: the net-new-primitive budget is **spent** — `delegate` (built)
and `research` (a *composition*, shipped as a skill template, not a primitive)
(`CAPABILITY-CLUSTERS.md:26-36`). "Multiplying concepts would re-introduce bloat"
(`CLUSTERS:31`). So this spec adds **zero new capabilities and zero ontology
extensions**. It re-homes every piece of behaviour to where the canon already puts
it:

- **loop-detection is engine middleware, not a concept** — the canon names it by
  that exact term (`CORE.md:16-18`);
- **a predicate that blocks a phase IS a `gate`** (`CLUSTERS:18`);
- **structural checks over an agent-session are Lifecycle observation** (`check`,
  in the `verify`/`COMPLETED ≠ done` family, `CORE.md:31,33-35`);
- **a delegate→transform→gate flow ships as a skill template** — the `research`
  precedent (`CLUSTERS:22,36`).

Agency already ships the *orchestration* surface this composes with: `delegate`
(`fan_out`/`join` over child Lifecycles under a quota), `subagent` (dispatch a
worker then run a two-stage gated review), and `gate` (the reusable hard-gate
predicate, `gate.py`). It also already ships the *doctrine* of pressure-testing as
an on-demand reference: `develop.py:86-94` (`REFERENCES["testing-skills"]`) states
verbatim "a discipline is only real if a fresh agent, given ONLY the discipline,
follows it… turn each rationalization into a fixture the gate must reject." What is
missing is the **executable** half: a loop-detection signal the engine can run, a
couple of decidable `gate` predicates, an auditable Lifecycle check, and a
pressure-test *skill* (loader + pure rubric + recorded run) the author can actually
*walk* instead of only reading the doctrine. The `agentic-pressure-test` SKILL.md
cross-links (does not restate) `testing-skills` so there is one canonical doctrine.

**Code-mode IS the contract**: the gate predicates are discovered via `search` and
called from inside `execute`; the loop helper is an internal engine util (not a
discoverable verb); the pressure-test is a Lifecycle template the skill walker
walks. There is no bespoke agentic tool surface.

## Done When

- [ ] **No new capability and no new ontology extension is added.** No
  `agency/capabilities/agentic.py`, no `agency/capabilities/pressure.py`, no
  `LoopSignal`/`Scenario`/`PressureRun` node labels. The work lands as middleware +
  `gate` facets + a Lifecycle check + one skill template (`CLUSTERS:26-36`).
- [ ] `agency/_middleware/loop.py` exposes a **pure helper** (NOT a discoverable
  verb) `detect_loop(messages, tool_results) -> {detected, confidence, evidence}`
  re-implementing the Plan-119 Jaccard-on-3-char-shingles algorithm (last 4 msgs +
  last 5 tool results, pairwise max over ≤ 9²=81 pairs, threshold 0.7), stdlib only
  (no `numpy`/`rapidfuzz`). Loop-detection is engine middleware, **not a concept**
  (`CORE.md:17`); the function is imported by the future hooks layer, never
  surfaced via `search`/`get_schema`/`execute`. **v1 ships the helper only**: Agency
  has no hook layer and no session-message store, so the Plan-119 `UserPromptSubmit`
  hook, the 2-note/3-turn throttle, and the `session_log_query` message source
  (`119:38-40`) are DEFERRED **as middleware** to a future hooks spec — not as a
  verb-now/hook-later split. The helper does not invent a message source; its
  caller supplies `messages`/`tool_results`.
- [ ] `gate.check` is used to record a **`spec_validate` predicate**: a pure module
  helper classifies RFC-2119 keyword presence + Gherkin-scenario presence on spec
  text → `{ok, findings:[{rule, locator, msg}]}`, and the caller records the verdict
  via `gate.check(lifecycle_id, name="spec-valid", passed=ok, evidence=...)`
  (`gate.py:28`). No new verb; it feeds `develop`'s `spec-panel`/`plan` disciplines
  (`develop.py:57-61`). Decidable, no LLM.
- [ ] `gate.check` is used to record a **`confidence_check` predicate**: a pure
  module helper scores a pre-action confidence gate from a checklist of decidable
  claims → `{score:float, blocking:[...]}`; `score ≥ 0.9` is the documented
  go-threshold (mirrors JULES_PROTOCOL Gate 1) and is recorded via
  `gate.check(name="confidence", passed=score>=0.9, evidence=...)`. A stateless
  precondition predicate with a go-threshold that blocks a phase **is the definition
  of `gate`** (`CLUSTERS:18`) — no new verb.
- [ ] A **Lifecycle structural `check`** over a delegation/subagent run asserts the
  one non-redundant invariant — **no orphaned `working` children** — and records the
  outcome via `gate.check`. It is the auditable companion to the `ctx.spawn`
  depth backstop and the `COMPLETED ≠ done` `verify` family (`CORE.md:33-35`), NOT a
  new capability's `act`. The depth-bound is already enforced by `ctx.spawn`
  (`capability.py:52-53`) and the quota half is tautological — `fan_out` caps at
  `quota` at write time (`delegate.py:39`) — so **both are dropped**. The checked
  `lifecycle_id` MUST be a child of the *current* delegation (children all `SERVES`
  the current intent, `delegate.py:49`); otherwise `gate.check` returns
  `{"error": "...does not serve..."}` (`gate.py:23-27`). No `Invariant` node is
  recorded — `gate.check` records only a `Gate` (`gate.py:28`).
- [ ] `skills/agentic-pressure-test/SKILL.md` (kind `discipline`) is a **Lifecycle
  template** (the `research` model, `CLUSTERS:22,36`) that walks
  `delegate.fan_out` (worker) → a `transform` rubric step → `gate.check`. The pure
  scenario/rubric functions live as **module helpers the skill calls** (the open
  `transform` set, `CLUSTERS:20`), recorded via existing `Artefact`/`Gate` nodes —
  **no `Scenario`/`PressureRun` labels**:
  - `load_scenario(scenario)` validates a pressure-scenario mapping (`name`,
    `skill_under_test`, `pressures` [≥3], `task_prompt`, `compliant_behaviours`,
    `violation_indicators`, `rationalisation_patterns`) → normalized scenario or a
    structured error.
  - `score_transcript(transcript, scenario)` → `{score:int(0-100), verdict,
    evidence}` via pure string-pattern checks; a `rationalisation_patterns` hit
    flips `verdict="rationalised"` regardless of raw score; verdict ∈ `{compliant,
    violation, rationalised, ambiguous}`.
  - the run step **takes the worker output as an INPUT** — it does NOT invoke an
    LLM. Mirroring `subagent.develop` (which takes `spec_passed`/`quality_passed` as
    inputs, `subagent.py:24-25`), it accepts a `transcript:str` (the already-produced
    worker output) plus the `scenario`, scores it via `score_transcript`, records an
    `Artefact` (kind `pressure-run`) `SERVES` intent, and records a scored `Gate` via
    `gate.check`. A `dry_run=True` path (the v1 default and the **only runnable v1
    path**) short-circuits with a synthetic `ambiguous` result so tests never need a
    live LLM. The **wet path** — dispatching a fresh worker to *generate* the
    transcript — is DEFERRED: `delegate.fan_out` returns the driver verb's raw
    `result` dict, not a transcript (`delegate.py:52-56`), and the only shipped effect
    driver (`jules`) returns session JSON, not scoreable text (`jules.py:79-80`). v1
    has no local-subagent LLM driver; the skill caller supplies the transcript.
- [ ] The two skills install and lint clean (`plugin.lint_skill`):
  `skills/agentic-pressure-test/SKILL.md` (kind `discipline`, the 4-phase
  RED→GREEN→REFACTOR→STAY-GREEN cycle, cross-linking `develop.py:86-94`) and
  `skills/orchestrator-discipline/SKILL.md` (kind `discipline`, the token/summary-only
  orchestration rule, with its own pressure scenario shipped so it is itself
  pressure-testable).
- [ ] `pytest -q tests/test_loop_middleware.py tests/test_gate_predicates.py
  tests/test_lifecycle_check_invariants.py tests/test_pressure_skill.py` passes; the
  baseline suite (`pytest -q`) still passes (no regression).
- [ ] `python docs/examples/pressure_test_a_skill.py` walks the pressure-test skill's
  dry-run path end-to-end and prints the recorded provenance (scenario `Artefact` →
  run `Artefact` → scored `Gate`).

## Design

### The reframe: every piece re-homed to an existing concept

This spec is **additive and compositional** — it never reimplements and never adds
a primitive. The mapping from the original (deleted) two-capability draft to its
canon home:

| Original verb | Original home | **Canon home** | This spec |
|---|---|---|---|
| `detect_loop` | new `agentic` cap | engine **middleware** (`CORE.md:17`) | pure helper in `agency/_middleware/loop.py`, not a discoverable verb |
| `verify_invariants` | new `agentic` cap | Lifecycle **`check`** + `gate` (`CORE.md:31,33-35`) | a structural check (no-orphans only) recorded via `gate.check` |
| `spec_validate` | new `agentic` cap | facet of **`gate`** (`CLUSTERS:18`) | a pure predicate recorded via `gate.check`, feeding `develop` |
| `confidence_check` | new `agentic` cap | facet of **`gate`** (`CLUSTERS:18`) | a pure go/no-go predicate (`≥0.9`) recorded via `gate.check` |
| `load_scenario` | new `pressure` cap | **skill** helper / `transform` (`CLUSTERS:20,22,36`) | module helper the pressure-test skill calls |
| `score_transcript` | new `pressure` cap | **skill** helper / `transform` | module helper the pressure-test skill calls |
| `run` | new `pressure` cap | **skill composition** (delegate→transform→gate) | the pressure-test skill's run step (transcript-as-input, dry_run-only v1) |

### Relationship to the existing orchestration capabilities

- `delegate.fan_out`/`join` — child-Lifecycle orchestration under a quota
  (`delegate.py:28-56`). The structural `check` is the *post-hoc* read over whatever
  a delegation/subagent produced — the same Lifecycle-read family as
  `delegate.join`'s state tally (`delegate.py:69-77`). The pressure-test skill's run
  step does NOT dispatch through `delegate` in v1 (its wet path is deferred); it
  scores a caller-supplied transcript.
- `subagent.develop` — dispatch + two-stage gated review (`subagent.py:22-39`). This
  is the **precedent the pressure-test run step mirrors**: `subagent.develop` keeps
  the LLM out of the verb by taking the review verdicts as *inputs* and recording
  only the gate provenance (`subagent.py:24-25`). The run step does the same with the
  transcript/verdict — its job is *score + record*, not *invoke an agent*.
- `develop`'s disciplines (`develop.py`) — `develop.py:65-71` already binds the
  `review` skill's `dispatch` phase to `delegate.fan_out` (degrading to a document
  phase without a registry), and `develop.py:86-94` already carries the
  `testing-skills` pressure-test doctrine as an on-demand reference. The
  pressure-test skill adds the *executable loader + rubric + recorded run* the
  reference only describes; its SKILL.md cross-links the reference rather than
  restating it (one canonical doctrine). `spec_validate` plugs into `develop`'s
  `spec-panel`/`plan` disciplines as a gate predicate.
- `gate.check` — the hard-gate predicate (`gate.py:20-32`). All four predicates
  (`spec_validate`, `confidence_check`, the no-orphans check, the pressure run)
  record their verdicts through `gate.check`, so a failed gate is provenance and
  pauses the Lifecycle for re-entry (no new gate mechanism invented). `gate.check`
  records a `Gate` only — never a separate invariant node.
- `ctx.spawn` depth guard (`CapabilityContext.MAX_DEPTH = 16`, `capability.py:47`,
  raise at `:52-53`). The structural `check` *asserts the audited residue* (no
  orphaned `working` children); it does NOT re-check depth — the engine's depth guard
  stays the runtime backstop.

### No OntologyExtension — reuse core nodes

The original draft added `LoopSignal`, `Scenario`, and `PressureRun` node labels in
two capability ontology extensions. **All three are dropped** (`CLUSTERS:31`):

- `detect_loop` is a *middleware emission*, not a graph concept — it records nothing
  (the helper is pure; a future hooks layer decides whether to persist a note).
- `Scenario` and `PressureRun` are *skill-walk artefacts* — the pressure-test skill
  records them as core `Artefact` nodes (`{kind: "scenario", ...}`,
  `{kind: "pressure-run", verdict: ...}`), exactly as `delegate.join` records its
  reduction as a core `Artefact` (`delegate.py:78`). Verdict is an Artefact property,
  not an ontology-enum on a bespoke label.
- the structural check + all predicates record only a core `Gate` via `gate.check`.
  `Gate.name` stays an *open* string (enum-constraining it would constrain
  `spec-review`/`quality-review` too); the gate names used here (`no_orphans`,
  `spec-valid`, `confidence`, `pressure`) are documented conventions, not an enum.

Net: zero new labels, zero enum changes, zero capability files. The strict ontology
merge (`ontology.py`) is untouched.

### Skills (Lifecycle templates the walker walks)

- `agentic-pressure-test` (kind `discipline`): `scenario(load) → red(without-skill)
  → green(with-skill) → refactor(close-loopholes, hard)`. The phase ordering enforces
  RED-before-GREEN the same way `develop`'s `tdd` skill enforces the Iron Law, and the
  worker step composes `delegate.fan_out` exactly as `develop`'s `review` discipline
  does (`develop.py:65-71`). The scenario/rubric module helpers are called from the
  phase code; provenance is recorded as core `Artefact` + `Gate` nodes.
- `orchestrator-discipline` (kind `discipline`): `summarize → filter → confirm(hard)`
  — codifies summary-only / no-raw-dump orchestration (the L14 token rule), with a
  pressure scenario shipped under the skill so it is itself pressure-testable.

### Loop detection (Plan 119 → `_middleware/loop.py`)

Pure re-implementation: `shingles(s) = {s[i:i+3] …}` after lower/whitespace-normalise;
Jaccard `|A∩B|/|A∪B|`; pairwise max over the last 4 messages + last 5 tool results
(≤ 81 pairs); `detected = max ≥ 0.7`; `evidence` names the two driving indices (keep
the index-citation requirement — Plan 119 anchor 119.1, `119:79-84`). Empty inputs →
`{detected:False, confidence:0.0, evidence:None}`. The 2-note-per-session cap, 3-turn
cooldown, `UserPromptSubmit` hook, and `session_log_query` message source
(`119:38-40`) are **out of scope for v1**: the whole consumer is deferred *as
middleware* (Agency has no hook layer or message store), per `CORE.md:17`. The
function never sources its own history and is never registered as a verb.

### Pressure-test skill (Plan 133 → a skill template, the `research` model)

`load_scenario` mirrors the-agency-system's `Scenario` dataclass (≥3 pressures, the
compliant/violation/rationalisation lists; rejects a mapping missing a required key,
Plan 133 anchor 133.1) but ships as a **module helper**, not a node label.
`score_transcript` is the pure rubric: `score = max(0, min(100, 50 + 10*compliance -
15*violation))`; decision order (1) any rationalisation hit → `rationalised`;
(2) compliance ≥ violation and ≥1 → `compliant`; (3) violation ≥1 → `violation`;
(4) else → `ambiguous` (Plan 133 anchor 133.2: both a compliant hit and "just this
once" → `rationalised`, never `compliant`). The run step scores a caller-supplied
transcript and records a `pressure-run` `Artefact` + scored `Gate`; the dry-run
synthetic result keeps unit tests deterministic and offline (Plan 133 anchor 133.3:
`dry_run=True` → `verdict="ambiguous"` and no dispatch). The two shipped scenarios
pressure-test `orchestrator-discipline` and (for the `agentic-pressure-test` skill's
own GREEN baseline) `develop`'s `tdd` discipline — an *other* skill, sidestepping the
circular self-test problem.

### Deliberate divergence from the research draft (no `core.py`)

`research/capability-specs/specs/agentic.md` proposed engine-level loop-detection
middleware *and* a `core.py` edit (`affects: agency/core.py`). **There is no
`core.py` and no `core/` package** in Agency — the substrate is `agency/engine.py` +
`agency/capability.py`. The depth guard already lives in `CapabilityContext.spawn`
(`capability.py:49-55`, `MAX_DEPTH=16` at `:47`). This spec lands the loop algorithm
as a *new internal middleware module* (`agency/_middleware/loop.py`) — honouring the
research draft's "middleware" instinct without editing a file that does not exist —
and the structural check asserts against the existing depth guard rather than adding
a depth middleware.

### Migration / coverage map (the-agency-system → Agency)

| the-agency-system (Plan @ SHA) | Agency landing |
|---|---|
| 016 agentic handlers (32 decidable tools) | distilled to 2 `gate` predicates (`spec_validate`, `confidence_check`) + a Lifecycle no-orphans check; the rest are out-of-scope v1 (the `develop` skill family already covers plan/workflow disciplines) |
| 016 `dry_run` / `return_plan` / `ToolResult` envelope | Agency's analogue is the verb-result `{result: …}` shape + an explicit `dry_run` flag in the skill's run step; no separate envelope (code-mode IS the contract) |
| 119 loop detection (UserPromptSubmit hook + Jaccard) | the Jaccard helper in `agency/_middleware/loop.py` (**middleware, not a verb**, `CORE.md:17`); the hook/throttle/message-source are deferred to a future hooks spec — Agency has no hook layer |
| 133 skill subagent-pressure-tests (CLI + scenarios + rubric) | the `agentic-pressure-test` **skill template** (load → red → green → refactor) + module-level rubric helpers; the run step scores a supplied transcript (the `subagent.develop` LLM-as-input dodge) instead of shelling out to `claude -p` |
| 016 agentic skill catalogue (~60 sc-*/superpowers-* skills) | OUT — already covered by the `develop` capability's disciplines + `skills/`; this spec adds only the two missing discipline skills |
| token-budget invariants / loop-depth middleware (catalogue row 24) | the structural `check` asserts against the engine's existing `MAX_DEPTH` guard (`capability.py:47-55`); loop detection is a separate middleware util |

## Files

- **Create**:
  - `agency/_middleware/loop.py` — the pure Jaccard-shingle `detect_loop` helper
    (NOT a capability; not discoverable). A future hooks layer imports it.
  - `skills/agentic-pressure-test/` — the discipline skill (SKILL.md + a `scenarios/`
    example or two, pressure-testing `develop`'s `tdd`; cross-links `develop.py:86-94`
    rather than restating the doctrine) + the module-level `load_scenario` /
    `score_transcript` rubric helpers the skill phases call.
  - `skills/orchestrator-discipline/SKILL.md` — the orchestration discipline skill (+
    its own pressure scenario).
  - `docs/examples/pressure_test_a_skill.py` — runnable dry-run walk of the skill.
  - `tests/test_loop_middleware.py`, `tests/test_gate_predicates.py`,
    `tests/test_lifecycle_check_invariants.py`, `tests/test_pressure_skill.py`.
- **No new capability file**: no `agency/capabilities/agentic.py`, no
  `agency/capabilities/pressure.py`. The predicates are `gate.check` calls; the
  helpers are module functions; the run flow is a skill template.
- **No edit required**: `agency/capabilities/gate.py` already records the predicates
  via its existing `check` verb; `agency/capabilities/__init__.py` is untouched (no
  new module to discover).
- **Do not modify**: `agency/engine.py`, `agency/capability.py`, `agency/ontology.py`,
  and the existing `delegate`/`subagent`/`gate`/`develop` capabilities — this spec
  composes with them. (There is no `core.py` to leave untouched.)

## Acceptance (Gherkin — ported anchors)

```gherkin
# anchor: 119.1 (detect_loop middleware helper)
Scenario: Identical repeated tool result triggers loop detection at confidence 1.0
  Given a window of 5 tool results where indices 0, 2, and 4 are byte-identical
  When the _middleware.loop.detect_loop(messages=[], tool_results=window) helper is called
  Then result.detected is True
  And result.confidence == 1.0
  And result.evidence references two of the duplicate indices
  And detect_loop is not registered as a discoverable verb

# anchor: 133.2 (score_transcript skill helper)
Scenario: Rubric flips verdict to "rationalised" when patterns match
  Given a transcript containing both "ran pytest" (compliant) and "just this once" (rationalisation)
  When the pressure-test skill's score_transcript(transcript, scenario) helper is called
  Then the verdict is "rationalised"
  And the verdict is NOT "compliant" regardless of raw score

# anchor: 133.3 (pressure-test skill run step, dry_run)
Scenario: Dry-run run produces an ambiguous verdict without an LLM dispatch
  Given a valid scenario and dry_run=True
  When the pressure-test skill's run step is walked with dry_run=True
  Then a pressure-run Artefact is recorded with verdict == "ambiguous"
  And a Gate is recorded via gate.check
  And no worker is dispatched

# anchor: gate facet (confidence_check)
Scenario: A sub-threshold confidence predicate blocks the phase as a Gate
  Given a confidence checklist scoring 0.6 (< the 0.9 go-threshold)
  When gate.check(lifecycle_id, name="confidence", passed=False, evidence=...) is called
  Then a BLOCKED_ON Gate is recorded and the Lifecycle pauses at input-required
  And no new node label is introduced
```

## Open Questions / Needs Research

1. **Loop-detection consumer is middleware, deferred whole (DECIDED for v1).** v1
   ships the pure helper in `agency/_middleware/loop.py` only; the `UserPromptSubmit`
   hook, 2-note/3-turn throttle, and the message source are out of scope (Agency has
   no hook layer or message store). The canon names loop-detection middleware, not a
   concept (`CORE.md:17`), so it is deferred *as middleware*, not as a verb-now/hook-
   later split. The open question for the *future* hooks spec: where does session-
   message history come from — a host-supplied buffer, or an `Invocation`-result
   traversal of the graph? Recorded here so it is not lost; does NOT block v1.
2. **Structural check — post-hoc, no-orphans only (RESOLVED).** A recorded post-hoc
   Lifecycle `check` is the right shape and honours "do not modify `delegate`". Depth
   is the `ctx.spawn` backstop (`capability.py:52-53`); quota admission is enforced in
   `fan_out` (`delegate.py:33-39`) so a post-hoc quota check is tautological — both
   DROPPED. The genuinely checkable invariant is "no orphaned `working` children"
   (children start `working` at `delegate.py:48`; only `subagent`/`join` move them to
   `completed`, `subagent.py:38`). Note its overlap with `COMPLETED ≠ done`/`verify`
   (`CORE.md:33-35`): it is the *same family*, the auditable residue, not a new concept.
3. **Pressure-test run wet path (DEFERRED, decided for v1).** v1's run step scores a
   caller-supplied transcript (the `subagent.develop` LLM-as-input pattern) and the
   only runnable path is `dry_run`. A *future* wet path needs a local-subagent LLM
   driver that returns scoreable text — Agency ships none (`jules` returns session
   JSON, `jules.py:79-80`; `delegate.fan_out` returns the raw verb `result`,
   `delegate.py:52-56`). Adding that driver is a separate spec.
4. **Scope of the agentic primitives (RESOLVED — accept as scoped).** Plan 016 had 32
   tools; this spec keeps 2 decidable gate predicates + a structural check, and the
   rest are covered by `develop`'s disciplines. `workflow_decompose`/`ralph_render`
   stay OUT (orchestration disciplines, not decidable transforms).
5. **Are these core capabilities, examples, or facets? (RESOLVED — facets/middleware/
   skill, NOT new capabilities.)** The canon's net-new-primitive budget is spent
   (`delegate` + `research`, `CLUSTERS:32-36`). Loop-detection is middleware
   (`CORE.md:17`); the predicates are `gate` facets (`CLUSTERS:18`); the structural
   check is Lifecycle observation (`CORE.md:31`); pressure-testing is a skill template
   (the `research` model, `CLUSTERS:22,36`). Zero new top-level capabilities.
6. **Skill self-test bootstrapping (DEFER as known limitation).** `agentic-pressure-
   test` tests discipline skills; for its own GREEN baseline it ships a scenario that
   tests *another* skill (`develop`'s `tdd`), avoiding a circular GREEN. Pressure-
   testing the skill against itself is a noted future limitation, not a v1 blocker.

## Evidence

- Vision canon (the reframe driver): `/home/user/agency/docs/vision/CORE.md`
  (`:16-18` loop-detection is middleware not a concept; `:31` Lifecycle observe
  verbs `read · find · check · watch`; `:33-35` an agent-session is a Lifecycle
  parameterization, `COMPLETED ≠ done`/`verify`),
  `/home/user/agency/docs/vision/CAPABILITY-CLUSTERS.md` (`:18` `gate` is a facet of
  Lifecycle; `:20` the open `transform` set; `:22,36` `research` is a composition
  shipped as a skill template; `:26-36` why so few primitives — the budget is spent).
- Vision-alignment review (verdict NEEDS-MAJOR-REFRAME):
  `/home/user/agency/Plan/011-agentic-capabilities/VISION-REVIEW.md` (per-verb rulings,
  MC1-MC7).
- Engineering review (kept realism): `/home/user/agency/Plan/011-agentic-capabilities/REVIEW.md`
  (transcript-as-input, dry_run-only, no phantom `core.py`).
- Research (the divergence source): `/home/user/agency/research/capability-specs/specs/agentic.md`
  (proposed the non-existent `core.py` edit),
  `/home/user/agency/research/capability-specs/capability-catalogue.md` (rows 22-28).
- Agency composition surface: `/home/user/agency/agency/capabilities/gate.py`
  (`check` records a `Gate` only `:28`; rejects cross-intent lifecycles `:23-27` — the
  home for the predicates),
  `/home/user/agency/agency/capabilities/delegate.py` (`fan_out`/`join` — returns the
  raw verb `result`, not a transcript, `:52-56`; quota admission `:33-39`; children
  start `working` `:48`; `join` records a core `Artefact` reduction `:78` — the
  precedent for skill-walk artefacts),
  `/home/user/agency/agency/capabilities/subagent.py` (dispatch + two-stage gated
  review; takes verdicts as INPUTS `:24-25` — the LLM-out-of-the-verb pattern the run
  step mirrors; moves a verified child to `completed` `:38`),
  `/home/user/agency/agency/capabilities/develop.py` (`review` binds a phase to
  `delegate.fan_out` `:65-71` — the skill-template precedent; `spec-panel` `:57-61`
  consumes `spec_validate`; `REFERENCES["testing-skills"]` carries the pressure-test
  doctrine `:86-94` — prior art this spec cross-links),
  `/home/user/agency/agency/capability.py` (`CapabilityContext.spawn` `MAX_DEPTH=16`
  guard `:47-55`; `@verb` roles `:84-90`).
- Source depth (the-agency-system @ 0a6a9e71): `Plan/016-agentic-handlers-and-skills`
  (the decidable agentic surface + dry_run/ToolResult discipline), `Plan/119-loop-detection`
  (the Jaccard-shingle algorithm + thresholds + the deferred hook/throttle/source),
  `Plan/133-skill-subagent-pressure-tests` (the Scenario dataclass, the pure rubric,
  the RED/GREEN/REFACTOR cycle, anchors 133.1-133.3),
  `Plan/135-spec-test-anchor-traceability` (the anchor-citation convention used above).
</content>
</invoke>
