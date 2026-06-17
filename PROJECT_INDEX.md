# Project Index — agency

## Substrate
- language: python
- package_config: pyproject.toml
- test_runner: pytest (inferred)

## Entry points
- `agency = "agency.cli:main"`
- `agency-mcp = "agency.__main__:main"`
- `agency-doctor = "agency.__main__:doctor_main"`

## Notable patterns
- agency-style capability folder pattern
- Claude Code plugin manifest (.claude-plugin/)
- MCP server config (.mcp.json)
- skills/<name>/SKILL.md disclosure pattern
- Plan/NNN-slug/spec.md doctrine

## Recent activity
- _no recent reflections recorded_

## Macro-structure

**Capabilities:** `analyze/`, `branch/`, `clusters/`, `delegate/`, `develop/`, `document/`, `dogfood/`, `gate/`, `intent/`, `jules/`, `migrations/`, `music/`, `novel/`, `plugin/`, `prompt/`, `reflect/`, `research/`, `shell/`, `skill_generator/`, `skills/`, `subagent/`, `thinking/`, `workspace/`

### `./` (1 files)
- **conftest.py**

### `Plan/_research/novel-mvp-source/legacy-skills/dramatica-theory/scripts/` (1 files)
- **split_book.py** — Split the Dramatica book Markdown into thematic reference chunks.

Reads /home/claude/dramatica.md (output of pdf-to-markdown skill against
the source PDF) and writes 9 chunk files into ./references/.

Each chunk gets a written preamble describing what's in it and where it
sits in the source — so the SKILL.md can reference chunks by topic
without preloading them.

Boundaries are line-numbers verified against the source by inspecting
the headings.

### `agency/` (55 files)
- **__init__.py** — agency — an installable Claude Code plugin: the v4 core on the real substrate.

Four concepts (Intent, Capability, Lifecycle, Memory) + a FastMCP engine, over a
real GraphQLite bi-temporal graph.
- **__main__.py** — `python -m agency` — start the Agency MCP server (stdio).

Three console-script entry points (Spec 039):
  `agency`        — CLI for bash callers (see ``agency.cli:main``).
  `agency-mcp`    — MCP server entry; this module's :func:`main`.
  `agency-doctor` — bare-CLI health check; this module's
                    :func:`doctor_main`.
- **_capability_loader.py** — Spec 032 §B — capability folder loader.
- **_checks.py** — Spec 011 — structural Lifecycle checks (the auditable residue of a run).

A Lifecycle `check` is the post-hoc read over whatever a delegation/subagent
produced — same observe family as `COMPLETED ≠ done`/`verify` (CORE.md:31,33-35),
NOT a new capability's act.
- **_coverage_gate.py** — Spec 169 Slice 1 — typed GateResult + pure evaluate() for the CI gate.

The CI gate has three concerns: coverage trend (non-decreasing per
capability), flake count (zero tolerance), and verb-test coverage (every
verb has a test).
- **_db_path.py** — DB path resolution per Spec 020 — central .agency/session.db.

Resolution order (Spec 020 Done When item):
  1.
- **_doctor_shapes.py** — Spec 170 Slice 1 — typed Field/Section/Report shapes for `agency_doctor`.

The doctor surface today is an ad-hoc dict with per-section dict bodies.
Spec 170 lifts it to a typed contract so every section has the same
shape + the invariants are enforced at construction:

  ready=False ⇒ hint is non-empty (pipx-HINT pattern, Spec 065 generalised)
  source ∈ {env, extra, graph, registry}  (where the value comes from)

Slice 1 ships the shapes + invariants offline-clean.
- **_embedder_handle.py** — Spec 181 Slice 1 — typed EmbedderHandle for the reflect-embedder upgrade.
- **_enhancement_stubs.py** — Wave 3-12 enhancement Slice 1 catalogue — typed stubs for every drafted spec.

Each EnhancementSliceStub records the Slice 1 commitment: the spec_id +
slug + wave.
- **_entities.py** — Spec 289 — SQLModel typed entities derived from the graph ontology.

The ontology (`Ontology.nodes` = label→required fields, `Ontology.enums` =
(label,field)→allowed set) is the schema authority.
- **_entity_store.py** — Spec 289 Slice 2 — the graph-authoritative typed projection.

Every graph data entity is MIRRORED into a typed row in a SQLModel
(``table=True``) table that shares graphqlite's ONE ``.db`` file.
- **_enums.py** — Spec 284 — projected-enum substrate.

