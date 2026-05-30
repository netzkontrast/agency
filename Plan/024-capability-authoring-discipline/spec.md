---
spec_id: "024"
slug: authoring-capabilities-discipline
status: draft
version: 3                              # v3 — folds spec-panel REVISE on v2 (5 changes + 1 tightening)
owner: "@agency"
depends_on: ["016", "020", "023", "025-P1", "026-P0"]   # 025-P1 shipped (19058fe); 026-P0 = Matcher schema + benchmark baseline
unblocks: ["026"]                          # PR-C of THIS spec (Matcher scaffolds) ships AFTER 026-P0 lands the schema
ship_as: ["PR-A (discipline+lint)", "PR-B (doc-slicing)", "PR-C (Matcher scaffolds, gated on 026-P0)", "PR-D (pressure tests, @pytest.mark.slow)"]
panel_revision: "a583d6004bdb3fc67"  # spec-panel verdict REVISE on v2
affects:
  - agency/capabilities/develop.py                  # NEW discipline + 2 verbs (scaffold_capability + doc) — NO lint wrapper
  - agency/capabilities/plugin.py                   # lint_capability lives here (Spec 016 P4) including the consumer-contract checks
  - skills/authoring-capabilities/SKILL.md          # NEW — model-invoked discipline guide (≤200 words; references CAPABILITY-AUTHORING.md)
  - docs/vision/CAPABILITY-AUTHORING.md             # ALREADY SHIPPED at f5f7575 — develop.doc("authoring") returns slices of THIS
  - tests/test_develop_authoring.py                 # PR-A — discipline + scaffold + lint
  - tests/test_develop_doc.py                       # PR-B — sliced long-doc rendering
  - tests/test_authoring_pressure_scenarios.py      # PR-D — TDD-for-docs subagent pressure tests (slow, marked)
  - tests/test_develop_matcher_modes.py             # PR-C — three Matcher-mode scaffolds (depends 026-P0)
estimated_jules_sessions: 0
domain: meta / self-improvement
wave: 3
---

# Spec 024 v3 — Authoring-capabilities discipline (self-guiding development)

> **What changed in v3 from v2 (panel `a583d6`, verdict REVISE):**
> 1. **`develop.lint_capability` wrapper dropped (panel F5a).** Consumer-contract
>    checks (`Engine(":memory:")` round-trip, `mcp._list_tools()` tag
>    propagation) live directly on `plugin.lint_capability` — its natural home
>    next to `plugin.lint_skill`. The discipline's lint phase binds to
>    `plugin.lint_capability`, not a develop wrapper. Removes the layering
>    inversion (`develop` would otherwise import `Engine` and become a
>    meta-engine).
> 2. **`develop.reference` no longer overloaded (panel F1a).** New verb
>    `develop.doc(topic, depth=)` for sliced long-form docs (`authoring`,
>    later `core`, `goals`). `develop.reference(topic)` stays for the existing
>    short prose blobs (`testing-skills` / `skill-descriptions` / `best-practices`)
>    — two contracts, two verbs.
> 3. **026-P0 dependency made explicit (panel F3a + F6b).** PR-C (Matcher
>    scaffolds) gates on Spec 026 phase 0 landing the Matcher JSON Schema +
>    `MATCHER_SCHEMA_VERSION` constant + the Jules-benchmark baseline. Without
>    that gate, the three example scaffolds become orphans referencing a
>    defunct schema.
> 4. **Scaffold marker for lint-mode dispatch (panel F4a).** Scaffold emits
>    `# agency-scaffold: v1` as the file's first comment; `plugin.lint_capability`
>    reads it: present → block on violations, absent → warn (legacy
>    grandfathering rule from F4b).
> 5. **Sliced shipping (panel F7a).** Four PRs explicit in frontmatter:
>    PR-A (discipline+lint), PR-B (doc-slicing), PR-C (Matcher scaffolds,
>    gated 026-P0), PR-D (pressure tests, `@pytest.mark.slow`). Natural
>    cleavage already existed; the spec makes it the merge plan.
> 6. **Pressure-test stability (panel F2a, optional).** N=5 runs + ≥2
>    distinct violation kinds across the set, not single-run kind-assertion.

> **What changed in v2 from v1** (kept for history; superseded by v3 above):
> consumed shipped foundations (Specs 023, 025-P1, the unified
> `CAPABILITY-AUTHORING.md`), added Matcher-mode scope for Spec 026, dropped
> the `references/` subdir, folded R1-R4 + F1-F2 consumer-contract lessons.

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

