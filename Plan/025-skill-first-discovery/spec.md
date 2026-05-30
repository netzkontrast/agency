---
spec_id: "025"
slug: skill-first-discovery
status: draft
owner: "@agency"
depends_on: ["016", "018", "023"]
affects:
  - agency/engine.py                     # tag verbs with skills; custom Search ranks skills-first; skill-schema discovery tool
  - agency/skill.py                      # SkillRun → exposed; per-phase slice rendering
  - agency/capabilities/develop.py       # skill.walk / skill.step verbs (the adaptive walker surface)
  - agency/render.py                     # render_phase (Spec 023 slices applied to phases)
  - agency/capability.py                 # verb→skill tag wiring at registration
  - tests/test_skill_first_discovery.py  # NEW
  - tests/test_skill_walk_slices.py      # NEW
estimated_jules_sessions: 0
domain: engine / discovery
wave: 3
---

# Spec 025 — Skill-first discovery + adaptive phase disclosure

## Why

The canonical code-mode flow is `search → get_schema → execute` with
progressive disclosure (Anthropic *Code execution with MCP*: 150k→2k tokens,
98.7%; FastMCP code-mode: ~34k upfront → ~600/workflow). Anthropic's **Agent
Skills** formalize the same idea as **three-stage disclosure** — discovery
(name+description) → activation (read the steps) → execution (load each step as
needed). **Agency has the substrate for all three but wires only the first
crudely:** `search` returns a flat verb dump; there is no skill-level
discovery, no phase-map activation, no per-step execution disclosure.

Spec 023 (shipped) sliced *verb docstrings* (brief/standard/deep). PR-review
finding #8 exposed the tension: truncating a verb's description to `brief`
for `search` also strips the `Returns`/`chain_next` prose from `get_schema`.
**This spec resolves #8 by reframing rather than patching:** discovery is
*skill-first*, and the chain hint belongs in the **skill phase-map**, not
crammed into a verb description.

Research findings that ground the design (subagent reports, this session):
- **Code-mode has no skill or next-step primitive** (`GetToolNext` is a
  middleware continuation, not an LLM-facing hint). We build adaptive
  disclosure ourselves — on `SkillRun`, which already exists.
- **Tags are native.** Verbs carry `tags: set[str]`; `Search(tags=[…])` and the
  `tags` tool group by tag. Skill-first discovery = tag each verb with its
  discipline; no fork of code-mode.
- **The sandbox is fresh per `execute` call.** Cross-step state lives in the
  graph (`SkillRun` already persists `skill_id` + `Gate` nodes) — so
  `skill.walk` runs to first hard gate in one block, resumes via `skill_id`
  later. This is *why* Spec 018 Win 1's resume-by-id design is correct.
- **`search` can return synthetic entries** (fabricated `Tool.from_function`
  with a phase-map description + tags), but they are display-only — `execute`'s
  `call_tool` resolves names against the real catalog. So skill entries are a
  *discovery/schema* surface; the *walk* goes through real verbs.

## The model (three stages)

```
search("dispatch jules")     →  SKILLS first (tag-grouped) + brief verbs   [DISCOVERY]
get_schema("jules-dispatch") →  collapsed phase-map: ordered steps + gates, [ACTIVATION]
                                each step's instruction COLLAPSED (expand on walk)
skill.walk / skill.step      →  one phase's slice at a time; engine-        [EXECUTION]
                                heuristic: dump whole skill if < threshold,
                                else step phase-by-phase
```

`search`/`get_schema`/`execute` stay the only three wire tools (canon
unchanged). Skills surface *through* them; the walk is a capability verb
reachable inside `execute`.

## Done When

- [ ] **Verbs are tagged with their skill(s).** At registration
  (`agency/capability.py`), each verb a skill phase BINDS to (the `invoke`
  field in `ontology.skills`) gets a `skill:<name>` tag. `search(tags=
  ["skill:jules-dispatch"])` returns that skill's verbs. Pure metadata; zero
  behaviour change.
