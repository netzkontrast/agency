---
spec_id: "011"
slug: agentic-capabilities
status: draft
owner: "@agency"
depends_on: [001, 003]
affects:
  - agency/capabilities/agentic.py
  - agency/capabilities/pressure.py
  - skills/agentic-pressure-test/SKILL.md
  - skills/orchestrator-discipline/SKILL.md
  - docs/examples/pressure_test_a_skill.py
  - tests/test_agentic_capability.py
  - tests/test_pressure_capability.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 3
domain: engine
wave: 1
---

# Spec 011 — Agentic Capabilities

## Why

`the-agency-system` has a distinct **agentic** layer that is not domain content and
not raw orchestration — it is the discipline that keeps multi-agent work honest:
spec validation + confidence gating + workflow decomposition as decidable
primitives (Plan 016), loop detection as a fast-twitch self-interrupt signal (Plan
119), and — most load-bearing — **subagent pressure-tests** that ask the question
neither a frontmatter linter nor a runtime hook can answer: *does a discipline skill
actually change a fresh agent's behaviour under pressure, or does the agent
rationalise it away?* (Plan 133, ported from Superpowers' "TDD for skills").

Agency already ships the *orchestration* half of this: `delegate` (`fan_out`/`join`
over child Lifecycles under a quota), `subagent` (dispatch a worker then run a
two-stage gated review), and `gate` (the reusable hard-gate predicate). It also
already ships the *doctrine* of pressure-testing as an on-demand reference:
`develop.py:86-94` (`REFERENCES["testing-skills"]`) states verbatim "a discipline is
only real if a fresh agent, given ONLY the discipline, follows it… turn each
rationalization into a fixture the gate must reject." What is missing is the
**executable** half — verbs and skills that make autonomous loops self-correcting
and that let an author *run* a pressure-test (a loader + a pure rubric + a recorded
run) instead of only reading the doctrine. This spec adds an `agentic` capability
(decidable agentic primitives) and a `pressure` capability (the TDD-for-skills
framework), plus the two discipline skills they surface, **without re-deriving**
`delegate`/`subagent`/`gate` — it composes with them, and the
`agentic-pressure-test` SKILL.md cross-links (does not restate) the `testing-skills`
reference so there is one canonical statement of the doctrine.

Because these are engine-domain (not a content domain), they ship in the core
`agency/capabilities/` package and self-register exactly like `delegate` and
`subagent`. **Code-mode IS the contract**: the verbs are discovered via `search`
and called from inside `execute`; there is no bespoke agentic tool surface.

## Done When

- [ ] `agency/capabilities/agentic.py` defines `AgenticCapability(CapabilityBase)`
  (`name="agentic"`, `home="lifecycle"`) that self-registers — `discover()` walks the
  package by reflection, so dropping the file is the only wiring needed (no edit to
  `engine.py` or `capabilities/__init__.py`).
- [ ] `agency/capabilities/pressure.py` defines `PressureCapability` (`name="pressure"`,
  `home="lifecycle"`) carrying the pressure-scenario + rubric ontology.
- [ ] The `agentic` verb table (below) is implemented and role-tagged; every verb
  is **decidable** (pure `transform`) or records real provenance (`act`) — none
  requires an LLM at call time.
- [ ] `agentic.verify_invariants(lifecycle_id, max_depth=...)` (act) asserts the
  structural invariants over a delegation/subagent run — depth ≤ `ctx.MAX_DEPTH`
  (`capability.py:47-55`) and **no orphaned `working` children** — and records the
  outcome as a `Gate` via `gate.check` (PASS, or `BLOCKED_ON` + an `input-required`
  pause). `lifecycle_id` MUST be a child of the *current* delegation (children all
  `SERVES` the current intent, `delegate.py:49`); otherwise `gate.check` returns
  `{"error": "...does not serve..."}` (`gate.py:23-27`). No `Invariant` node is
  recorded — `gate.check` records only a `Gate` (`gate.py:28`).
- [ ] `agentic.detect_loop(messages, tool_results)` (transform) re-implements the
  Plan-119 Jaccard-on-3-char-shingles algorithm (last 4 msgs + last 5 tool results,
  pairwise max over ≤ 9²=81 pairs, threshold 0.7) and returns `{detected, confidence,
  evidence}` — stdlib only, no `numpy`/`rapidfuzz`. **v1 ships the PURE verb only**:
  Agency has no hook layer and no session-message store (`engine.py` exposes only
  `search`/`get_schema`/`execute`), so the Plan-119 `UserPromptSubmit` hook, the
  2-note/3-turn throttle, and the `session_log_query` message source
  (`119:38-40`) are explicitly DEFERRED to a future hooks spec. The verb does not
  invent a message source; its callers supply `messages`/`tool_results`.
- [ ] `agentic.spec_validate(text)` (transform) returns `{ok, findings:[{rule,
  locator, msg}]}` classifying RFC-2119 keyword presence and Gherkin-scenario
  presence — decidable, no LLM.
- [ ] `agentic.confidence_check(claims)` (transform) scores a pre-action confidence
  gate from a checklist of decidable claims and returns `{score:float, blocking:[...]}`;
  `score ≥ 0.9` is the documented go-threshold (mirrors JULES_PROTOCOL Gate 1).
- [ ] `pressure.load_scenario(scenario)` (transform) validates a pressure-scenario
  mapping (`name`, `skill_under_test`, `pressures` [≥3], `task_prompt`,
  `compliant_behaviours`, `violation_indicators`, `rationalisation_patterns`) and
  returns the normalized scenario or a structured error.
- [ ] `pressure.score_transcript(transcript, scenario)` (transform) returns
  `{score:int(0-100), verdict, evidence}` using pure string-pattern checks: a
  `rationalisation_patterns` hit flips `verdict="rationalised"` regardless of raw
  score; verdict ∈ `{compliant, violation, rationalised, ambiguous}`.
- [ ] `pressure.run` (effect) **takes the worker output as an INPUT** — it does NOT
  invoke an LLM. Mirroring `subagent.develop` (which takes `spec_passed`/
  `quality_passed` as inputs, `subagent.py:24-25`), `run` accepts a `transcript:str`
  (the already-produced worker output) plus the `scenario`, scores it via
  `score_transcript`, and records a `PressureRun` + a scored `Gate` via `gate.check`.
  A `dry_run=True` path (the v1 default and the **only runnable v1 path**)
  short-circuits with a synthetic `ambiguous` result so tests never need a live LLM.
  The **wet path** — actually dispatching a fresh worker to *generate* the transcript
  — is DEFERRED: `delegate.fan_out` returns the driver verb's raw `result` dict, not
  a transcript (`delegate.py:52-56`), and the only shipped effect driver (`jules`)
  returns session JSON, not scoreable text (`jules.py:79-80`). v1 has no
  local-subagent LLM driver; the caller supplies the transcript.
- [ ] The two skills install and lint clean (`plugin.lint_skill`):
  `skills/agentic-pressure-test/SKILL.md` (kind `discipline`, the 4-phase
  RED→GREEN→REFACTOR→STAY-GREEN cycle, cross-linking `develop.py:86-94`) and
  `skills/orchestrator-discipline/SKILL.md` (kind `discipline`, the token/summary-only
  orchestration rule).
- [ ] `pytest -q tests/test_agentic_capability.py tests/test_pressure_capability.py`
  passes; the baseline suite (`pytest -q`) still passes (no regression).
- [ ] `python docs/examples/pressure_test_a_skill.py` runs the dry-run path
  end-to-end and prints the recorded provenance (scenario → run Lifecycle →
  scored Gate).

## Design

### Relationship to the existing orchestration capabilities

This spec is **additive and compositional** — it never reimplements:

- `delegate.fan_out`/`join` — child-Lifecycle orchestration under a quota
  (`delegate.py:28-56`). `agentic.verify_invariants` is the *post-hoc* structural
  check over whatever a delegation/subagent produced (it does not gate admission —
  see below). `pressure.run` does NOT dispatch through `delegate` in v1 (its wet path
  is deferred); it scores a caller-supplied transcript.
- `subagent.develop` — dispatch + two-stage gated review (`subagent.py:22-39`).
  This is the **precedent `pressure.run` mirrors**: `subagent.develop` keeps the LLM
  out of the verb by taking the review verdicts as *inputs* and recording only the
  gate provenance. `pressure.run` does the same with the transcript/verdict — its job
  is *score + record*, not *invoke an agent*.
- `develop`'s disciplines (`develop.py`) — `develop.py:65-71` already binds the
  `review` skill's `dispatch` phase to `delegate.fan_out` (degrading to a document
  phase without a registry), and `develop.py:86-94` already carries the
  `testing-skills` pressure-test doctrine as an on-demand reference. The new
  `pressure` capability adds the *executable loader + rubric + recorded run* that the
  reference only describes; the `agentic-pressure-test` SKILL.md cross-links the
  reference rather than restating it (one canonical doctrine).