A *projected enum* is a field whose graph value is a closed enum, but whose
caller-facing parameter accepts free text and is PROJECTED onto a canonical
member — keeping the original rich text in a paired ``<field>_detail`` prop so
nothing is lost (the non-lossy contract).
- **_envelope.py** — Spec 146 Slice 1 — engine-output-prefix discipline.

The Claude API's prompt-caching is a prefix-match: any byte change anywhere in
the cached prefix invalidates everything after it.
- **_frontmatter.py** — Spec 283 (+ minimal Spec 278) — frontmatter emit / parse / hash.

The render substrate writes each graph entity to a markdown file carrying a
YAML-ish frontmatter block (the node id + key fields, so a re-render is
byte-identical and `parse` reconstructs the slice).
- **_hooks.py** — Spec 280 Slice 1 — hooks install verification + foreign-hook wrapping.

The agency plugin ALREADY ships hooks (`hooks/hooks.json` + Spec 076
unified-event-hook dispatcher).
- **_host_bridge.py** — Spec 285 Slice 1 — the host-bridge seam.

`ctx.sample()` / `ctx.elicit()` live on the FastMCP ``Context``, which is
injected only into wired tools — capability verbs (and the ``skill_walk``
walker) receive the agency ``CapabilityContext`` and have no handle to the
client.
- **_host_llm.py** — Spec 279 Slice 1 — host-LLM delegation envelope.

When the AnthropicDriver isn't capable (no ``ANTHROPIC_API_KEY`` + no
injected client), ``driver.backend()`` returns ``"none"`` and
``driver.complete`` raises ``AUTH_FAILED``.
- **_invoke.py** — Spec 286 Phase-1 / A3 — the `Registry.invoke` decomposition.

`Registry.invoke` was a ~105-line god-method fusing five responsibilities.
- **_link_finding.py** — Spec 173 Slice 1 — typed LinkFinding for the reflection-edge linter.

Every Reflection in the graph MUST carry two edges: `SERVES` to an
Intent (Spec 002 provenance moat) and `OBSERVED_DURING` to the Event
that produced the observation (Spec 076 unified-hook discipline).

Spec 173 Slice 1 ships the typed lint finding so the audit + the CI
gate consume one shape.
- **_llm.py** — Spec 092 G3 — the LLM-decider boundary (an ``llm`` Driver on the Spec-002 registry).

A constrained classifier the engine uses where a small judgement is needed without an
autonomous agent — today `intent.suggests`'s ``llm_select`` Matcher; later the agentic
pressure-test deciders (Spec 011).
- **_loop_events.py** — Spec 156 Slice 1 — typed LoopEvent shape + pure loop detector.

The dogfood loop needs to know when an agent is repeating itself: 3 raw
`git commit` calls in a row, 4 identical Edit invocations, the same
spec being re-walked over and over.
- **_monitor.py** — Spec 021 — the engine Monitor channel.

Claude Code's plugin system supports ``monitors/monitors.json`` — each entry is
a long-running shell command whose stdout lines are delivered to the agent as
notifications.
- **_overflow.py** — Spec 154 Slice 1 — output overflow capture + recall (pure library).

When a verb returns more than the token budget (Spec 023), the engine
truncates — and the truncated tail was LOST, even though it might hold
the answer.
- **_predicates.py** — Spec 011 — decidable gate predicates (pure module helpers, not verbs).

A predicate that blocks a phase IS a `gate` (CLUSTERS:18).
- **_pressure.py** — Spec 011 — pressure-test rubric + run step (Plan-133 port, the `research` model).

Subagent pressure-tests answer the question neither a frontmatter linter nor a
runtime hook can: *does a discipline skill actually change a fresh agent's
behaviour under pressure, or does the agent rationalise it away?* This ships as
**skill-walk helpers + a run step**, NOT a capability:

- `load_scenario` / `score_transcript` are pure `transform` helpers (CLUSTERS:20)
  the `agentic-pressure-test` skill calls;
- `run_pressure_test` records provenance through existing core nodes
  (`Artefact{kind: scenario|pressure-run}`) + a scored `Gate` (via `gate.check`)
  — no `Scenario`/`PressureRun` labels.

