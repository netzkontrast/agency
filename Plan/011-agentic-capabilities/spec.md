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
two-stage gated review), and `gate` (the reusable hard-gate predicate). What is
missing is the **agentic-discipline** half — the verbs and skills that make
autonomous loops safe and self-correcting, and that let an author *pressure-test*
their own discipline skills before shipping them. This spec adds an `agentic`
capability (decidable agentic primitives) and a `pressure` capability (the
TDD-for-skills framework), plus the two discipline skills they surface, **without
re-deriving** `delegate`/`subagent`/`gate` — it composes with them.

Because these are engine-domain (not a content domain), they ship in the core
`agency/capabilities/` package and self-register exactly like `delegate` and
`subagent`. **Code-mode IS the contract**: the verbs are discovered via `search`
and called from inside `execute`; there is no bespoke agentic tool surface.

## Done When

- [ ] `agency/capabilities/agentic.py` defines `AgenticCapability(CapabilityBase)`
  (`name="agentic"`, `home="lifecycle"`) that self-registers (discovered by
  `Engine` reflection — no edit to `engine.py`).
- [ ] `agency/capabilities/pressure.py` defines `PressureCapability` (`name="pressure"`,
  `home="lifecycle"`) carrying the pressure-scenario + rubric ontology.
- [ ] The `agentic` verb table (below) is implemented and role-tagged; every verb
  is **decidable** (pure `transform`) or records real provenance (`act`) — none
  requires an LLM at call time.
- [ ] `agentic.verify_invariants(lifecycle_id, max_depth=..., quota_used=...)`
  (act) asserts the structural invariants over a delegation/subagent run (depth ≤
  `ctx.MAX_DEPTH`, quota respected, no orphaned `working` children) and records a
  `Gate` via `gate.check` — PASS or `BLOCKED_ON` + an `input-required` pause.
- [ ] `agentic.detect_loop(messages, tool_results)` (transform) re-implements the
  Plan-119 Jaccard-on-3-char-shingles algorithm (last 4 msgs + last 5 tool results,
  pairwise max, threshold 0.7) and returns `{detected, confidence, evidence}` —
  stdlib only, no `numpy`/`rapidfuzz`.
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
- [ ] `pressure.run` (effect) dispatches a fresh worker child via `delegate.fan_out`
  (RED = without-skill, GREEN = with-skill), captures the transcript, and scores it
  via `score_transcript`; a `dry_run=True` path short-circuits before dispatch and
  returns a synthetic `ambiguous` result (so tests never need a live LLM).
- [ ] The two skills install and lint clean (`plugin.lint_skill`):
  `skills/agentic-pressure-test/SKILL.md` (kind `discipline`, the 4-phase
  RED→GREEN→REFACTOR→STAY-GREEN cycle) and `skills/orchestrator-discipline/SKILL.md`
  (kind `discipline`, the token/summary-only orchestration rule).
- [ ] `pytest -q tests/test_agentic_capability.py tests/test_pressure_capability.py`
  passes; the baseline suite (`pytest -q`) still passes (no regression).
- [ ] `python docs/examples/pressure_test_a_skill.py` runs the dry-run path
  end-to-end and prints the recorded provenance (scenario → run Lifecycle →
  scored Gate).

## Design

### Relationship to the existing orchestration capabilities

This spec is **additive and compositional** — it never reimplements:

- `delegate.fan_out`/`join` — child-Lifecycle orchestration under a quota. `pressure.run`
  dispatches its worker through `delegate.fan_out(quota=1)` (the same path `subagent`
  uses), so a pressure run is a connected provenance subgraph by construction.
- `subagent.develop` — dispatch + two-stage gated review. `agentic.verify_invariants`
  is the *post-hoc* structural check over whatever `subagent`/`delegate` produced.
- `gate.check` — the hard-gate predicate. `verify_invariants` and `confidence_check`
  record their verdicts through `gate.check` so a failed agentic gate is provenance
  and pauses the Lifecycle for re-entry (no new gate mechanism invented).
- `ctx.spawn` depth guard (`CapabilityContext.MAX_DEPTH = 16`). `verify_invariants`
  *asserts* against this guard rather than replacing it — the engine's depth guard
  stays the runtime backstop; this verb is the auditable, recorded check.

### OntologyExtension — node types, enums, skills

**`agentic` extension:**

| Node | Required fields | Notes |
|---|---|---|
| `Invariant` | `name`, `holds` | one recorded invariant assertion |
| `LoopSignal` | `confidence`, `detected` | a recorded loop-detection result |

- Enums: `("Invariant", "name"): {"depth_bound", "quota_respected", "no_orphans"}`.
- Reuses core `Gate` (via `gate.check`), `Lifecycle`, `Invocation`. Edges: reuses
  `PASSED`/`BLOCKED_ON`/`SERVES`.

**`pressure` extension:**

