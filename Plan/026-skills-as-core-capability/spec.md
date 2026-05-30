---
spec_id: "026"
slug: skills-as-core-capability
status: draft
owner: "@agency"
depends_on: ["016", "023"]
parallel_to: ["025"]                 # exploring an alternative model in parallel
affects:
  - agency/capabilities/skills.py    # NEW — core capability, single-file (peer of reflect/develop/plugin)
  - agency/ontology.py               # Skill+Phase+Gate node types; APPLIES_WHEN/CHAINS_TO/MATCHED_BY edges
  - agency/skill.py                  # SkillRun gains `cue` rendering + intent-conditioned dispatch hooks
  - agency/render.py                 # skill-template surface (T1 cue / T2 contract / T3 reference)
  - agency/capability.py             # at registration, promote each Capability.ontology.skills entry to a Skill graph node
  - tests/test_skills_capability.py  # NEW
  - tests/test_skills_dispatch_modes.py  # NEW — one test per heuristic mode
estimated_jules_sessions: 0
domain: meta / dispatch
wave: 3
---

# Spec 026 — Skills as a core capability (intent-conditioned dispatch)

> **Parallel to Spec 025, not replacement.** Spec 025 puts skills on the
> *discovery* surface (search returns skills + verbs; get_schema returns the
> phase-map). Spec 026 puts skills on the *execution* surface (verbs return
> intent-conditioned next-skill snippets in their result envelope). We
> explore both before deciding; canonical Skill-as-concept ownership lands
> here regardless of which discovery layer ships.

## Why

The current model has skills as data — `Capability.ontology.skills` dicts
merged into one ontology. The runtime (`SkillRun`) walks them linearly,
phase by phase, by orchestrator-chosen schedule. Nothing in the system
*suggests* which skill applies to a given intent or attaches a skill
to a verb's return. Three concrete consequences:

1. **No intent-conditioned routing.** A user typing "develop a new
   capability" gets the same `develop.*` surface as "develop a new
   skill" — no automatic mapping intent → discipline. Today this is the
   orchestrator's job, done from prompt context.