### A. The discipline + verbs (PR-A; no cross-spec deps)

- [ ] **`authoring-capabilities` discipline** lands in
  `agency/capabilities/develop.py`'s `DEV_SKILLS` — 6 phases, hard gate:
  1. **research** — author reads `docs/vision/CAPABILITY-AUTHORING.md`
     (T1/T2/T3 slices via `develop.doc("authoring", depth=)` — PR-B).
  2. **scaffold** — invoke `develop.scaffold_capability(name, kind)`
     (bound).
  3. **author** — write verbs with Hint #7 docstrings + role tags.
  4. **lint** — invoke `plugin.lint_capability(name)` — bound directly
     (no develop wrapper; panel F5a — `plugin.lint_skill` precedent).
  5. **token-check** — `parse_slices(verb.doc)["brief"]` non-empty + ≤120 chars; simulated `search` on the new capability ≤20 tokens/verb.
  6. **commit** — hard gate: tests green, lint green, `reflection:`
     recorded SERVES the calling intent. Phases 2 and 4 are **bound**
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

  **Every scaffolded file emits `# agency-scaffold: v1` as the first
  line** (panel F4a — the marker `plugin.lint_capability` reads to
  switch lint mode between block-on-violation (scaffolded) and
  warn-only (legacy)). The marker version bumps when the scaffolded
  contract evolves.

  Returns `{result: path, artefact: {kind: "capability-scaffold", name, path, kind, scaffold_version: 1}}`.

  **Acceptance**: scaffolded skeleton lints clean immediately (no
  manual edits required to pass `plugin.lint_capability`).