- `gate.check` — the hard-gate predicate (`gate.py:20-32`). `verify_invariants`,
  `confidence_check`, and `pressure.run` record their verdicts through `gate.check`
  so a failed agentic gate is provenance and pauses the Lifecycle for re-entry (no
  new gate mechanism invented). `gate.check` records a `Gate` only — never a separate
  invariant node.
- `ctx.spawn` depth guard (`CapabilityContext.MAX_DEPTH = 16`, `capability.py:47`,
  raise at `:52-53`). `verify_invariants` *asserts* against this guard rather than
  replacing it — the engine's depth guard stays the runtime backstop; this verb is
  the auditable, recorded check.

### OntologyExtension — node types, enums, skills

**`agentic` extension:**

| Node | Required fields | Notes |
|---|---|---|
| `LoopSignal` | `confidence`, `detected` | an optional recorded loop-detection result (only if a caller chooses to persist one; `detect_loop` itself is pure and records nothing) |

- No `Invariant` node and no `Invariant.name` enum: `verify_invariants` records its
  verdict solely as a core `Gate` via `gate.check` (`gate.py:28`). The shared
  `Gate.name` is an *open* string and is deliberately NOT enum-constrained here (that
  would constrain `spec-review`/`quality-review` too). The gate names this verb uses
  (`depth_bound`, `no_orphans`) are documented conventions, not an ontology enum.
