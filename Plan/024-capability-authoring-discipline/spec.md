---
spec_id: "024"
slug: authoring-capabilities-discipline
status: draft
version: 2                              # v2 — folds shipped foundations + Matcher-mode scope expansion
owner: "@agency"
depends_on: ["016", "020", "023", "025"]   # 025 Phase-1 (tags + render_phase) is the foundation v2 uses
unblocks: ["026"]                          # Matcher-mode scaffolds are the prerequisite for 026 implementation
affects:
  - agency/capabilities/develop.py                  # NEW discipline + 3 verbs (scaffold/lint/reference) + 3 matcher-mode helpers
  - agency/capabilities/plugin.py                   # lint_capability lives here (Spec 016 P4) — develop wraps it
  - skills/authoring-capabilities/SKILL.md          # NEW — model-invoked discipline guide (≤200 words; references CAPABILITY-AUTHORING.md)
  - docs/vision/CAPABILITY-AUTHORING.md             # ALREADY SHIPPED at f5f7575 — develop.reference returns slices of THIS
  - tests/test_develop_authoring.py                 # NEW — RED-GREEN-REFACTOR coverage of scaffold + lint
  - tests/test_authoring_pressure_scenarios.py      # NEW — TDD-for-docs subagent pressure tests
  - tests/test_develop_matcher_modes.py             # NEW — three Matcher-mode scaffolds (unblocks 026)
estimated_jules_sessions: 0
domain: meta / self-improvement
wave: 3
---

# Spec 024 v2 — Authoring-capabilities discipline (self-guiding development)

> **What changed in v2 from v1 (`29a9cfc`):**
> 1. **Foundations are no longer "proposed" — they're shipped.** Render-slice
>    contract (Spec 023), verb→skill tags + `render_phase` (Spec 025 Phase 1,
>    `19058fe`), the unified doctrine page (`docs/vision/CAPABILITY-AUTHORING.md`
>    at `f5f7575`). v2 *consumes* them — doesn't propose them.
> 2. **Scope expanded to unblock Spec 026.** v1 shipped scaffold + lint + a
>    discipline. v2 adds **three Matcher-mode scaffolds** (pattern / verb-code /
>    llm-select) so the matchers Spec 026 needs to test against are
>    *real, scaffolded capabilities*, not stubs.
> 3. **`references/` subdir dropped.** v1 split the synthesis across 5 sub-pages;
>    v2 points at the single unified `CAPABILITY-AUTHORING.md` (the user's
>    explicit directive: "Single unified page, all four sources synthesized").
> 4. **Lessons from Spec 023+025 R1-R4 + F1-F2 folded.** The pressure-test
>    contracts must verify the *consumer*, not the *wiring* — a test that
>    only asserts on registry state misses the FastMCP propagation bug
>    Codex R2 caught. v2 pressure tests round-trip through `mcp._list_tools()`
>    and through `search` output.

## Why

