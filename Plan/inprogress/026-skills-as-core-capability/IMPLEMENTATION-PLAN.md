# Spec 026 — IMPLEMENTATION-PLAN

Loop output: Design (v1) → spec-panel (REVISE, 6 findings folded) → Design (v2)
→ **Workflow**. Per-phase RED → GREEN → green `python -m pytest -q` → commit
→ push. Phase 0 ships the convergence baseline ALONE so the gate has a number
before any new surface lands. Review checkpoint after Phase 3 (the projection
surface) and at Phase 5 (the binary convergence gate).

Ordered: measure first (0), ontology (1), read-only registry (2), projection
(3), chain convention (4), re-measure (5), close the loop (6).

---

## Phase 0 — Baseline Jules-flow benchmark (NO NEW SURFACE) ⚓

Convergence gate (panel F7) compares Spec-026 to status-quo numbers. Those
numbers must EXIST before Phase 1 ships anything that could move them.

### 0.1 RED
- `tests/test_jules_workflow_dispatch.py::test_status_quo_baseline_recorded`:
  fails until `tests/fixtures/jules_baseline.json` exists with the three
  metrics filled.

### 0.2 GREEN
- `tests/test_jules_workflow_dispatch.py` — ONE function:
  - **LOC**: reads `AGENCY_PROTOCOL.md` §5 (lines 99-131) + §9 (158-193)
    and counts the orchestrator-side `e.invoke(...)` / `git ls-remote` /
    branching `if branch_on_remote:` lines a faithful impl needs.
  - **tiktoken cost**: instantiates a real engine, invokes the four steps
    against a mocked Jules session (reuse `tests/fixtures/jules/*.patch`
    + stub `jules.{status,verify,message,patch}` returns), sums
    `tiktoken.encoding_for_model("gpt-4").encode(...)` over every tool
    return envelope the orchestrator must read.
  - **manual decisions**: counts the `if`/`elif` the orchestrator owns to
    discriminate the §1 four-COMPLETED cases + §5 recovery routing + §9
    review handshake.
  - Writes `tests/fixtures/jules_baseline.json`:
    `{loc, tokens, manual_decisions, recorded_at, spec_rev}`.
  - Asserts the fixture is readable; the three integers are >0.

  Open in implementation: LOC rule (whole §5 vs only outside helpers) —
  pick one, document inline, reuse in Phase 5 via a shared helper.

### 0.3 Gate
- New test green; fixture committed; full suite green. **Commit + push.**
  No other change in this commit.

### Risks
- LOC count subjective → rule documented in module docstring; SAME rule
  reused in Phase 5 via shared helper.
- tiktoken cost varies with mock fidelity → pin mock returns to fixed
  strings drawn from `_jules_skills.py` + `AGENCY_PROTOCOL.md`; record
  input corpus hash.

---

## Phase 1 — Skill/Phase/Gate/Matcher node schemas + pinned JSON Schema

Additive ontology change. No new behaviour. The 17 existing skills round-trip
unchanged.

### 1.1 RED
- `tests/test_skills_capability.py::test_skill_phase_gate_matcher_nodes_registered`:
  the four node types exist in `OntologyExtension` after engine build.
- `…::test_matcher_schema_pinned_in_ontology_extension`: an invalid Matcher
  (e.g. `{"kind":"bogus"}`) raises at `record`/`link` per the pinned JSON
  Schema (panel F3b).
- `…::test_all_existing_skills_walkable_unchanged`: every entry in
  `Capability.ontology.skills` across the 17 still parses + walks via
  `SkillRun` (no `applies_when` required).

### 1.2 GREEN
- `agency/ontology.py` — `Skill`, `Phase`, `Gate`, `Matcher` node types;
  `APPLIES_WHEN`, `CHAINS_TO`, `MATCHED_BY` edges; `Skill.kind ∈
  {discipline, authoring, workflow}` enum.