- Reuses core `Gate` (via `gate.check`), `Lifecycle`, `Invocation`. Edges: reuses
  `PASSED`/`BLOCKED_ON`/`SERVES`.

**`pressure` extension:**

| Node | Required fields | Notes |
|---|---|---|
| `Scenario` | `name`, `skill_under_test` | a pressure-test scenario |
| `PressureRun` | `scenario`, `with_skill`, `verdict` | one RED or GREEN run |

- Enum: `("PressureRun", "verdict"): {"compliant", "violation", "rationalised", "ambiguous"}`.
- Both extensions declare only *new* node labels/enums, so the strict ontology merge
  (`ontology.py:81-86`, raises only on *redefining* a core label) admits them; there
  is no label collision between the two extensions or with core.
- Skills (Lifecycle templates the walker walks):
  - `agentic-pressure-test` (kind `discipline`): `scenario → red(without-skill) →
    green(with-skill) → refactor(close-loopholes, hard)`. The phase ordering enforces
    RED-before-GREEN the same way `develop`'s `tdd` skill enforces the Iron Law.
  - `orchestrator-discipline` (kind `discipline`): `summarize → filter → confirm(hard)`
    — codifies summary-only / no-raw-dump orchestration (the L14 token rule), with a
    pressure scenario shipped under the skill so it is itself pressure-testable.

### Verb table (role-tagged)

**`agentic`:**

| Verb | Role | What | Provenance |
|---|---|---|---|
| `verify_invariants` | act | Assert depth-bound + no-orphaned-`working`-children over a delegation/subagent Lifecycle; record the verdict via `gate.check`. | one `Gate` via `gate` (PASS or BLOCKED_ON + pause); no `Invariant` node |
| `detect_loop` | transform | Jaccard-shingle loop detection (Plan-119 algorithm), threshold 0.7. Pure signal; callers supply messages/tool_results. | none (pure) |
| `spec_validate` | transform | RFC-2119 + Gherkin presence findings on spec text. | none (pure) |
| `confidence_check` | transform | Decidable pre-action confidence score + blocking list; `≥0.9` go-threshold. | none (pure) |

**`pressure`:**