A new capability author today is left to read `Plan/016-…/spec.md`,
`Plan/023-…/spec.md`, four external skills, and the precedent in
`reflect.py` / `plugin.py` / `jules.py`. The unified
`CAPABILITY-AUTHORING.md` (shipped `f5f7575`) collapses that to one
page — but **nothing in the engine enforces** that authors actually
read it before shipping. Empirically, the four Codex P2 findings on
Spec 023 + the two more after R4 (eight findings in PR #12 total) ALL
trace to authoring drift: tests verified wiring not consumer; bash
snippets bundled env-var assumptions; placeholders looked valid but
were semantically wrong. Lint + scaffold close the loop.

This spec turns `CAPABILITY-AUTHORING.md` from doctrine into an
**enforced discipline**: every new capability goes through scaffold +
lint + a hard-gated discipline walk, and `develop.reference("authoring")`
returns slices of `CAPABILITY-AUTHORING.md` at T1/T2/T3 (Spec 023
progressive disclosure applied to the doctrine page itself).

**Bonus payload (unblocks Spec 026):** v2 also scaffolds the three
Matcher modes Spec 026's `intent.suggests_skill` needs to dispatch
against — pattern (keyword), verb-code (decider), llm-select
(`ctx.sample`). The scaffolds are *real capabilities*, lint-clean by
construction; Spec 026 then implements the dispatcher against
real test fixtures instead of inventing skills.

## Done When

### A. The discipline + the three develop verbs

- [ ] **`authoring-capabilities` discipline** lands in
  `agency/capabilities/develop.py`'s `DEV_SKILLS` — 6 phases, hard gate:
  1. **research** — author reads `docs/vision/CAPABILITY-AUTHORING.md`
     (T1/T2/T3 slices via `develop.reference("authoring")`).
  2. **scaffold** — invoke `develop.scaffold_capability(name, kind)`
     (bound — the discipline RUNS the verb, not documents it).
  3. **author** — write verbs with Hint #7 docstrings + role tags.
  4. **lint** — invoke `develop.lint_capability(name)` — must pass.
  5. **token-check** — `parse_slices(verb.doc)["brief"]` non-empty + ≤120 chars; simulated `search` on the new capability ≤20 tokens/verb.
  6. **commit** — hard gate: tests green, lint green, `reflection:`
     recorded SERVES the calling intent. Phase 2 and 4 are **bound**
     (carry `invoke={capability, verb}`) — discipline executes, not
     documents.

- [ ] **`develop.scaffold_capability(name, kind)`** verb (role: `act`).
  Kinds:
  - `light` (single-file, ≤3 verbs) — emits `agency/capabilities/<name>.py`
    with the class-form skeleton from `CAPABILITY-AUTHORING.md` §"Capability skeleton".
  - `medium` (single-file, 4+ verbs OR ships templates/schemas) —
    same + ontology stubs.
  - `heavy` (folder form, Spec 016 Hint #1) — emits
    `agency/capabilities/<name>/{__init__.py, <name>.py}` with the
    re-export pattern.
  Returns `{result: path, artefact: {kind: "capability-scaffold", name, path, kind}}`.
  **Acceptance**: scaffolded skeleton lints clean immediately (no
  manual edits required to pass `develop.lint_capability`).

- [ ] **`develop.lint_capability(name)`** verb (role: `transform`).
  Wraps `plugin.lint_capability` (Spec 016 P4) and adds the v2 checks:
  - **structural** — every `@verb` has `Inputs:` / `Returns:` /
    `chain_next:` markers; role tag matches docstring shape (`effect`
    verbs name an external system; `transform` verbs have no I/O
    imports — `requests`, `httpx`, `subprocess` in body → flag).
  - **render-slice** — `parse_slices(verb.doc)["brief"]` non-empty +
    ≤120 chars; first sentence cleaves on `_first_sentence`; the
    delta after the brief cleanly survives `parse_slices` (the EOF +
    legacy-body bugs Codex caught).
  - **consumer-contract** (new in v2, from the R1-R4 + F1-F2 lessons):
    a simulated `Engine(":memory:", extra_capabilities=[scaffolded_cap])`
    actually builds; `mcp._list_tools()` returns the new tools with
    correct tags; a `search` for the capability's domain finds them
    under budget. **The lint exercises the consumer surface, not just
    the wiring** — every R-finding in PR #12 came from skipping this.
  - **token-budget** — simulated `search` containing only this
    capability's verbs returns ≤ 20 × verb_count tiktoken cl100k tokens.
  Returns `{ok, violations: [{verb?, phase?, kind, msg, fix}], skipped: N}`
  (mirrors `plugin.lint_skill`).

- [ ] **`develop.reference(topic)`** verb (role: `transform`) — extends
  the existing `develop.reference`. New topic: `"authoring"`. Returns
  slices of `docs/vision/CAPABILITY-AUTHORING.md` at T1/T2/T3 depth
  using `render_phase` machinery — Spec 023 progressive disclosure
  applied to a long doc. Caller passes `depth='brief'|'standard'|'deep'`.

### B. The model-invoked SKILL.md

- [ ] **`skills/authoring-capabilities/SKILL.md`** — ≤200 words total
  (anthropic-best-practices token-efficiency rule). Description is
  pure WHEN, not WHAT (CSO rule from writing-skills). Body is the
  index that points at `docs/vision/CAPABILITY-AUTHORING.md` for
  substance.

  Frontmatter:
  ```yaml
  ---
  name: authoring-capabilities
  description: Use when authoring a new agency capability or extending
    an existing one — before writing the file. The discipline runs
    scaffold then lint behind a hard gate; lint must pass before
    commit.
  allowed-tools:
    - mcp__plugin_agency_agency__search
    - mcp__plugin_agency_agency__get_schema
    - mcp__plugin_agency_agency__execute
    - Read
    - Write
    - Edit
    - Bash
  ---
  ```

  Body (≤200 words): three steps (research → scaffold → lint), each
  one line, plus a pointer to `docs/vision/CAPABILITY-AUTHORING.md`
  for the why/how. **Drop `references/` subdir** (user directive:
  single unified page).

### C. Three Matcher-mode scaffolds (unblocks Spec 026)

Each scaffold is a **real capability**, lint-clean by construction, that
Spec 026's `intent.suggests_skill` then matches against. Concrete files:

- [ ] **Pattern mode**: a scaffolded `examples/notebook.py` capability
  with a skill whose `applies_when={kind:"pattern", purpose_kw:["note","journal"]}`.
  The scaffold demonstrates the **simplest** matcher — string
  intersection with intent.purpose.

- [ ] **Verb-code mode**: a scaffolded `examples/code_advisor.py`
  capability with a `tdd_applies(intent_id) -> {matches, confidence}`
  decider verb + a skill carrying
  `applies_when={kind:"verb_code", verb_code:{capability:"code_advisor", verb:"tdd_applies"}}`.
  The decider reads intent.acceptance text and detects TDD keywords;
  returns a normalized confidence score. Demonstrates the **dispatch
  carries verb-execution cost**.

- [ ] **LLM-select mode**: a scaffolded `examples/research_routes.py`
  capability with sibling skills (`research-quick`, `research-deep`,
  `research-empirical`) sharing
  `applies_when={kind:"llm_select", llm_select:{prompt:"Pick the research style…", candidates:[...]}}`.
  Demonstrates `ctx.sample` selection AND failure semantics (gibberish
  return → demote to next mode).

- [ ] **`tests/test_develop_matcher_modes.py`** asserts each scaffold:
  - lints clean (no edits required);
  - the `applies_when` field validates against the Matcher JSON Schema
    Spec 026 ships in `OntologyExtension.schemas`;
  - a unit test of the matcher payload (pattern matches expected keywords;
    decider verb returns the right shape; llm-select prompt is well-formed).

### D. The TDD-for-docs validation (load-bearing for THIS spec)

- [ ] **`tests/test_authoring_pressure_scenarios.py`** —
  RED-GREEN-REFACTOR per writing-skills doctrine:
  - **RED**: dispatch a subagent to "Add a `notebook` capability with
    verbs `save(content, path)` and `list(directory)`" WITHOUT the
    discipline. Capture the result. Run `develop.lint_capability` —
    assert violations exist (this is the documented baseline failure
    mode; the *rationalization table* in `CAPABILITY-AUTHORING.md` was
    seeded from running this scenario).
  - **GREEN**: dispatch same task pointing at the
    `authoring-capabilities` discipline. Run `develop.lint_capability` —
    assert `{ok: True}`.
  - **REFACTOR slot**: every new rationalization the RED agent
    invokes ("the docstring is self-evident", "I'll add markers later",
    "this verb is too simple for the contract") becomes a row in the
    rationalization table. The Rev-2 spec INCLUDES the seven rows
    `CAPABILITY-AUTHORING.md` already documents; the test asserts the
    table grows monotonically (entries don't disappear silently).
  - Marked `@pytest.mark.slow`; skipped in CI unless
    `AGENCY_RUN_PRESSURE_TESTS=1` (the v1 question — defaulted yes).

- [ ] **Self-improvement loop wired** — every successful walk of
  `authoring-capabilities` records a Reflection SERVES
  `intent:c374ac3d`. Spec 014 (when shipped) projects these into
  doctrine amendments.

- [ ] **Backward compatibility** — all 17 existing capabilities still
  load + walk; their skills still walkable via SkillRun unchanged.
  Asserted by full suite green throughout (currently 282).

## Files (final list)

- **Create:**
  - `skills/authoring-capabilities/SKILL.md` (~120 lines)
  - `tests/test_develop_authoring.py`
  - `tests/test_develop_matcher_modes.py`
  - `tests/test_authoring_pressure_scenarios.py`
  - `examples/notebook.py` (pattern-mode reference scaffold)
  - `examples/code_advisor.py` (verb-code mode reference scaffold)
  - `examples/research_routes.py` (llm-select mode reference scaffold)
- **Modify:**
  - `agency/capabilities/develop.py` — discipline + 3 verbs
  - `agency/capabilities/plugin.py` — `lint_capability` (Spec 016 P4) lands here; `develop.lint_capability` wraps + extends
- **Already shipped** (this spec consumes):
  - `docs/vision/CAPABILITY-AUTHORING.md` (`f5f7575`)
  - `agency/render.py:parse_slices, render_verb, render_phase` (Spec 023 + Spec 025 P1)
  - `agency/engine.py` verb tag propagation (`19058fe`)
  - `agency/capability.py:_wire_skill_tags` (`660d7f5`)

## Open Questions

1. **Reference verb topic disambiguation.** `develop.reference("authoring")`
   returns the new doc; `develop.reference("testing-skills")` etc. already
   exist (T3 progressive disclosure precedent). Should "authoring" be
   the canonical topic name, or "capabilities" / "capability-authoring"?
   Recommend "authoring" — gerund form per anthropic-best-practices.

2. **Lint mode**: warn-only vs hard-block. Spec 016 v1's Open Q #1 said
   warn during migration → block after. v2 says: **block immediately**
   for newly-scaffolded capabilities (the scaffold lints clean by
   construction; first-time violation means someone modified it
   wrongly); **warn-only** for existing 17 (migration path).

3. **Pressure-test stability**. Subagent dispatch is non-deterministic;
   the RED test asserts "violations exist" not "violations match X".
   Is that strong enough? Recommend: assert the *kind* of violation
   matches a documented baseline (e.g. at least one
   `kind:"render_slice"` and one `kind:"role_tag"`), not just count.

4. **The three example scaffolds — light/medium/heavy distribution.**
   v2 puts all three under `examples/` (out of core, per the existing
   pattern). The scaffolds are *also* the test fixtures for matcher
   modes. Should one be promoted to a real core capability if it
   proves load-bearing in Spec 026 (e.g. `code_advisor` matches the
   "decider" pattern `delegate.dispatch_decision` already does)?
   Recommend: keep in `examples/` for v2; promote in a Spec 028 if
   real usage warrants.

## Evidence (cites)

- `docs/vision/CAPABILITY-AUTHORING.md` (f5f7575) — the unified
  doctrine page; develop.reference returns slices of it.
- `Plan/016-…/spec.md` — 11 hints; Phase 4 (lint_capability) folded.
- `Plan/023-…/spec.md` + `agency/render.py:parse_slices` — render-slice
  contract.
- `Plan/025-skill-first-discovery/spec.md` + `agency/render.py:render_phase`
  + `agency/capability.py:_wire_skill_tags` — Phase 1 foundations
  this spec consumes (commits `660d7f5`, `19058fe`).
- `Plan/026-skills-as-core-capability/spec.md` v2 — defines the Matcher
  schema this spec's scaffolds populate.
- `tests/test_render.py` + `tests/test_skill_walk_slices.py` +
  `tests/test_skill_first_discovery.py` — the consumer-contract test
  pattern this spec extends to capability-authoring.
- PR #12 Codex review history (8 P2 findings, all fixed) — the empirical
  evidence that lint without consumer-contract checks is insufficient.
- `reflection:c374ac3d-anchor` — durable goal "make Development guiding itself."

## Loop position

- ✅ v1 drafted (`29a9cfc`, predated 023/025 shipping)
- ✅ Foundations shipped (PR #12 carries them)
- ✅ Unified doctrine page shipped (`f5f7575`)
- ✅ **v2 drafted** (this revision)
- ⏭ spec-panel — pressure test v2
- ⏭ refine
- ⏭ Workflow — IMPLEMENTATION-PLAN.md
- ⏭ Implement — TDD per phase

Goal: every future capability (including the `skills` capability
from Spec 026) is authored under this discipline → lint-clean by
construction → no more Codex P2 round-trip cycle. Empirically
falsifiable: count Codex P2 findings on the next capability merged
under this discipline. Target: 0.