- [ ] **Skills rank first in `search`.** A custom `Search` (via
  `CodeMode(discovery_tools=[…])`) surfaces a synthetic skill entry per
  discipline (name + one-line cue + `tags`) ABOVE the matching verbs, when the
  query matches a skill. Verbs still appear (skill-first ≠ skill-only —
  research: a leaf verb like `reflect.note` must stay directly findable).
  - **Back-compat (panel F1):** the change is ADDITIVE — skill entries are
    PREPENDED; the existing verb-line format (`- name: desc`) is unchanged, so
    agents/tests parsing verb lines still work. `test_search_isomorphism` is
    extended (not rewritten); an output-contract note lands in Spec 019's doc.
  - **Anti-footgun (panel F3):** each skill entry's description ENDS with
    `→ walk: develop.skill_walk(name="<skill>")` so an agent that sees the
    skill calls the walker, not `call_tool("<skill>")` (which would raise
    NotFoundError — skill entries are display-only synthetic tools).
- [ ] **`get_schema(skill)` returns the collapsed phase-map** (panel-locked
  choice): `{skill, phases: [{n, name, gate?, binds?}], next_to_walk}`. Phase
  *instructions* are NOT included here — collapsed; the walk discloses them.
  Reuses the existing `ontology.skills[name]` schema.
- [ ] **`develop.skill_walk(name, inputs)` + `develop.skill_step(...)` verbs**
  (Spec 018 Win 1, here gaining slice rendering). `skill_walk` runs to first
  hard gate in one block; returns `{status, phase, slice, produced}` or the
  `input-required` resume contract (Spec 016 Hint #8). `skill_step` advances
  one phase, returning only that phase's render slice.
- [ ] **Per-phase render slices** (`agency/render.py:render_phase`): a phase's
  T1 cue (≤120 char imperative; hard-gate phases state the gate question),
  T2 instruction (produces-keys + gate), T3 reference (heavy how-to via
  `develop.reference`, on demand). A verb-bound phase INHERITS the bound verb's
  Spec-023 slice — no duplicate authored.
- [ ] **Engine heuristic for dump-vs-step.** Each skill's full collapsed-render
  token cost is **measured ONCE at registration** and cached on the skill
  schema (panel F2 — not recomputed per walk). `skill_walk` reads the cached
  cost; if < `AGENCY_SKILL_DUMP_TOKENS` (default 200, tiktoken) it returns all
  phases at once; else it steps. The "only where token-efficient" rule,
  automatic (research: <~20 items / small total → show all; else stage).
- [ ] **#8 resolved.** Verb descriptions stay the brief (search token win
  holds); `get_schema` of a *verb* returns its Spec-023 standard slice
  (Inputs/Returns via params). `chain_next` lives in BOTH the skill phase-map
  AND (panel F8) the verb's `deep` slice — because some verbs chain
  meaningfully with no skill wrapper (`jules.dispatch → jules.status`). The
  two coexist: the phase-map is the skill-context hint; the deep verb slice is
  the skill-less hint. `tests/test_engine_brief_descriptions.py` updated to
  assert the split (search=brief; chain hint reachable via skill phase-map OR
  verb-deep, never via the brief that `search` shows).

- [ ] **`get_schema` dispatches on target kind (panel F7, was Open Q4):** a
  registered skill name → the collapsed phase-map; a `capability_*` name → the
  verb's Spec-023 slice. Documented contract, asserted in tests.

- [ ] **Reserve the `skill:` tag namespace (panel F6):** the ontology declares
  `skill:` a reserved tag prefix; `lint_capability` rejects a hand-authored
  literal `skill:` tag (only the registration path mints them).