| Verb | Role | What | Provenance |
|---|---|---|---|
| `load_scenario` | transform | Validate + normalize a pressure-scenario mapping. | none (pure) |
| `score_transcript` | transform | Pure string-pattern rubric → `{score, verdict, evidence}`; rationalisation flips verdict. | none (pure) |
| `run` | effect | Score a **caller-supplied** `transcript` against a scenario and record it; `dry_run` (v1 default) short-circuits to a synthetic `ambiguous`. Does NOT invoke an LLM (wet path deferred). | `PressureRun` recorded `SERVES` intent; scored `Gate` via `gate` |

Role rationale: the agentic *judgement* primitives (`detect_loop`, `spec_validate`,
`confidence_check`, `load_scenario`, `score_transcript`) are `transform` — decidable,
replayable, LLM-free, which is exactly what lets an autonomous loop trust them.
`verify_invariants` is an `act` (records a gate). `run` is tagged `effect` (it will
become a dispatcher when a local LLM driver exists), but in v1 it records provenance
over a supplied transcript and its `dry_run` path keeps the test suite LLM-free —
the same LLM-out-of-the-verb dodge `subagent.develop` uses (`subagent.py:24-25`).

### Loop detection (Plan 119 → `agentic.detect_loop`)

Pure re-implementation: `shingles(s) = {s[i:i+3] …}` after lower/whitespace-normalise;
Jaccard `|A∩B|/|A∪B|`; pairwise max over the last 4 messages + last 5 tool results
(≤ 81 pairs); `detected = max ≥ 0.7`; `evidence` names the two driving indices
(keep the index-citation requirement — Plan 119 anchor 119.1, `119:79-84`). Empty
inputs → `{detected:False, confidence:0.0, evidence:None}`. The 2-note-per-session
cap, 3-turn cooldown, `UserPromptSubmit` hook, and `session_log_query` message source
(`119:38-40`) are **out of scope for v1** — Agency has no hook layer or message store,
so the consumer is deferred to a future hooks spec (see Open Questions). v1 ships the
decidable signal only; the verb never sources its own history.

### Pressure-test framework (Plan 133 → `pressure` capability)

`load_scenario` mirrors the-agency-system's `Scenario` dataclass (≥3 pressures, the
compliant/violation/rationalisation lists; rejects a mapping missing a required key,
Plan 133 anchor 133.1). `score_transcript` is the pure rubric:
`score = max(0, min(100, 50 + 10*compliance - 15*violation))`; decision order
(1) any rationalisation hit → `rationalised`; (2) compliance ≥ violation and ≥1 →
`compliant`; (3) violation ≥1 → `violation`; (4) else → `ambiguous` (Plan 133 anchor
133.2: a transcript with both a compliant hit and "just this once" → `rationalised`,
never `compliant`). `run` scores a caller-supplied transcript and records the
`PressureRun` + scored `Gate`; the dry-run synthetic result keeps unit tests
deterministic and offline (Plan 133 anchor 133.3: `dry_run=True` → `RunResult` with
`verdict="ambiguous"` and no dispatch). The two shipped scenarios pressure-test
`orchestrator-discipline` and (for the `agentic-pressure-test` skill's own GREEN
baseline) `develop`'s `tdd` discipline — an *other* skill, sidestepping the circular
self-test problem.

### Migration / coverage map (the-agency-system → Agency)

| the-agency-system (Plan @ SHA) | Agency landing |
|---|---|
| 016 agentic handlers (32 decidable tools across specs/plans/workflows/research/ralph/confidence) | distilled to the 4 decidable `agentic` verbs (`spec_validate`, `confidence_check`, + `detect_loop`, `verify_invariants`); the rest are out-of-scope v1 (the `develop` skill family already covers plan/workflow disciplines) |
| 016 `dry_run` / `return_plan` / `ToolResult` envelope | Agency's analogue is the verb-result `{result: …}` shape + an explicit `dry_run` flag where an effect would mutate; no separate envelope (code-mode IS the contract) |
| 119 loop detection (UserPromptSubmit hook + Jaccard) | `agentic.detect_loop` transform (the pure signal) only; the hook/throttle/message-source are deferred to a future hooks spec — Agency has no hook layer |
| 133 skill subagent-pressure-tests (CLI + scenarios + rubric) | `pressure` capability (`load_scenario`/`score_transcript`/`run`) + the `agentic-pressure-test` skill; `run` scores a supplied transcript (the `subagent.develop` LLM-as-input dodge) instead of shelling out to `claude -p` |
| 016 agentic skill catalogue (~60 sc-*/superpowers-* skills) | OUT — already covered by the `develop` capability's disciplines + `skills/`; this spec adds only the two missing discipline skills |
| token-budget invariants / loop-depth middleware (catalogue row 24) | `agentic.verify_invariants` asserts against the engine's existing `MAX_DEPTH` guard (`capability.py:47-55`) rather than adding middleware |