| Node | Required fields | Notes |
|---|---|---|
| `Scenario` | `name`, `skill_under_test` | a pressure-test scenario |
| `PressureRun` | `scenario`, `with_skill`, `verdict` | one RED or GREEN run |

- Enum: `("PressureRun", "verdict"): {"compliant", "violation", "rationalised", "ambiguous"}`.
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
| `verify_invariants` | act | Assert depth-bound, quota-respected, no-orphaned-children over a delegation/subagent Lifecycle; record each via `gate.check`. | one `Gate` per invariant via `gate`; `Invariant` nodes recorded |
| `detect_loop` | transform | Jaccard-shingle loop detection (Plan-119 algorithm), threshold 0.7, max-2 advisory. | none (pure) |
| `spec_validate` | transform | RFC-2119 + Gherkin presence findings on spec text. | none (pure) |
| `confidence_check` | transform | Decidable pre-action confidence score + blocking list; `≥0.9` go-threshold. | none (pure) |

**`pressure`:**

| Verb | Role | What | Provenance |
|---|---|---|---|
| `load_scenario` | transform | Validate + normalize a pressure-scenario mapping. | none (pure) |
| `score_transcript` | transform | Pure string-pattern rubric → `{score, verdict, evidence}`; rationalisation flips verdict. | none (pure) |
| `run` | effect | Dispatch a worker via `delegate.fan_out(quota=1)`, capture + score the transcript; `dry_run` short-circuits. | `PressureRun` recorded `SERVES` intent; worker child via `delegate`; scored `Gate` via `gate` |

Role rationale: the agentic *judgement* primitives (`detect_loop`, `spec_validate`,
`confidence_check`, `load_scenario`, `score_transcript`) are `transform` — decidable,
replayable, LLM-free, which is exactly what lets an autonomous loop trust them.
`verify_invariants` is an `act` (records gates). `run` is the only `effect` (it
dispatches a real worker), and its `dry_run` path keeps the test suite LLM-free.

### Loop detection (Plan 119 → `agentic.detect_loop`)

Pure re-implementation: `shingles(s) = {s[i:i+3] …}` after lower/whitespace-normalise;
Jaccard `|A∩B|/|A∪B|`; pairwise max over the last 4 messages + last 5 tool results
(≤ 81 pairs); `detected = max ≥ 0.7`; `evidence` names the two driving indices. The
2-note-per-session cap and 3-turn cooldown from Plan 119 are a *consumer* concern
(an advisory loop in a host hook), not part of the pure verb — the verb is the
decidable signal; throttling is left to whoever wires it (see Open Questions on
hooks).

### Pressure-test framework (Plan 133 → `pressure` capability)

`load_scenario` mirrors the-agency-system's `Scenario` dataclass (≥3 pressures, the
compliant/violation/rationalisation lists). `score_transcript` is the pure rubric:
`score = max(0, min(100, 50 + 10*compliance - 15*violation))`; decision order
(1) any rationalisation hit → `rationalised`; (2) compliance ≥ violation and ≥1 →
`compliant`; (3) violation ≥1 → `violation`; (4) else → `ambiguous`. `run` composes
`delegate.fan_out` for the actual dispatch; the dry-run synthetic result keeps unit
tests deterministic and offline. The two shipped scenarios pressure-test
`orchestrator-discipline` and (self-referentially) the `tdd` discipline from the
existing `develop` capability.

### Migration / coverage map (the-agency-system → Agency)

| the-agency-system (Plan @ SHA) | Agency landing |
|---|---|
| 016 agentic handlers (32 decidable tools across specs/plans/workflows/research/ralph/confidence) | distilled to the 4 decidable `agentic` verbs (`spec_validate`, `confidence_check`, + `detect_loop`, `verify_invariants`); the rest are out-of-scope v1 (the `develop` skill family already covers plan/workflow disciplines) |
| 016 `dry_run` / `return_plan` / `ToolResult` envelope | Agency's analogue is the verb-result `{result: …}` shape + an explicit `dry_run`/`apply` flag where an effect would mutate; no separate envelope (code-mode IS the contract) |
| 119 loop detection (UserPromptSubmit hook + Jaccard) | `agentic.detect_loop` transform (the pure signal); the hook/throttle is a host concern |
| 133 skill subagent-pressure-tests (CLI + scenarios + rubric) | `pressure` capability (`load_scenario`/`score_transcript`/`run`) + the `agentic-pressure-test` skill; `run` composes `delegate` instead of shelling out to `claude -p` |
| 016 agentic skill catalogue (~60 sc-*/superpowers-* skills) | OUT — already covered by the `develop` capability's disciplines + `skills/`; this spec adds only the two missing discipline skills |
| token-budget invariants / loop-depth middleware (catalogue row 24) | `agentic.verify_invariants` asserts against the engine's existing `MAX_DEPTH` guard rather than adding middleware to `core.py` |

