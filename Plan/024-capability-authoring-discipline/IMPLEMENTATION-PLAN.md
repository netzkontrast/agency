# Spec 024 — IMPLEMENTATION-PLAN

Loop output: Design v3 (folds 6 panel findings, `9830570`) → **Workflow**.
Per-phase RED → GREEN → green `python -m pytest -q` → commit → push. Four
PRs; three ship independently, PR-C gates on 026-P0. Review checkpoints
after PR-A Phase A3 (discipline lands on `DEV_SKILLS`) and PR-B Phase B1
(`render_phase` long-doc extension). Ordered: PR-A → PR-B → PR-D (parallel
after PR-A) → PR-C (blocked until 026-P0 lands `MATCHER_SCHEMA_VERSION`).

**Spec §A acceptance bullets → phases:**
- `authoring-capabilities` discipline in `DEV_SKILLS` → A3
- `develop.scaffold_capability(name, kind)` → A2 (RED) + A3 (GREEN)
- `plugin.lint_capability(name)` → A0 (RED) + A1 (GREEN)
- lint MODE DISPATCH via scaffold marker → A0 covers all three branches
  (scaffolded clean→green, scaffolded broken→block, legacy broken→warn);
  A1 implements dispatch
- "scaffolded skeleton lints clean immediately" → A2 cross-asserts A1
- §C SKILL.md → A4; §A self-improvement loop (Reflection SERVES `c374ac3d`) → A5

# PR-A — discipline + plugin.lint_capability (no cross-spec deps; ships first)

## Phase A0 — RED tests for `plugin.lint_capability`