Note the deliberate divergence from `research/capability-specs/specs/agentic.md`,
which proposed engine-level loop-detection middleware and a `core.py` edit
(`research/capability-specs/specs/agentic.md` `affects: agency/core.py`). **There is
no `core.py` and no `core/` package** in Agency — the substrate is `agency/engine.py`
+ `agency/capability.py`. The depth guard already lives in `CapabilityContext.spawn`
(`capability.py:49-55`, `MAX_DEPTH=16` at `:47`), and `verify_invariants` audits it as
a recorded `act` — so no engine edit is needed and none is being "spared"; the
research draft's edit targeted a file that does not exist.

## Files

- **Create**:
  - `agency/capabilities/agentic.py` — `AgenticCapability` + its `OntologyExtension`.
  - `agency/capabilities/pressure.py` — `PressureCapability` + its `OntologyExtension`
    (scenario/rubric helpers may live as module functions, mirroring `develop.py`).
  - `skills/agentic-pressure-test/SKILL.md` — the discipline skill (+ a
    `scenarios/` example or two, pressure-testing `develop`'s `tdd`; cross-links
    `develop.py:86-94` rather than restating the doctrine).
  - `skills/orchestrator-discipline/SKILL.md` — the orchestration discipline skill.
  - `docs/examples/pressure_test_a_skill.py` — runnable dry-run example.
  - `tests/test_agentic_capability.py`, `tests/test_pressure_capability.py`.
- **No edit required**: `agency/capabilities/__init__.py` — `discover()` walks the
  package by reflection (`pkgutil.iter_modules` + `issubclass`) and `engine.py`
  registers whatever it returns, so dropping the two modules self-registers them.
- **Do not modify**: `agency/engine.py`, `agency/capability.py`, `agency/ontology.py`,
  and the existing `delegate`/`subagent`/`gate`/`develop` capabilities — this spec
  composes with them. (There is no `core.py` to leave untouched.)

## Acceptance (Gherkin — ported anchors)

```gherkin
# anchor: 119.1 (detect_loop)
Scenario: Identical repeated tool result triggers loop detection at confidence 1.0
  Given a window of 5 tool results where indices 0, 2, and 4 are byte-identical
  When agentic.detect_loop(messages=[], tool_results=window) is called
  Then result.detected is True
  And result.confidence == 1.0
  And result.evidence references two of the duplicate indices

# anchor: 133.2 (score_transcript)
Scenario: Rubric flips verdict to "rationalised" when patterns match
  Given a transcript containing both "ran pytest" (compliant) and "just this once" (rationalisation)
  When pressure.score_transcript(transcript, scenario) is called
  Then the verdict is "rationalised"
  And the verdict is NOT "compliant" regardless of raw score

# anchor: 133.3 (run, dry_run)
Scenario: Dry-run run produces an ambiguous verdict without an LLM dispatch
  Given a valid scenario and dry_run=True
  When pressure.run(scenario=scenario, dry_run=True) is invoked
  Then a result is returned with verdict == "ambiguous"
  And no worker is dispatched
```

## Open Questions / Needs Research

1. **Loop-detection hook + message source (DEFERRED, decided for v1).** v1 ships the
   pure `detect_loop` verb only; the `UserPromptSubmit` hook, 2-note/3-turn throttle,
   and the message source are out of scope (Agency has no hook layer or message
   store). The open question for the *future* hooks spec: where does session-message
   history come from — a host-supplied buffer, or an `Invocation`-result traversal of
   the graph? Recorded here so it is not lost, but it does NOT block v1.