2. **No verb-return chaining.** A successful `plugin.scaffold` doesn't
   tell the caller "now walk `skill-creation`"; the orchestrator must
   know. `chain_next:` markers are docstring prose only —
   `render.py:35-40,88-90` parses them, **no code consumes them**
   (survey #6).
3. **No Skill-as-concept owner.** Skill schemas, templates, and
   dispatch heuristics are scattered across `develop.py` (8 skills),
   `plugin.py` (2), `delegate.py` (1), `jules._jules_skills.py` (6),
   `examples/music.py` (1). Adding a new dispatch mode (intent-keyword,
   LLM-select) requires touching the skill *consumers*, not one
   capability.

The user's frame: **"Skills accompany every code-mode capability aspect
as prose for the ideal next step of that MCP function in dependency of
the current intent."** A `develop.*` verb called under one intent
("create a new skill") returns one snippet; the same verb under a
different intent ("create a new capability") returns a different one.
Skills *describe workflows and function chains for specific use
cases*, dispatched on intent.

This spec makes that concrete: a **single core capability,
`agency/capabilities/skills.py`** (peer of `reflect.py`, single file,
no subdirectory) owns Skill-as-concept — schema, templates, dispatch.

## Done When

- [ ] **`agency/capabilities/skills.py` lands** as a single-file core
  capability (~200 LOC + tests). Class-based `SkillsCapability`
  (`CapabilityBase`) per the established pattern (survey §4).
  Owns:
  - Skill+Phase+Gate node types in `OntologyExtension.nodes` —
    promoted from dicts to first-class graph entities at registration.
  - `APPLIES_WHEN`, `CHAINS_TO`, `MATCHED_BY` edges.
  - Skill+Phase schemas (the per-phase shape contract).
  - Rendering templates (T1 cue / T2 contract / T3 reference).
  - The dispatch verbs (below).

- [ ] **Skill schema gains an `applies_when` field.** Optional.
  Three shapes the dispatcher recognizes:
  - **Pattern**: `{"type": "pattern", "intent_re": "...", "purpose_kw": [...]}`
  - **Verb-code**: `{"type": "verb_code", "decider": {"capability", "verb"}}` — calls that verb at dispatch time, expects `{matches: bool, confidence: float}`
  - **LLM-select**: `{"type": "llm_select", "prompt": "..."}` — `ctx.sample()` picks among siblings

  Skills WITHOUT `applies_when` are not dispatched automatically — only
  reachable by name (status quo). This preserves all 17 existing skills
  unchanged.

- [ ] **Verbs on the new capability:**
  - `skills.find(intent_id, *, kind=None, capability=None) -> {candidates: [(skill, score)], …}`
    — discovery; returns skills whose `applies_when` matches the intent.
  - `skills.dispatch(intent_id, *, called_verb=None, called_capability=None) -> {skill, mode, confidence, ...}`
    — the central heuristic dispatch: walks `applies_when` modes in priority
    order (verb-code > pattern > llm-select); first match wins.
  - `skills.render(skill_name, *, depth='brief', intent_id=None) -> str`
    — render a skill (or one of its phases) at T1/T2/T3 depth. Uses
    Spec 023 slice machinery applied to phases (Spec 025 Phase-1
    foundation already shipped at `commit 660d7f5` is reusable here).
  - `skills.attach(call_result, dispatched_skill, depth='brief') -> dict`
    — decorate a verb's return envelope with `{next_skill: {…},
    next_cue: "…"}`. The orchestrator sees it and can chain.

- [ ] **Three reference examples — one per dispatch mode**
  (per user directive "find a good example for all three"):
  1. **Pattern**: a `reflect-recall` skill with
     `applies_when={type:"pattern", purpose_kw:["recall","remember","prior"]}` —
     when intent.purpose contains those keywords, `skills.dispatch`
     suggests walking `reflect-recall`.
  2. **Verb-code**: `develop.tdd` with
     `applies_when={type:"verb_code", decider:{capability:"develop", verb:"tdd_applies"}}`
     where `tdd_applies` is a new transform verb returning
     `{matches: bool}` based on whether the intent.acceptance text
     mentions tests/RED/GREEN/refactor.
  3. **LLM-select**: a `delegate.choose_subskill` flow where
     `applies_when={type:"llm_select", prompt:"Pick the discipline best matched to intent…"}`
     calls `ctx.sample()` over a candidate set.

- [ ] **Backward compatibility — strict, additive:**
  - All 17 existing skills work unchanged (`applies_when` absent →
    not dispatched, still walkable by name via `SkillRun`).
  - `OntologyExtension.skills` merge semantics unchanged (unique-name,
    collision raises — `ontology.py:114-117`).
  - `_wire_skill_tags` (`capability.py:151-174`) continues to mark
    bound verbs `skill:<name>` — Spec 025 Phase-1's foundation.

- [ ] **Tests:**
  - `tests/test_skills_capability.py` — capability registers cleanly;
    Skill nodes promoted to graph; `find`/`render` return shapes
    correct; backward-compat (existing 17 skills walkable unchanged).
  - `tests/test_skills_dispatch_modes.py` — one test per mode.
    Pattern: intent purpose matches keyword → dispatched. Verb-code:
    decider returns `matches=True` → dispatched. LLM-select: with a
    stubbed `ctx.sample`, picks the named winner. Negative cases
    (no match → empty candidates, no auto-dispatch).
  - Full suite stays green (currently 282).

## Architecture sketch

```
agency/capabilities/skills.py (NEW, ~200 LOC)
├── SkillsCapability(CapabilityBase)
│   ├── name = "skills"
│   ├── home = "lifecycle"          # skills are Lifecycle templates
│   ├── ontology = OntologyExtension(
│   │       nodes = {"Skill": [...], "Phase": [...], "Gate": [...]},
│   │       edges = {"APPLIES_WHEN", "CHAINS_TO", "MATCHED_BY"},
│   │       enums = {("Skill", "kind"): {"discipline", "authoring", "workflow"}},
│   │       templates = {"phase-cue-t1": "...", "phase-contract-t2": "...", ...},
│   │       schemas = {"Skill": [...], "Phase": [...]},
│   │   )
│   ├── @verb(role="transform")  find(self, intent_id, *, kind=None, capability=None)
│   ├── @verb(role="transform")  dispatch(self, intent_id, *, called_verb=None, called_capability=None)
│   ├── @verb(role="transform")  render(self, skill_name, *, depth="brief", intent_id=None)
│   └── @verb(role="act")        attach(self, call_result, dispatched_skill, depth="brief")
│
└── internal:
    ├── _match_pattern(applies_when, intent) -> (matches, score)
    ├── _match_verb_code(applies_when, intent, ctx) -> (matches, score)  # calls the decider verb
    └── _match_llm_select(applies_when, intent, candidates, ctx) -> (winner, score)  # ctx.sample