- `agency/ontology.py:OntologyExtension.schemas` — pin the Matcher JSON
  Schema (spec §Matcher definition) so `record`/`link` reject drift.
- `agency/capability.py` — at registration, promote every
  `Capability.ontology.skills[name]` to a `Skill` graph node + `Phase`
  children. No `applies_when` reading yet.

### 1.3 Gate
- New tests green; full suite green (incl. existing skill-walk tests).
  **Commit + push.**

### Risks
- Promotion changes graph counts; downstream tests assert counts → spec
  verified `grep "memory.find\|graph_count" tests/` returns nothing today;
  update any surface in the SAME PR.
- Matcher schema too strict → `oneOf` on `kind`; adding a fourth is one diff.

---

## Phase 2 — `skills.py` capability (find / render / lint, NO dispatch)

Read-only registry. TDD against the three real reference skills:
`plugin.skill-creation`, `delegate.dispatch-decision`,
`jules.jules-dispatch` & `jules.jules-fanout`.

### 2.1 RED
- `tests/test_skills_capability.py::test_find_lists_all_registered_skills`:
  `skills.find()` returns ≥17.
- `…::test_find_filters_by_kind_and_capability`: filter combos return the
  expected subsets.
- `…::test_render_skill_creation_t1_t2_t3`: `depth="brief"` returns
  ≤120-char cue; `depth="full"` returns instruction+produces+gate per
  phase — bytes match Spec-025 `render_phase` for the same inputs.
- `…::test_lint_dispatch_decision_passes`: `{ok:True, violations:[]}`.
- `…::test_lint_rejects_malformed_matcher`: hand-built skill with
  `applies_when={"kind":"bogus"}` lints with ≥1 violation.
- `…::test_duplicate_skill_collision_raises_at_registration` (panel F6b).

### 2.2 GREEN
- `agency/capabilities/skills.py` (~150 LOC) — `SkillsCapability
  (CapabilityBase)`:
  - `find(intent_id=None, *, kind=None, capability=None)` — registry
    browse via graph query. `transform`.
  - `render(skill_name, *, depth='brief', phase_index=None, intent_id=None)`
    — delegates to Spec-025 `render_phase`. `transform`.
  - `lint(skill_name)` — phase-shape + Matcher-schema validation.
    `transform`.
- Register via `agency/capabilities/__init__.py`.

### 2.3 Gate
- New tests green; full suite green. **Commit + push.**

### Risks
- `skills.render` duplicates Spec-025 `render_phase` → import + delegate;
  render-bytes assert in the test enforces identity.
- Duplicate-name check fires on legitimate aliases → same check in
  `ontology.py:114-117`; this just moves the layer.

---

## Phase 3 — `intent.suggests_skill` verb (three Matcher modes + cycle-check)

The central projection. **effect** role. TDD'd against the three real
examples; failure semantics covered.

### 3.1 RED
- `tests/test_intent_suggests_skill.py::test_pattern_match_skill_creation`:
  intent purpose mentions skill authoring → returns
  `{skill:"skill-creation", mode:"pattern", confidence ≥0.5, cue:str}`.
- `…::test_verb_code_match_dispatch_decision`: delegation-shaped intent →
  `mode:"verb_code", skill:"dispatch-decision"`; the
  `delegate.dispatch_decision` verb was invoked as decider.
- `…::test_llm_select_picks_between_jules_dispatch_and_fanout`: batch-shaped
  intent → `jules-fanout`; single-target → `jules-dispatch`. `ctx.sample`
  stubbed to return canonical JSON.
- `…::test_matcher_timeout_demotes_to_next_mode`: `budget_ms=1` against a
  sleeping decider → demotes, no exception; a
  `Reflection{scope:"technical", text:"matcher … failed: …"}` was written.
- `…::test_llm_select_gibberish_demotes`: `ctx.sample` returns non-JSON →
  demotes, never raises.
- `…::test_decider_cycle_raises_at_registration`: 3-hop cycle across two
  capabilities → engine build raises with a clear cycle error.