2. **`verify_invariants` post-hoc vs pre-admission (RESOLVED).** A recorded post-hoc
   `act` is the right shape and honours "do not modify `delegate`". Admission is
   already enforced inside `fan_out` (it caps at `quota` and rejects `quota<0`,
   `delegate.py:33-39`), so a "quota respected" post-hoc check would be tautological —
   it is therefore DROPPED. The genuinely checkable invariant is "no orphaned
   `working` children" (children start `working` at `delegate.py:48`; only
   `subagent`/`join` move them to `completed`, `subagent.py:38`), which `delegate`
   does not itself enforce.
3. **`pressure.run` wet path (DEFERRED, decided for v1).** v1's `run` scores a
   caller-supplied transcript (the `subagent.develop` LLM-as-input pattern) and the
   only runnable path is `dry_run`. A *future* wet path needs a local-subagent LLM
   driver that returns scoreable text — Agency ships none (`jules` returns session
   JSON, `jules.py:79-80`; `delegate.fan_out` returns the raw verb `result`,
   `delegate.py:52-56`). Adding that driver is a separate spec.
4. **Scope of the agentic primitives (RESOLVED — accept as scoped).** Plan 016 had 32
   tools; this spec keeps 4 decidable ones and the rest are covered by `develop`'s
   disciplines. `workflow_decompose`/`ralph_render` stay OUT (they are orchestration
   disciplines, not decidable transforms).
5. **Are these core or examples/? (RESOLVED — core.)** The agentic layer is
   engine-discipline and sits beside `delegate`/`subagent`/`gate`; `pressure` belongs
   in core too. (Domain content → `examples/`; engine → `agency/capabilities/`.)
6. **Skill self-test bootstrapping (DEFER as known limitation).** `agentic-pressure-test`
   tests discipline skills; for its own GREEN baseline it ships a scenario that tests
   *another* skill (`develop`'s `tdd`), avoiding a circular GREEN. Pressure-testing the
   skill against itself is a noted future limitation, not a v1 blocker.

## Evidence

- Exemplar spec format: `/home/user/the-agency-system/Plan/108-context-mode-integration/spec.md`
- Research (the divergence source): `/home/user/agency/research/capability-specs/specs/agentic.md`
  (proposed the non-existent `core.py` edit),
  `/home/user/agency/research/capability-specs/capability-catalogue.md` (rows 22-28).
- Agency composition surface: `/home/user/agency/agency/capabilities/delegate.py`
  (`fan_out`/`join` — returns the raw verb `result`, not a transcript, `:52-56`; quota
  admission `:33-39`; children start `working` `:48`),
  `/home/user/agency/agency/capabilities/subagent.py` (dispatch + two-stage gated
  review; takes verdicts as INPUTS `:24-25` — the LLM-out-of-the-verb pattern
  `pressure.run` mirrors; moves a verified child to `completed` `:38`),
  `/home/user/agency/agency/capabilities/gate.py` (records a `Gate` only `:28`; rejects
  cross-intent lifecycles `:23-27`),
  `/home/user/agency/agency/capabilities/develop.py` (`review` binds a phase to
  `delegate.fan_out` `:65-71`; `REFERENCES["testing-skills"]` carries the pressure-test
  doctrine `:86-94` — prior art this spec cross-links),
  `/home/user/agency/agency/capability.py` (`CapabilityContext.spawn` `MAX_DEPTH=16`
  guard `:47-55`; `@verb` roles `:84-90`),
  `/home/user/agency/agency/capabilities/__init__.py` (`discover()` reflection — why no
  edit is needed).
- Source depth (the-agency-system @ 0a6a9e71): `Plan/016-agentic-handlers-and-skills`
  (the decidable agentic surface + dry_run/ToolResult discipline), `Plan/119-loop-detection`
  (the Jaccard-shingle algorithm + thresholds + the deferred hook/throttle/source),
  `Plan/133-skill-subagent-pressure-tests` (the Scenario dataclass, the pure rubric,
  the RED/GREEN/REFACTOR cycle, anchors 133.1-133.3),
  `Plan/135-spec-test-anchor-traceability` (the anchor-citation convention used above).