```

## Three forks the spec-panel will pressure-test

1. **Skill as graph node vs in-memory only.** Today skills are dicts in
   `OntologyExtension`. Promoting them to graph nodes at registration
   (default in this draft) gives provenance + cross-capability query but
   adds write overhead. Alternative: in-memory only; only Invocations
   and Reflections hit the graph.
2. **Where does `applies_when` live?** Above I put it on the skill dict
   (in-capability). Alternative: separate registry attached to the
   `skills` capability (skill-author opts in by registering with the
   skills capability rather than declaring on their own ontology).
3. **Attach vs return-shape change.** `skills.attach(result, ...)` is
   non-invasive — orchestrator opts in. Alternative: every verb's
   return AUTO-gets `next_skill` populated by the engine. Heavier,
   couples verb returns to skills.

## Open Questions

1. **Spec 025 ↔ Spec 026 convergence.** Both touch the same machinery
   (tags + render_phase) at the foundation layer. The Phase-1 work
   already shipped (`660d7f5` + `19058fe`) is reusable by both. The
   decision deferred: do we merge them into one Spec 027 once the
   discovery vs execution surface picture is clear, or ship Spec 026
   as the canonical Skill-as-concept owner and keep Spec 025 narrower
   to discovery wiring?

2. **Heuristic priority.** Above I sketched verb-code > pattern >
   llm-select. Alternative orderings: pattern first (cheapest), or
   "first applies_when defined wins" (no precedence). The cheapest
   wins on cost; the user's directive of "depending on flexibility
   needed" suggests caller-overridable priority.

3. **Cache on dispatch.** Should `skills.dispatch` cache the
   intent→skill match? An intent rarely changes mid-walk, and a
   verb-code or LLM-select dispatch has real cost. A weak per-intent
   cache (TTL/invalidate on intent.supersede) is probably right; the
   spec-panel should pressure-test it.

4. **Does this subsume `chain_next:` in docstrings?** Today it's
   prose only. If `skills.dispatch` provides the actual "what next"
   answer, do we deprecate the marker? Or keep it as static text +
   add the skill-level dispatch as the dynamic answer.

## Evidence (cites)

- Survey (this iteration) — file:line citations for every claim about
  current state. Recorded as `reflection:3ff930a3` SERVES intent:c374ac3d.
- `agency/ontology.py:60-126` — `OntologyExtension` shape + merge rules.
- `agency/capabilities/develop.py:21-99` — `_phase` helper + 8 skills.
- `agency/skill.py:24-108` — `SkillRun` runtime (already provides
  progressive disclosure via `current()`).
- `agency/capability.py:151-174` — `_wire_skill_tags` cross-capability
  binding (the discovery-layer foundation Spec 025 Phase-1 extends).
- `agency/capabilities/reflect.py:17-32` — minimal capability scaffold
  (the shape this spec follows).
- `agency/capabilities/delegate.py:32-100` — `dispatch-decision` skill
  + verb pair (the closest behavioural precedent to verb-code
  dispatch — already shows the "decider verb returns a recommendation"
  pattern).
- `agency/render.py:251-273` — `render_phase` (Spec 025 Phase-1 work
  reused for skill-level rendering).
- `reflection:f9b1d8bd` — the Spec 025 design rationale (skill-first
  discovery model).
- `reflection:3ff930a3` — the Plan/026 anchor decision (this spec).

## Loop position

- ✅ **Design** (this draft, anchored by `reflection:3ff930a3`)
- ⏭ **spec-panel** — pressure-test the three forks + four open questions
- ⏭ **Workflow** — IMPLEMENTATION-PLAN.md once panel finishes
- ⏭ **Implement** — TDD per phase
- ⏭ **Review** — Codex + agency:code-review
- ⏭ **Improve** — re-enter Design with findings, or close

Goal contributed to `intent:c374ac3d`: **a single source of truth for
Skill-as-concept that lets development guide itself by suggesting the
right next-skill from the intent's text + the verb's context** — the
literal mechanism behind "Development guiding itself."