Test names (`tests/test_develop_authoring.py`):
- `test_lint_structural_inputs_returns_chain_next_markers_required`
- `test_lint_role_tag_transform_with_network_imports_flags` (param: `requests`/`httpx`/`subprocess`)
- `test_lint_render_slice_brief_nonempty_and_under_120_chars`
- `test_lint_render_slice_first_sentence_cleaves_on_first_sentence_helper`
- `test_lint_render_slice_legacy_body_drift_flags` (the PR #12 Codex bug)
- `test_lint_consumer_contract_engine_memory_builds_and_lists_tools`
- `test_lint_consumer_contract_search_finds_under_budget`
- `test_lint_token_budget_under_20_tokens_per_verb_cl100k`
- `test_lint_mode_dispatch_marker_present_violations_blocks` (ok=False)
- `test_lint_mode_dispatch_marker_absent_violations_warns` (ok=True, warnings≠[])
- `test_lint_mode_dispatch_marker_absent_clean` (ok=True, warnings=[])
- `test_lint_returns_shape_ok_violations_warnings_skipped_mode`

Fixtures: three in-memory source strings via `textwrap.dedent` —
scaffolded-clean, scaffolded-broken (`# agency-scaffold: v1`),
legacy-broken (no marker). Reuse `tests/conftest.py` engine fixture.

Gate: all RED (verb missing; collection-error RED OK).

Risks: (1) `parse_slices` surface drifts → import via `agency.render` +
import-test that fails loud if renamed. (2) Mode-dispatch 2×2 not fully
covered → three explicit tests above span the relevant branches
(clean+absent is the no-op symmetric case).

## Phase A1 — GREEN `plugin.lint_capability`

Code: `agency/capabilities/plugin.py:~104` (after `lint_skill`) — module
function `lint_capability(name) -> dict` + `@verb(role="transform")` on
`PluginCapability:~219`. Helpers: `_read_scaffold_marker`,
`_check_structural`, `_check_render_slice`, `_check_consumer_contract`,
`_check_token_budget`. Consumer-contract builds `Engine(":memory:",
extra_capabilities=[loaded_cap])` — `plugin.py` already imports `Engine`
for `lint_skill` (no layering inversion, panel F5a). Returns
`{ok, violations, warnings, skipped, mode}`.

Gate: A0 green; full suite green. **Commit + push.**

Risks: (1) `Engine(":memory:")` round-trip slow → target ≤100ms/call;
cache `MCPCodeMode.tools()` per-process. Open in implementation: gate
consumer-contract behind `deep=True` if hot. (2) tiktoken absent in
non-dev installs → already in `[dev]`; import-guard with `pytest.skip`.

## Phase A2 — RED tests for `develop.scaffold_capability`

Test names:
- `test_scaffold_light_emits_single_file`
- `test_scaffold_medium_emits_single_file_plus_ontology_stubs`
- `test_scaffold_heavy_emits_folder_with_init_and_reexport`
- `test_scaffold_first_line_is_agency_scaffold_marker_v1`
- `test_scaffold_returns_artefact_kind_capability_scaffold_with_path`
- `test_scaffold_output_lints_clean_in_block_mode` (cross-asserts A1)
- `test_scaffold_unknown_kind_returns_input_required`

Gate: all RED. Risks: (1) Scaffold trips its own lint (chicken/egg) → A3
iterates template until A2's cross-assertion passes. (2) Files leak to
repo root → use `tmp_path`; scaffold takes a `base_dir` kwarg.

## Phase A3 — GREEN `develop.scaffold_capability` + the discipline

Code: `agency/capabilities/develop.py:~27` — add to `DEV_SKILLS`:
```
"authoring-capabilities": {"name":"authoring-capabilities", "kind":"authoring", "phases":[
  _phase(1, "research", ["read_doctrine"]),
  {"index":2, "name":"scaffold", "produces":["skeleton"],
   "invoke":{"capability":"develop", "verb":"scaffold_capability"}, "inputs":["name","kind"]},
  _phase(3, "author", ["verbs_written"]),
  {"index":4, "name":"lint", "produces":["lint"],
   "invoke":{"capability":"plugin", "verb":"lint_capability"}, "inputs":["name"]},
  _phase(5, "token-check", ["budget_ok"]),
  _phase(6, "commit", ["reflection_recorded"], gate="hard"),
]},
```
`agency/capabilities/develop.py:~146` — `@verb(role="act")
scaffold_capability(self, name, kind="light", base_dir=None) -> dict`.
Module helpers `_render_{light,medium,heavy}_skeleton` emit
`# agency-scaffold: v1` as line 1 + the class-form skeleton from
CAPABILITY-AUTHORING.md §"Capability skeleton" verbatim, parameterized
on `name`. Returns `{result: <path>, artefact: {kind:"capability-scaffold",
name, path, kind, scaffold_version: 1}}`.

Gate: A2 green; A0 cross-assertions hold; full suite green.
**Commit + push.** **REVIEW CHECKPOINT** — `agency:code-review` on the
discipline + scaffold diff (load-bearing — every future capability walks it).

Risks: (1) Skeleton drifts from doctrine → pin to `agency/templates.py:CAPABILITY_SKELETON`;
doctrine + scaffold both reference it. (2) Marker version bumps break
legacy mode → lint reads marker version-agnostically (any `# agency-scaffold:`
prefix → block mode).

## Phase A4 — `skills/authoring-capabilities/SKILL.md`

New file ≤200 words. Frontmatter per spec §C (name, description starts
`Use when…`, `allowed-tools` block). Body: three steps (research /
scaffold / lint) one line each + pointer to
`docs/vision/CAPABILITY-AUTHORING.md`. No `references/` subdir (panel).

Gate: `plugin.lint_skill(name, description)` → `{ok: True}`;
`wc -w SKILL.md ≤ 200`. Assert via
`test_skill_md_lints_clean_and_under_200_words`.

Risks: description summarizes workflow → Claude skips body. Spec §C
mandates pure WHEN triggers; lint enforces "Use when…" prefix.

## Phase A5 — End-to-end discipline walk + reflection wiring

Test names:
- `test_walking_authoring_capabilities_records_reflection_serves_c374ac3d`
- `test_phase_2_scaffold_invokes_develop_scaffold_capability_via_skillrun`
- `test_phase_4_lint_invokes_plugin_lint_capability_via_skillrun`
- `test_hard_gate_phase_6_blocks_until_reflection_recorded`

Code: `agency/capabilities/develop.py` — on gate-pass of
`authoring-capabilities`, write
`Reflection{scope:"observation", serves:"c374ac3d-anchor"}` via
`reflect.note` (precedent: `delegate.dispatch-decision`'s end-of-walk).

Open in implementation: write inside `SkillRun.advance` (generic) vs a
discipline-specific hook. v1 plan: discipline-specific hook (least surface
change); revisit if Spec 026's `next_skill` chain wants the same.

Gate: A5 green; full suite green; PR-A ready for merge.

Risks: anchor reflection id `c374ac3d` not stable across runs. Spec
§Evidence cites `reflection:c374ac3d-anchor` as a durable goal node.
Open in implementation: seed via conftest or
`tests/fixtures/anchor_reflections.json` if missing.

# PR-B — `develop.doc` + long-doc slicing (independent of A and C)

## Phase B0 — RED tests for `develop.doc("authoring", depth=)`

Test names (`tests/test_develop_doc.py`):
- `test_doc_authoring_brief_returns_h1_first_para_toc`
- `test_doc_authoring_brief_under_250_tokens_cl100k`
- `test_doc_authoring_standard_includes_four_named_sections`
  (four-line-summary / decision-tree / common-docstring-mistakes / role-tags)
- `test_doc_authoring_standard_under_900_tokens_cl100k`
- `test_doc_authoring_deep_returns_entire_document`
- `test_doc_authoring_deep_under_5500_tokens_cl100k` (~10% slack)
- `test_doc_unknown_topic_returns_input_required_with_available_list`

Fixture: `tests/fixtures/doc_token_budgets.json` →
`{authoring: {brief: 250, standard: 900, deep: 5500}}`. Gate: all RED.
Risks: token counts drift on doctrine edits → fixture is the gate;
busting it requires deliberate update (forcing function).

## Phase B1 — GREEN `develop.doc` + extend `render.py` for long docs

Code: `agency/render.py` — extend `render_phase` (or sibling
`render_long_doc(path, *, depth)`): reads markdown, splits on H1/H2/H3,
returns per-depth slices (brief = H1 + first-para + H2 TOC; standard =
the four named sections; deep = full bytes).
`agency/capabilities/develop.py:~146` — `@verb(role="transform")
doc(self, topic, *, depth="brief") -> dict`. `topic ∈ {"authoring"}` →
`docs/vision/CAPABILITY-AUTHORING.md`. Unknown topic → input-required
with `available` list.

Gate: B0 green; full suite green. **Commit + push.**
**REVIEW CHECKPOINT** — `agency:code-review` on `render.py` (consumer
surface for future `develop.doc("core"|"goals")`).

Risks: (1) H2 names drift → match on stable anchor slug not display
title; fixture asserts the four anchor slugs. (2) Collision with
`develop.reference` → panel F1a: two contracts, two verbs.

## Phase B2 — wire `develop.doc` into discipline's research phase

Code: `agency/capabilities/develop.py` — phase 1 (`research`) of
`authoring-capabilities` gains `invoke:{capability:"develop", verb:"doc"}`
with `inputs:["topic"]` (default `"authoring"`). Cross-edits Phase A3's
`DEV_SKILLS`. Safe: PR-A shipped `research` as document phase; binding
to a verb is strict refinement (additive).

Gate: add `test_phase_1_research_invokes_develop_doc` (RED in B2, GREEN
with edit). Full suite green; PR-B ready for merge.

Risks: discipline mutated mid-flight → re-bind strictly additive;
SkillRun walkers tolerate it (Spec 025 Phase 1 exercises this).

# PR-C — Matcher scaffolds (GATED on 026-P0 landing `MATCHER_SCHEMA_VERSION`)

## Phase C0 — import-time gate

Code: `examples/{notebook,code_advisor,research_routes}.py` — first
import each: `from agency.ontology import MATCHER_SCHEMA_VERSION`
(comment: "gated on Spec 026 P0"). If 026-P0 not shipped → `ImportError`
at collection; PR-C CI fails loud. Spec §D explicit.

Gate: confirm `MATCHER_SCHEMA_VERSION` on `main` before opening PR-C.
Per spec Open Q #5: if 026 fails its benchmark, PR-C rewrites against
026's revised schema or gets archived (NOT orphaned in `examples/`).

Risks: 026-P0 renames the constant → import-gate fail-loud catches it
pre-merge; subscribe Spec 024 owner to 026-P0.

## Phase C1 — `examples/notebook.py` (pattern mode)

Tests (`tests/test_develop_matcher_modes.py`):
- `test_notebook_scaffold_lints_clean`
- `test_notebook_applies_when_validates_against_matcher_schema`
- `test_notebook_pattern_matches_intent_purpose_with_note_or_journal_kw`
- `test_notebook_pattern_returns_empty_on_unrelated_purpose`

Code: `examples/notebook.py` scaffolded via PR-A's
`develop.scaffold_capability` (commit output verbatim). Single skill
`note-keeping`, `applies_when={kind:"pattern", purpose_kw:["note","journal"]}`.

Risks: scaffold output drifts as marker version bumps → regenerate when
version bumps; assert clean via A1 lint.

## Phase C2 — `examples/code_advisor.py` (verb-code mode)

Tests:
- `test_code_advisor_scaffold_lints_clean`
- `test_code_advisor_applies_when_validates_against_matcher_schema`
- `test_code_advisor_tdd_applies_returns_matches_and_confidence_shape`
- `test_code_advisor_tdd_applies_high_confidence_on_tdd_keywords`
- `test_code_advisor_tdd_applies_zero_on_unrelated`

Code: `examples/code_advisor.py` — `tdd_applies(intent_id) ->
{matches:bool, confidence:float}` decider (role: `transform`) reading
`intent.acceptance` for TDD keywords. Skill `applies_when={kind:"verb_code",
verb_code:{capability:"code_advisor", verb:"tdd_applies"}}`.

Risks: confidence normalization differs across deciders. Open in
implementation: pin to `[0.0, 1.0]` with `0.5` suggest-threshold;
document in verb docstring.

## Phase C3 — `examples/research_routes.py` (llm-select mode)

Tests:
- `test_research_routes_scaffold_lints_clean`
- `test_research_routes_applies_when_validates_against_matcher_schema`
- `test_research_routes_llm_select_prompt_well_formed`
- `test_research_routes_llm_select_picks_quick_for_simple_intent` (stub
  `ctx.sample` → canonical JSON)
- `test_research_routes_llm_select_gibberish_demotes_no_raise`

Code: `examples/research_routes.py` — three sibling skills
(`research-quick`, `research-deep`, `research-empirical`) sharing
`applies_when={kind:"llm_select", llm_select:{prompt:"…", candidates:[…]}}`.
Failure-semantics dispatcher lives in Spec 026 Phase 3; PR-C asserts
fixture well-formedness only.

Risks: `ctx.sample` stub missing → import from Spec 026's
`tests/test_intent_suggests_skill.py`; bake local if absent.

# PR-D — pressure tests (`@pytest.mark.slow`; parallel; ships after PR-A)

## Phase D0 — N=5 RED scenario harness

Test: `tests/test_authoring_pressure_scenarios.py::test_red_subagent_without_discipline_produces_diverse_violations`.
Marked `@pytest.mark.slow`; skipped unless `AGENCY_RUN_PRESSURE_TESTS=1`.

Dispatch N=5 subagents (via `delegate.fan_out`) for "Add a `notebook`
capability with `save(content, path)` and `list(directory)`" WITHOUT the
discipline. Run `plugin.lint_capability` on each. **Assertion (panel
F2a)**: union of violation kinds across the 5 runs has cardinality ≥2.

Open in implementation: live dispatch in CI expensive. v1 plan: results
recorded in `tests/fixtures/pressure_red.json`; test loads + asserts.
Live dispatch only under `AGENCY_RUN_PRESSURE_TESTS_LIVE=1`.

Risks: CI flake / cost → fixture-replay is the default.

## Phase D1 — N=5 GREEN scenario harness

Test: `…::test_green_subagent_with_discipline_all_runs_ok`. Same N=5
dispatch, pointed at `authoring-capabilities`. Lint each.
**Assertion**: all 5 runs produce `{ok: True}`. Outcome deterministic
even if route varies. Stored in `tests/fixtures/pressure_green.json`.

Risks: 4/5 pass, 1/5 fails → failure analysis feeds back into A1 lint
rules or A3 skeleton template; not a test-tuning exercise.

## Phase D2 — rationalization table monotonicity

Test: `…::test_rationalization_table_grows_monotonically`. Parse
`## Rationalization table` in `docs/vision/CAPABILITY-AUTHORING.md` into
a row-set; compare against snapshot
`tests/fixtures/rationalization_table_snapshot.json` (seven seeded rows).
**Assertion**: every snapshot row exists in current doc (additions OK;
silent removals fail). Updated via `--update-snapshot` flag.

Risks: markdown parsing brittle → parse on pipe-delimiter shape only.

---

## Test additions / files
- Tests: `tests/test_develop_authoring.py` (PR-A A0/A2/A4/A5 + PR-B B2),
  `tests/test_develop_doc.py` (PR-B B0),
  `tests/test_develop_matcher_modes.py` (PR-C C1/C2/C3),
  `tests/test_authoring_pressure_scenarios.py` (PR-D).
- Fixtures: `tests/fixtures/{doc_token_budgets,pressure_red,pressure_green,rationalization_table_snapshot}.json`.
- Create: `skills/authoring-capabilities/SKILL.md` (A4),
  `examples/{notebook,code_advisor,research_routes}.py` (C1/C2/C3).
- Modify: `agency/capabilities/develop.py` (A3+A3+B1+A5+B2),
  `agency/capabilities/plugin.py` (A1), `agency/render.py` (B1),
  `agency/templates.py` (A3 `CAPABILITY_SKELETON`).
- Consumed already-shipped: `docs/vision/CAPABILITY-AUTHORING.md`,
  `agency/render.py:parse_slices`, engine tag propagation, `_wire_skill_tags`.

## Risk register (cross-PR)
| Risk | Mitigation |
|---|---|
| PR-A consumer-contract lint slow | Cache `Engine(":memory:")` per-process; `deep=True` gate if hot |
| PR-B doc-budget drift | Fixture is the gate; deliberate-update forcing function |
| PR-C ships before 026-P0 | Import-time gate fails loud; do not open PR-C until 026-P0 on `main` |
| PR-D subagent flake/cost | Fixture-replay default; live dispatch behind env var |
| Mode dispatch regresses on legacy caps | A0's three explicit dispatch tests + full-suite-green |
| Marker version bumps break legacy mode | Version-agnostic prefix check (any `# agency-scaffold:` → block) |

Loop: v3 spec drafted (`9830570`); **IMPLEMENTATION-PLAN drafted** (this
doc); next PR-A (no deps) → PR-B (no deps) → PR-D (parallel after A) →
PR-C (BLOCKED on 026-P0). Goal: every future capability authored under
`authoring-capabilities` → lint-clean by construction. Empirical
falsifier: Codex P2 findings on the next capability merged under this
discipline. Target: 0.