- [ ] **Isomorphic over MCP + CLI** (the loop's exit condition): the skill
  discovery + walk works identically via `mcp__plugin_agency_agency__*` and
  `python -m agency.cli`. Asserted by extending `test_search_isomorphism.py`.
- [ ] `python -m pytest -q` stays green throughout.

## Files

- **Modify:** `agency/engine.py` (custom Search + skill-schema discovery tool +
  verb tagging), `agency/capability.py` (registration-time skill tags),
  `agency/skill.py` (SkillRun slice rendering), `agency/render.py`
  (`render_phase`), `agency/capabilities/develop.py` (`skill_walk`/`skill_step`).
- **Create:** `tests/test_skill_first_discovery.py`,
  `tests/test_skill_walk_slices.py`, `Plan/025-…/IMPLEMENTATION-PLAN.md`.

## Behavioral examples (panel F5)

**Discovery** — *Given* the registry has a `jules-dispatch` skill, *When*
`search("dispatch a jules session")`, *Then* the first result is the skill
entry `jules-dispatch: dispatch+watch a remote Jules session → walk:
develop.skill_walk(name="jules-dispatch")`, followed by the matching verbs
(`capability_jules_dispatch: …`, `capability_delegate_dispatch_decision: …`).

**Activation** — *Given* `get_schema("jules-dispatch")`, *Then* it returns
`{skill: "jules-dispatch", phases: [{n:1, name:"detect-mode", binds:"jules.detect_mode"}, {n:2, name:"dispatch", binds:"jules.dispatch"}, {n:3, name:"approve-plan", gate:"hard", binds:"jules.approve_plan"}], next_to_walk: 1}` — phase NAMES + gates + bound verbs, instructions COLLAPSED.

**Stepped walk pausing at a gate** — *Given* a skill whose cached render cost
> 200 tokens, *When* `develop.skill_walk(name="jules-dispatch", inputs={…})`,
*Then* it executes phases 1-2, reaches the hard gate at phase 3, and returns
`{status:"input-required", phase:"approve-plan", slice:"Confirm: approve the
generated plan?", blocked_on:"<Gate id>", resume_with:["confirmed"],
skill_id:"<id>"}` — and a later `skill_walk(resume_from=skill_id,
inputs={confirmed:true})` resumes from the graph-persisted state.

## Open Questions

1. **Skill entry backing.** A synthetic skill entry in `search` is display-only
   (not callable). Do we ALSO register a real `capability_<x>_walk` per skill
   (so `call_tool` can invoke it), or is the single `develop.skill_walk(name)`
   enough (the agent passes the skill name as an arg)? **Default**: one
   `develop.skill_walk(name)` — no per-skill tool explosion.
2. **Tag namespace.** `skill:<name>` vs a dedicated tag field. **Default**:
   `skill:` prefix on the existing `tags` set — zero schema change.
3. **Dump threshold default.** 200 tiktoken tokens is a guess. **Default**: ship
   200, tune from a real walk's measured cost (record a Reflection).
4. **Does `get_schema` dispatch on target kind?** `get_schema("jules-dispatch")`
   (skill) vs `get_schema("capability_reflect_note")` (verb) need different
   renders. **Default**: name-prefix dispatch — a registered skill name → phase
   map; a `capability_*` name → verb slice.

## Evidence (cites)

- `docs/vision/CORE.md:40-52` — skills as Lifecycle templates walked step-by-step
  with per-step disclosure (the canon this implements).
- `docs/vision/GOALS.md:8-12` — token-efficient loops; "the full tool list never
  loads into context."
- Anthropic, *Code execution with MCP* — 150k→2k tokens; tools-as-filesystem.
- Anthropic, *Equipping agents… Agent Skills* — 3-stage progressive disclosure.
- FastMCP code-mode docs — `search → get_schema → execute`; detail levels;
  <20-tool threshold.
- `agency/skill.py:SkillRun` — the walker we expose (currently engine-internal).
- `Plan/018-…/spec.md` Win 1 — `skill.walk` (this spec adds slice rendering).
- `Plan/023-…/spec.md` — verb slices (become the leaf here).
- `reflection:ca2b6bfe` (skill-slice doctrine), `reflection:f9b1d8bd` (this
  design), `reflection:61e018f1` (realignment-surface gaps — a `memory.census`
  sibling verb).

## Goal (loop exit condition)

The loop restarts until: (1) discovering+walking a skill costs materially fewer
tokens than the current flat verb dump (target: a `jules-dispatch` discovery +
first-phase walk ≤ 300 tiktoken tokens vs the ~520 boilerplate baseline in Spec
018); (2) it works identically via MCP code-mode and the bash CLI; (3) #8 is
closed (search=brief, get_schema reveals what each tier needs). Miss any → back
to **Design (improve)** with a REVISION-N gap analysis.