Note the deliberate divergence from `research/capability-specs/specs/agentic.md`,
which proposed engine-level loop-detection middleware and a `core.py` edit. Agency's
contract makes that unnecessary: the depth guard already lives in
`CapabilityContext.spawn`, and `verify_invariants` audits it as a recorded `act` —
so this spec leaves `core.py`/`engine.py` untouched and keeps everything in
self-registering capability files.

## Files

- **Create**:
  - `agency/capabilities/agentic.py` — `AgenticCapability` + its `OntologyExtension`.
  - `agency/capabilities/pressure.py` — `PressureCapability` + its `OntologyExtension`
    (scenario/rubric helpers may live as module functions, mirroring `develop.py`).
  - `skills/agentic-pressure-test/SKILL.md` — the discipline skill (+ a
    `scenarios/` example or two, pressure-testing `develop`'s `tdd`).
  - `skills/orchestrator-discipline/SKILL.md` — the orchestration discipline skill.
  - `docs/examples/pressure_test_a_skill.py` — runnable dry-run example.
  - `tests/test_agentic_capability.py`, `tests/test_pressure_capability.py`.
- **Modify**:
  - `agency/capabilities/__init__.py` — only if `discover()` needs the new modules
    listed explicitly; if discovery is by package reflection, no edit is required
    (verify against the existing `discover()` mechanism).
- **Do not modify**: `agency/core` engine/capability/ontology, and the existing
  `delegate`/`subagent`/`gate` capabilities — this spec composes with them.

## Open Questions / Needs Research

1. **Loop-detection wiring.** `detect_loop` is a pure verb; the Plan-119 value comes
   from a `UserPromptSubmit` hook that throttles to 2 notes/session. Agency has no
   hook layer in scope here. Do we ship just the verb (v1), or also a hook/CLI that
   consumes it? Where would session-message history come from in Agency's model
   (the graph? a host-supplied buffer)?
2. **`verify_invariants` vs the engine depth guard.** The engine already raises at
   `MAX_DEPTH=16` inside `ctx.spawn`. Is a recorded *post-hoc* invariant check the
   right shape, or should invariants be asserted *during* `delegate.fan_out`
   (pre-admission)? The latter would mean touching `delegate` — explicitly avoided
   here; confirm that is the right call.
3. **`pressure.run` worker driver.** `run` composes `delegate.fan_out`, which needs
   a driver capability/verb that actually invokes an LLM-bearing subagent. Agency's
   only shipped driver is `jules` (remote). Is there (or should there be) a
   local-subagent driver, or does `run`'s wet path require `jules` + a live
   `JULES_API_KEY`? (The `dry_run` path sidesteps this for tests.)
4. **Scope of the agentic primitives.** Plan 016 had 32 tools; this spec keeps 4
   decidable ones and argues the rest are covered by `develop`. Is `spec_validate`/
   `confidence_check` enough, or do we need `workflow_decompose`/`ralph_render`
   analogues as verbs vs. as `develop` skills?
5. **Are these core or examples/?** Unlike novel (Spec 010, a content domain →
   `examples/`), the agentic layer is engine-discipline and sits beside
   `delegate`/`subagent`. v1 puts it in core `agency/capabilities/`. Confirm that is
   right, or whether `pressure` (which dispatches workers) belongs nearer the
   orchestration cluster.
6. **Skill self-test bootstrapping.** `agentic-pressure-test` is a discipline skill
   that exists to test discipline skills — should it ship a scenario that
   pressure-tests *itself*, and how do we avoid a circular GREEN-baseline?

## Evidence

- Exemplar spec format: `/home/user/the-agency-system/Plan/108-context-mode-integration/spec.md`
- Research: `/home/user/agency/research/capability-specs/specs/agentic.md`,
  `/home/user/agency/research/capability-specs/capability-catalogue.md` (rows 22-28).
- Agency composition surface: `/home/user/agency/agency/capabilities/delegate.py`
  (`fan_out`/`join` over child Lifecycles + quota), `/home/user/agency/agency/capabilities/subagent.py`
  (dispatch + two-stage gated review — the pattern `pressure.run` extends),
  `/home/user/agency/agency/capabilities/gate.py` (the hard-gate predicate
  `verify_invariants`/`confidence_check` record through),
  `/home/user/agency/agency/capabilities/develop.py` (discipline-skill-as-Lifecycle-template
  template, incl. the `tdd` Iron-Law ordering this spec mirrors),
  `/home/user/agency/agency/capability.py` (`CapabilityContext.spawn` MAX_DEPTH guard
  + `@verb` roles), `/home/user/agency/agency/skill.py` (walker: ordering + hard gate).
- Source depth (the-agency-system @ 0a6a9e71): `Plan/016-agentic-handlers-and-skills`
  (the decidable agentic surface + dry_run/ToolResult discipline), `Plan/119-loop-detection`
  (the Jaccard-shingle algorithm + thresholds), `Plan/133-skill-subagent-pressure-tests`
  (the Scenario dataclass, the pure rubric, the RED/GREEN/REFACTOR cycle).