The run step takes the worker transcript as an INPUT (the `subagent.develop`
LLM-out-of-the-verb pattern); the `dry_run=True` default is the only runnable v1
path (synthetic `ambiguous`, no dispatch).
- **_prosody.py** — Shared prosody helpers — deterministic, driver-free text math.

Lifted from music/_main.py + novel/_main.py post Round-1 sc-analyze
finding F2 ("_syllables_word duplicates music's _syllables; same
heuristic, two implementations, drift risk").

Both music's `lyric_report` family and novel's `analyze_readability`
need a syllable count; promoting to a shared module so one fix lands
in one place.
- **_render.py** — Spec 283 Slice 1 — the capability render substrate (graph → markdown view).

A capability declares a `RenderSpec`: a list of `RenderRule`s binding a node
`label` to (output_path, frontmatter, body, kind).
- **_replay_invariants.py** — Spec 195 Slice 3 — monotone invariant verification for replay chains.

Spec 195 Slice 2 ships `dogfood.replay_events(for_intent_id)` which
returns events ordered with each event's `prior_event_id` pointing at
the previous event's id.
- **_research_citation.py** — Spec 168 Slice 1 — typed Citation shape + backend-selection invariant.
- **_retry.py** — Spec 282 — ``retry_transient``: the correct retry primitive.

Replaces the anti-pattern that produced the evidence retry storm
(``scripts/ingest_canon.py`` looping ``for attempt in range(1, 40)`` "while
progress is made"): retry a call ONLY when its result is a wire error envelope
classified ``transient``.
- **_runner.py** — Spec 073 — the toolchain `runner` boundary.

A thin, stubbable boundary (like `JulesClient` / `GitClient`) so `dogfood`'s
toolchain verbs can be exercised in tests without shelling out.
- **_skill_parse.py** — Spec 152 Slice 1 — typed Skill/Phase parse boundary.

A single parse + validate point for skill / phase dicts so the walker
(Spec 018), SkillDoc derive (Spec 081), and graph-promotion (Spec 026)
all consume the same typed shape — no more ad-hoc `phase.get("gate")`
scattered across the codebase.

Slice 1 surface (this module):
- `Phase` / `Skill` frozen dataclasses with a `variant` discriminator
  (`"hard_gate"` / `"verb_bound"` / `"step"`).
- `parse_phase(dict) -> ParseResult[Phase]`,
  `parse_skill(dict) -> ParseResult[Skill]`.
- Typed failure codes on `Codes`: `SKILL_PARSE_INVALID`,
  `PHASE_MISSING_FIELD`, `PHASE_UNKNOWN_KIND`.
- Round-trip — `parse_clean(s).to_dict() == s` for any well-formed input.

Live-skill compatibility (Codex review on PR #127):
- `gate` accepts `"hard"` / `"soft"` / `"computed"` (the gates the live
  registry already uses; see `agency/capabilities/music/ontology.py`,
  `agency/capabilities/subagent/_main.py`, `agency/capabilities/skills.py`).
- Top-level `kind` (e.g.
- **_substrate_tools.py** — Substrate tools as a registered set — Spec 286 Phase 2 / A5.

The engine exposes a handful of WIRE TOOLS that are **not** capability verbs:
``lifecycle_gate`` · ``memory_graph_provenance`` · ``hook_event`` ·
``intent_bootstrap`` · ``agency_install`` · ``agency_doctor`` ·
``agency_welcome``.
- **_tokens.py** — Spec 082 — the token-count boundary.

ONE place to count tokens, with tiers (best first):
  1.
- **_typed_shapes_wave1.py** — Spec 171 + 175 + 176 Slice 1 — typed shapes for the wave-1 batch.
- **_typed_shapes_wave1_part2.py** — Wave-1 enhancement Slice 1 batch — 8 typed shapes.

Specs 155 / 160 / 163 / 166 / 167 / 172 / 174 / 177.
- **_typed_shapes_wave3.py** — Wave-3 enhancement Slice 1 batch — substantive typed shapes (Specs 178/179/180/182/183).

Promotes 5 wave-3 specs from catalogue stub (agency/_enhancement_stubs.py)
to substantive Slice 1 code.
- **_typed_shapes_waves4_12.py** — Waves 4-12 enhancement Slice 1 batch — substantive typed shapes.

Promotes every wave-4..12 spec (184-277, minus 195/281) from catalogue
stub to substantive Slice 1.
- **_verb.py** — Spec 286 Phase-1 / A4 — the typed `

_…(content omitted to fit token budget)_