- `…::test_returns_none_when_no_matcher_applies`: matcher-less intent →
  `None` (Open Question #2 — Recommend: return None).

### 3.2 GREEN
- `agency/capabilities/intent.py` — add `suggests_skill`:
  - Loads candidate Skills (graph query — those with `applies_when`).
  - Walks matchers in deterministic order (sorted by `min_confidence`
    desc, then name) applying kind-specific predicate within `budget_ms`.
  - On timeout / exception / sub-threshold / parse error: write a
    Reflection, demote to next candidate.
  - Returns `{skill, mode, confidence, cue, matched_by} | None`.
  - `cue` via `skills.render(skill_name, depth='brief',
    intent_id=intent_id)`.
- `agency/capability.py:Registry._wire_skill_tags` — DFS cycle detection
  over `verb_code` matchers; raise at engine build on cycle.
- Add `applies_when` Matcher payloads to the three reference skills
  (spec §Three REAL reference examples).
- Cache key: `(intent_id, matcher_key, intent.version)` with `cache_ttl_s`
  (Open Question #3 — version-keyed for free invalidation).

  Open in implementation: tie-breaker when two candidates share
  `min_confidence` (spec under-specifies). Current plan: alphabetical by
  skill name; document in verb docstring.

### 3.3 Gate
- New tests green; full suite green. **Commit + push.**

### 3.4 REVIEW CHECKPOINT — `agency:code-review` on the
`intent.suggests_skill` diff (the load-bearing surface).

### Risks
- DFS misses indirect cycles via shared deciders → cycle test uses 3-hop;
  DFS visits-set covers arbitrary depth.
- `ctx.sample` cost balloons in CI → `llm_select` stubbed in all unit
  tests; real LLM only in Phase 5.

---

## Phase 4 — Return-shape convention (`next_skill`) + `engine._wire`

No new verb. Pure convention. The engine preserves `next_skill` through.

### 4.1 RED
- `tests/test_intent_suggests_skill.py::test_next_skill_field_preserved_by_wire`:
  a verb returning `{result:..., next_skill:{name, cue, confidence,
  matched_by}}` — after `engine._wire` → MCP envelope, `next_skill` is
  intact, not unwrapped.
- `…::test_orchestrator_can_chain_via_next_skill`: integration —
  `jules.dispatch(intent_id=...)` returns a payload whose `next_skill`
  names `jules-recovery-when-stuck` when the stub session is
  `COMPLETED+plan_unapproved`; `jules-pr-review-cycle` when PR-review
  comments are present.

### 4.2 GREEN
- `agency/engine.py:_wire` — preserve `next_skill` when present on a verb
  return (no unwrap, no strip). ~5 LOC.
- `agency/capabilities/jules.py` — `dispatch` / `verify` / `status` opt
  in: when `intent_id` is in call scope, call `intent.suggests_skill`
  inline pre-return; embed result as `next_skill`.

  Open in implementation: which other Jules verbs opt in. v1: dispatch /
  verify / status — enough for the §5 recovery + §1 routing. Others
  follow only if Phase 5 needs them.

### 4.3 Gate
- New tests green; full suite green. **Commit + push.**

### Risks
- `_wire` strips unknown fields → current behaviour is pass-through; test
  byte-asserts the `next_skill` sub-dict.
- Inline projection cost on every return → only when `intent_id` in scope;
  measured in Phase 5.

---

## Phase 5 — Convergence measurement (the binary gate) 🎯

Re-run the Phase-0 benchmark with Spec 026 active. The test asserts the
≥50% reduction. PASS or FAIL is the binary convergence answer.

### 5.1 RED
- `tests/test_jules_workflow_dispatch.py::test_spec_026_converges_vs_baseline`:
  re-runs the same three-metric measurement against the Spec-026 surface
  (orchestrator calls `intent.suggests_skill` instead of hand-routing).
  Reads `tests/fixtures/jules_baseline.json`. Asserts:
  - `spec_026.loc ≤ 0.5 * baseline.loc`, AND
  - `spec_026.manual_decisions ≤ 0.5 * baseline.manual_decisions`.
  - Tokens recorded for the report; NOT in the assert (panel F7's rule
    cites LOC + manual decisions; tokens decide the 025-vs-026 tiebreak
    in the alt branch).
- Emits `tests/fixtures/jules_spec026_result.json`:
  `{baseline, spec_026, delta_pct}`.

### 5.2 GREEN
- Wire the orchestrator-side fake-flow used in Phase 0 to call
  `intent.suggests_skill` between the four canonical steps. Same mocks;
  only the orchestrator surface differs.
- Re-use the LOC counting helper from Phase 0 (rule must be stable
  across both runs — apples to apples).
- If the assertion FAILS: do NOT tune the assertion. Stop here; Phase 6
  routes the failure.

### 5.3 Gate
- Test green (convergence achieved) OR explicit FAIL with comparison
  report attached. Full suite green regardless. **Commit + push** the
  result fixture either way.

### Risks
- Misses ≥50% by a hair → spec §Convergence is binary; do NOT relax;
  route via Phase 6.
- LOC rule drift Phase 0 ↔ Phase 5 → shared helper imported by both tests.

---

## Phase 6 — Review + Improve (loop exit)

`agency:code-review` pass on the cumulative diff. Then the binary fork:

### 6.1 If Phase 5 PASSED
- Narrow `Plan/inprogress/025-skill-first-discovery/spec.md` → discovery-only (drop
  `skill_walk`/`skill_step` if subsumed by the projection; or keep as a
  zero-dispatch walker for intent-less cases). Per spec §F7:
  "Spec 026 ships, Spec 025 becomes discovery layer only."
- Update `CLAUDE.md` doctrine — add `intent.suggests_skill` as the
  canonical way to thread multi-skill workflows; orchestrators stop
  hand-routing.
- Flip Spec 026 `status: done`.

### 6.2 If Phase 5 FAILED
- Re-enter Design with the measurement as evidence:
  `Plan/026-…/REVISION-1.md` carrying the comparison-report JSON.
- Per spec §F7 alt branches: if 025/026 produce identical orchestration
  AND 025 wins on tokens → write Spec 027 (discovery-first only). If
  neither significantly improves → propose a third approach.
- Spec 026 stays `draft`; Spec 025 Phase-2+ stays gated.

### 6.3 Gate
- Reviewer sign-off. Doctrine change (if PASS) committed; revision
  drafted (if FAIL). **Commit + push.**

---

## Test additions
```
tests/test_jules_workflow_dispatch.py     # Phase 0 (baseline) + Phase 5 (convergence)
tests/fixtures/jules_baseline.json        # Phase 0 — committed fixture
tests/fixtures/jules_spec026_result.json  # Phase 5 — committed comparison report
tests/test_skills_capability.py           # Phases 1, 2
tests/test_intent_suggests_skill.py       # Phases 3, 4
```

## Risk register (cross-phase)
| Risk | Mitigation |
|---|---|
| Phase 0 LOC rule disputed | Documented in test docstring; the gate is the *delta*, not the absolute. |
| Matcher schema too strict for future modes | `oneOf` on `kind`; adding a fourth is one diff. |
| Decider cycles slip past DFS | Phase 3 test uses a 3-hop cycle to exercise the visits-set. |
| Spec 025 + 026 collide on `render_phase` | Phase 2 imports + delegates; parallel by design (`parallel_to:["025"]`). |
| Phase 5 unstable across runs | All Jules calls mocked from `tests/fixtures/jules/*.patch` + frozen stubs; no network, no LLM in CI. |
| `next_skill` opt-in inconsistent | v1 covers `jules.{dispatch,verify,status}` — enough for §5 + §1; others follow only if benchmark needs them. |
