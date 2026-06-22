# Spec 025 — IMPLEMENTATION-PLAN

Loop output: Design → spec-panel (8 findings folded) → **Workflow**. Per-phase
RED → GREEN → green `python -m pytest -q` → commit → push. Review checkpoint
after Phase 3 (the search-shape change) and Phase 6 (acceptance). Loop re-enters
Design if the token-budget exit condition misses.

Ordered lowest-risk-additive first, so each phase ships independently and the
search-shape change (the only back-compat-sensitive one) lands mid-sequence on
a proven base.

---

## Phase 1 — verb→skill tags + `render_phase` (additive, zero behaviour change)

### 1.1 RED
- `tests/test_skill_first_discovery.py::test_verbs_tagged_with_their_skill`:
  every verb a skill phase binds to (the `invoke` field in any
  `ontology.skills`) carries a `skill:<name>` tag after engine build.
- `tests/test_skill_walk_slices.py::test_render_phase_t1_cue`: `render_phase`
  returns a ≤120-char imperative cue; a hard-gate phase's cue contains "?".
- `…::test_verb_bound_phase_inherits_verb_slice`: a phase with `invoke` renders
  via the bound verb's Spec-023 slice, not a hand-authored cue.

### 1.2 GREEN
- `agency/capability.py`: at registration, walk every capability's
  `ontology.skills`; for each phase with `invoke={capability,verb}`, add
  `skill:<skillname>` to that verb's tags. Reserve the `skill:` prefix.
- `agency/render.py`: `render_phase(phase, *, depth, registry=None)` — T1 cue /
  T2 instruction+produces+gate / T3 reference. Verb-bound → delegate to
  `render_verb` of the bound verb.

### 1.3 Gate: tests green; full suite green; commit + push.

---

## Phase 2 — `get_schema` dispatch (skill phase-map vs verb slice)

### 2.1 RED — `test_skill_first_discovery.py`:
- `get_schema("jules-dispatch")` → `{skill, phases:[{n,name,gate?,binds?}],
  next_to_walk}`; instructions NOT present (collapsed).
- `get_schema("capability_reflect_note")` → the verb's standard slice
  (unchanged from Spec 023).
- unknown name → the existing not-found behaviour.

### 2.2 GREEN
- Custom `GetSchemas`-style discovery tool (or wrap the engine's get_schema):
  name-prefix dispatch — registered skill name → `_render_phase_map(schema)`;
  `capability_*` → existing verb render.

### 2.3 Gate: green; commit + push.

---

## Phase 3 — skills-first `search` (the back-compat-sensitive change) ⚠️

### 3.1 RED — `test_skill_first_discovery.py`:
- `search("dispatch jules")` → first line is the `jules-dispatch` skill entry
  whose description ENDS with `→ walk: develop.skill_walk(name="jules-dispatch")`
  (panel F3 anti-footgun).
- the existing verb lines still follow, format unchanged (panel F1 additive).
- `search("reflect note")` (no matching skill) → verbs only, exactly as today.

### 3.2 GREEN
- Custom `Search(search_fn=…)`: run default BM25 over verbs; ALSO match the
  query against skill names/cues; PREPEND synthetic skill `Tool.from_function`
  entries (display-only). Wire via `CodeMode(discovery_tools=[custom_search,
  custom_get_schema])`.

### 3.3 Gate: green; full suite green (esp. `test_search_isomorphism`,
extended not rewritten); commit + push.

### 3.4 REVIEW CHECKPOINT — agency:code-review on the search/get_schema diff
(the load-bearing surface change; same care as Spec 023 Phase 3).

---

## Phase 4 — `skill_walk` / `skill_step` + engine heuristic

### 4.1 RED — `test_skill_walk_slices.py`:
- `develop.skill_walk(name, inputs)` on a SMALL skill (cached cost < 200) →
  `{status:"completed"|"input-required", phases:[all slices]}` (dumped).
- on a LARGE skill (cost > 200) → steps; returns first phase slice + a cursor.
- hard-gate pause → the Spec 016 Hint #8 resume contract; resume_from=skill_id
  resumes from graph-persisted state (fresh sandbox — research).
- `skill_step(skill_id)` advances one phase, returns only that slice.

### 4.2 GREEN
- `agency/skill.py`: `SkillRun` gains per-phase slice rendering (via
  `render_phase`). Cache each skill's collapsed-render token cost at
  registration (panel F2).
- `agency/capabilities/develop.py`: `skill_walk` / `skill_step` verbs over
  `SkillRun` + the dump-vs-step heuristic.

### 4.3 Gate: green; commit + push.

---

## Phase 5 — #8 resolution (chain_next coexistence)

### 5.1 RED:
- `test_engine_brief_descriptions.py` (updated): `search` shows brief (no
  chain hint); a verb's `deep` slice carries `chain_next` (panel F8); the skill
  phase-map carries the skill-context chain.
- a skill-less verb that documents `chain_next:` → reachable via `get_schema`
  deep / render_verb deep.

### 5.2 GREEN
- Reconcile `_wire` (engine.py): description = brief; full doc retained where
  `render_verb` can read it for deep. Remove the held #8 stopgap; this is the
  real resolution.

### 5.3 Gate: green; commit + push.

---

## Phase 6 — acceptance: token budget + isomorphism (loop exit)

### 6.1 RED — `tests/test_token_budget.py` (extended):
- discovery + first-phase walk of `jules-dispatch` ≤ 300 tiktoken tokens
  (vs ~520 Spec-018 boilerplate baseline).
- `test_search_isomorphism.py`: skill discovery + walk identical via MCP and
  `python -m agency.cli`.

### 6.2 GREEN: tune slices / threshold until the budget holds.

### 6.3 REVIEW CHECKPOINT (loop exit decision):
- budget met + isomorphic + #8 closed → DONE; flip Spec 025 `status: done`.
- missed after tuning → **re-enter Design** with `Plan/025-…/REVISION-1.md`.

---

## Test additions
```
tests/test_skill_first_discovery.py    # Phases 1-3
tests/test_skill_walk_slices.py        # Phases 1, 4
tests/test_engine_brief_descriptions.py (updated)  # Phase 5
tests/test_token_budget.py (extended)  # Phase 6
tests/test_search_isomorphism.py (extended)  # Phase 6
```

## Risk register
| Risk | Mitigation |
|---|---|
| search-shape change breaks agents/tests | Phase 3 additive (prepend only); isomorphism test extended; review checkpoint |
| synthetic skill entry → NotFoundError on naive call | F3 `→ walk:` cue in every skill entry description |
| heuristic measurement cost | F2 measure once at registration, cache on schema |
| chain hint lost for skill-less verbs | F8 chain_next coexists in verb-deep + phase-map |
| `SkillRun` exposure regresses existing internal walks | keep the internal API; verbs wrap it, don't replace |