- [ ] **`plugin.lint_capability(name)`** verb on the `plugin`
  capability (role: `transform`). Owns all the checks; the discipline
  binds to it directly (panel F5a, no wrapper):
  - **structural** — every `@verb` has `Inputs:` / `Returns:` /
    `chain_next:` markers; role tag matches docstring shape (`effect`
    verbs name an external system; `transform` verbs have no I/O
    imports — `requests`, `httpx`, `subprocess` in body → flag).
  - **render-slice** — `parse_slices(verb.doc)["brief"]` non-empty +
    ≤120 chars; first sentence cleaves on `_first_sentence`; the
    delta after the brief cleanly survives `parse_slices` (the EOF +
    legacy-body bugs Codex caught in PR #12).
  - **consumer-contract** — a simulated
    `Engine(":memory:", extra_capabilities=[scaffolded_cap])` builds;
    `mcp._list_tools()` returns the new tools with correct tags; a
    `search` for the capability's domain finds them under budget.
    Lives on `plugin` (not `develop`) — `plugin` already imports
    `Engine` for `lint_skill`'s precedent, no layering inversion.
  - **token-budget** — simulated `search` containing only this
    capability's verbs returns ≤ 20 × verb_count tiktoken cl100k tokens.
  - **mode dispatch** (panel F4a + F4b): reads the scaffold marker:
    - Marker present + violations → `{ok: False, ...}` (block).
    - Marker absent + violations → `{ok: True, warnings: [...]}`
      (warn-only; grandfathered legacy).
    - Marker absent + clean → `{ok: True}`.
  Returns `{ok, violations: [{verb?, kind, msg, fix}],
                 warnings: [{...}], skipped: N, mode: "block"|"warn"}`.

### B. Doc-slicing (PR-B; independent of A and C)

- [ ] **`develop.doc(topic, *, depth='brief'|'standard'|'deep')`** —
  NEW verb (role: `transform`). Returns slices of long-form docs at
  T1/T2/T3 using the `render_phase` machinery. Panel F1a: keep
  `develop.reference(topic)` for the existing short prose blobs
  (`testing-skills`, `skill-descriptions`, `best-practices`); the new
  `develop.doc` handles sliced long docs (`authoring` is the first;
  later `core`, `goals`).

  - Input: `topic ∈ {"authoring"}` initially; extends to more long
    docs as they land.
  - Output (markdown):
    - `brief` — H1 title + the doc's first paragraph + a TOC of section
      titles (~250 tokens).
    - `standard` — full §"The four-line summary" + §"Decision tree" +
      §"Common docstring mistakes" + §"Role tags" (~900 tokens).
    - `deep` — entire document (~5000 tokens).
  - **Acceptance**: each depth's token count (tiktoken cl100k) is
    asserted in `tests/test_develop_doc.py` against a budget fixture.

### C. The model-invoked SKILL.md

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

### D. Three Matcher-mode scaffolds (PR-C; gated on 026-P0)

> **Cross-spec contract** (panel F3a + F6b): this section depends on
> Spec 026 phase 0 landing the Matcher JSON Schema in
> `OntologyExtension.schemas` + the `MATCHER_SCHEMA_VERSION` constant.
> Until 026-P0 is on `main`, PR-C does not ship. The three scaffolds
> import the constant; if it doesn't exist, the import fails loud at
> CI rather than silently drifting.

Each scaffold is a **fixture** — a real capability authored
clean-by-construction (panel F2b — NOT a TDD cycle on the scaffolder;
the property "scaffold output lints clean" is the assertion). Spec
026's `intent.suggests_skill` then matches against these fixtures.

Concrete files:

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

### E. The TDD-for-docs validation (PR-D; @pytest.mark.slow)

- [ ] **`tests/test_authoring_pressure_scenarios.py`** —
  RED-GREEN-REFACTOR per writing-skills doctrine. **Stability tightened
  per panel F2a**: each scenario runs N=5 times and asserts on the
  *set* of violations across runs, not single-run kind-matching.

  - **RED**: dispatch a subagent to "Add a `notebook` capability with
    verbs `save(content, path)` and `list(directory)`" WITHOUT the
    discipline. Repeat **5 times**. Run `plugin.lint_capability` on
    each result. Assertion: **≥2 distinct violation kinds** appear
    across the 5 runs (e.g. at least one `kind:"render_slice"` AND
    at least one `kind:"role_tag"` somewhere in the set). Single-run
    stochasticity tolerated; population behaviour pinned.
  - **GREEN**: dispatch same task pointing at the
    `authoring-capabilities` discipline. Repeat **5 times**.
    Assertion: **all 5 runs produce `{ok: True}`** (the discipline
    is supposed to be deterministic in outcome even if route differs).
  - **REFACTOR slot**: every new rationalization the RED agents
    invoke becomes a row in the rationalization table.
    `CAPABILITY-AUTHORING.md` already documents the seven seeded rows;
    the test asserts the table grows monotonically (entries don't
    disappear silently).
  - Marked `@pytest.mark.slow`; skipped in CI unless
    `AGENCY_RUN_PRESSURE_TESTS=1`.

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

## Open Questions (v3 — most v2 questions resolved by panel revisions)

1. **Doc-topic naming.** `develop.doc("authoring")` — confirmed
   gerund-form per anthropic-best-practices. Future topics: `core`,
   `goals`. Resolved.

2. **Lint mode dispatch** — resolved by scaffold marker (§A).
   Marker present + violations → block. Marker absent + violations →
   warn-only (grandfathered legacy). No more "newly-scaffolded
   detection" ambiguity.

3. **Pressure-test stability** — resolved by N=5 + population
   assertion (§E). Was Open Q #3 in v2.

4. **The three example scaffolds — promotion path.** Keep in
   `examples/` for v3; promote in a future Spec 028 if real usage
   warrants. Was Open Q #4 in v2; unchanged.

5. **NEW Open Q (panel-derived):** If 026 fails its Jules-workflow
   benchmark gate and gets rewritten / dropped, what happens to
   PR-C? Recommend: PR-C ships only AFTER 026-P0 lands AND 026's
   benchmark passes. If 026 fails the gate, PR-C either rewrites
   against 026's revised schema or gets archived (not orphaned in
   `examples/`). The cross-spec contract is concrete; the rescue
   path is explicit.

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
- ✅ v2 drafted (`482cf4b`)
- ✅ spec-panel on v2 — verdict REVISE, 5+1 findings (panel `a583d6`)
- ✅ **v3 drafted** (this revision, folds all 6 panel findings)
- ⏭ Workflow — IMPLEMENTATION-PLAN.md (next)
- ⏭ Implement PR-A — TDD; ship discipline + scaffold + plugin.lint_capability
- ⏭ Implement PR-B — develop.doc + the long-doc render slice
- ⏭ Implement PR-D — pressure tests (parallel; @pytest.mark.slow)
- ⏭ Implement PR-C — Matcher scaffolds (BLOCKED on 026-P0)

Goal: every future capability (including the `skills` capability
from Spec 026) is authored under this discipline → lint-clean by
construction → no more Codex P2 round-trip cycle. Empirically
falsifiable: count Codex P2 findings on the next capability merged
under this discipline. Target: 0.
