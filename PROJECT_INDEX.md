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

**Capabilities:** `analyze/`, `branch/`, `clusters/`, `delegate/`, `develop/`, `discover/`, `doctrine/`, `document/`, `dogfood/`, `gate/`, `intent/`, `jules/`, `manage/`, `migrations/`, `mode/`, `music/`, `novel/`, `panel/`, `persona/`, `plugin/`, `prompt/`, `recommend/`, `reflect/`, `research/`, `select/`, `shell/`, `skill_generator/`, `skills/`, `subagent/`, `symbols/`, `thinking/`, `workspace/`

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

### `agency/` (61 files)
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
- **_clarity.py** — Intent clarity — the substrate readiness signals + score (Spec 307 §Refinement).

The clarity score is the home of the "is this intent clear enough to confirm?"
question.
- **_codes_coverage.py** — Spec 151 — ToolResult Codes coverage audit (engine-side core).

Moved out of ``scripts/check_codes_coverage.py`` (Spec 151 Slice 3) so the
engine — ``agency_doctor`` — can import the audit WITHOUT depending on the
dev-only ``scripts/`` tree (the wheel packages only ``agency``; importing
``scripts.*`` at runtime would crash the installed plugin).
- **_config.py** — Unified ``.agency/config.yaml`` — Spec 328 Slice 1 (resolver + registry).

A single home for all agency config.
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
- **_frugal.py** — Frugal core discipline — Spec 326 Slice 1 (level + render).

Agency's own minimal-code reflex (a redevelopment, not a port): a ladder + a
non-negotiable safety floor.
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
- **_install_adapters.py** — Spec 327 — multi-agent self-installer.

One ``surface_card`` (derived from the live registry + the Spec 326 frugal
discipline) projected into each agent's native instruction format.
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
- **_schema_coverage.py** — Spec 153 — template/schema coverage audit (engine-side core).

Moved out of ``scripts/check_schema_coverage.py`` (Spec 153 Slice 3) so the
engine — ``agency_doctor`` — can import the audit WITHOUT depending on the
dev-only ``scripts/`` tree (the wheel packages only ``agency``).
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
- **_verb.py** — Spec 286 Phase-1 / A4 — the typed ``Verb`` value object.

A capability verb was historically an untyped ``dict`` —
``{"role", "fn", "inject", "tags", "param_enums", "name"?}`` — built by the
``@verb`` decorator (``fn._verb``), normalised by ``_wrap_method`` /
``Registry.register``, and **mutated in place** (``_wire_skill_tags`` does
``spec.setdefault("tags", set()).add(...)``).
- **_wet_verify.py** — Spec 164 Slice 1 — typed VerifyResult shape for wet implementation-discipline phases.

The Slice 2 wet path (Spec 147 AnthropicDriver) runs the discipline-skill
verify step against a phase's outputs + the live graph; this slice ships
the typed return shape every verifier — wet OR scaffold (the deterministic
fallback) — coerces to.

Per Spec 050 graceful-degradation pattern: when `[anthropic]` is absent
(or the API key isn't provisioned), `matcher == "scaffold"` for every
discipline.
- **_wire_envelope.py** — Spec 286 Phase-2 / A7 — `WireEnvelope`: the ONE owner of the wire-shape rule.

The "strip / re-wrap `{result}`" rule (Spec 019) and the Spec 282 failure
envelope (`{ok, error:{code,message,severity,retryable,trace_id}}`) were
duplicated across `engine._wire`/`engine._shape_wire_result` and
`cli._structured`.
- **cache.py** — Spec 031 §E / Task 2.4 — atomic JSON cache for skill emit idempotency.

The cache lives at <cache_dir>/skill-cache.json — a single document mapping
capability name → {hash, files: [paths]}.
- **capability.py** — Capability — the craft (the open concept).
- **cli.py** — Bash-callable engine — the L3 layer of the harness-in-harness ladder (Click).

A bash-only agent (Jules, Codex, a raw LLM with a shell) has no MCP client and no
Skill loader.
- **disclosure.py** — Adaptive disclosure renderer — Spec 023 Phase 1.

A pure rendering pass over Capability/Verb/Skill nodes.
- **engine.py** — Engine — one FastMCP server + one graph.

**Code-mode IS the contract** (lean: no separate four-verb surface).
- **install.py** — Setup for the Agency Plugin for Claude Code.

This is the "in setup" that maps the harness-in-harness MICRO-skills (the engine's
capability verbs) into MACRO-skills (the capabilities themselves) behind a single
`help` discovery surface.
- **intent.py** — Intent — the human-owned root (why/what merged; deliverable is an attribute).

capture -> confirm -> (amend via supersede).
- **lifecycle.py** — Lifecycle — task/agent state-machine.
- **memory.py** — Memory — the moat.
- **ontology.py** — Strict, EXTENSIBLE ontology for the agency graph.

The **core** defines the irreducible base: every node type's required-field
schema, the enumerated edge set, and the closed enums.
- **skill.py** — Micro-step skill walker.

A skill is a Lifecycle of ordered Phases (a schema a capability contributes, e.g.
the `develop` or `plugin` skills).
- **skill_emit.py** — Spec 031 §D + Spec 032 §G — per-capability skill emission pipeline.
- **templates.py** — Templates — the prestructure for the resulting document of each step of a chain.

A small library of *living document* skeletons a Capability `act` fills in.
- **toolresult.py** — ToolResult — the in-sandbox envelope a verb may return.

Per Spec 001 (Option C, the canon-aligned, token-lean choice): the envelope is
an INTERNAL Python dataclass, NOT the wire shape.

### `agency/_drivers/` (2 files)
- **__init__.py**
- **_anthropic.py** — Spec 147 — the canonical AnthropicDriver boundary (Slice 1: inference surface).

ONE typed surface every verb that needs LLM inference (thinking, prompt-composition,
the dogfood-classifier, scene-writer, …) wires through, so the engine stops doing it
"lossy-in-chat" (Spec 110) or via one-off shims (Spec 026's pending llm_select).

### `agency/_middleware/` (2 files)
- **__init__.py** — Engine middleware — cross-cutting helpers that are NOT capabilities.

The canon (CORE.md:16-18) names loop-detection *middleware*, not a concept: it
is a fast-twitch self-interrupt signal an engine/hooks layer can run, never a
discoverable verb.
- **loop.py** — Loop-detection middleware (Spec 011, port of the-agency-system Plan 119).

A pure, stdlib-only signal: do the recent messages / tool results repeat enough
to indicate the agent is stuck in a loop? Jaccard similarity over 3-char
shingles, pairwise max over the last 4 messages + last 5 tool results (≤ 9² = 81
pairs), detected when the max ≥ 0.7.

This is **middleware, not a concept** (CORE.md:17): `detect_loop` is never
registered as a capability verb and never sources its own history — the caller
(a future hooks layer) supplies `messages`/`tool_results`.

### `agency/capabilities/` (3 files)
- **__init__.py** — Capabilities — discovered by REFLECTION, not hand-wired.

Drop a module in this package that defines a `Capability` instance OR a
`CapabilityBase` subclass at module level; `discover_capabilities()` finds both via the stdlib
reflection APIs (`pkgutil.iter_modules` to walk this package's directory +
`importlib` to import each module + `isinstance`/`issubclass` to pick them out).
The engine calls `discover_capabilities()` and registers everything, and auto-wires one MCP
tool per verb from the verb signature (`inspect.signature`).
- **_embed.py** — Embedder boundary — pluggable semantic-ranking backend.
- **_vcs.py** — _vcs — the version-control boundary the `workspace` and `branch` capabilities
talk to.

`VCSBackend` is a Protocol; `GitClient` is the default backend — real `git` (and
`gh` for PRs) via subprocess.

### `agency/capabilities/analyze/` (13 files)
- **__init__.py** — analyze — multi-axis decidable code analysis (Spec 042).

Folder-form capability.
- **_architecture.py** — Spec 042 / Spec 051 — analyze.architecture axis (dependency graph + structural).

Rules shipped:
  A001 — circular import (fail).
- **_bandit.py** — Spec 050 — bandit wrapper.

Composes bandit's CWE-mapped Python security ruleset into the agency
Finding shape.
- **_findings.py** — Spec 042 — Finding shape (the contract).

Every analyze.* axis returns a list of Finding value objects.
- **_main.py** — analyze — multi-axis decidable code analysis (Spec 042).
- **_paths.py** — Spec 048 — analyze.paths axis.

Surfaces intent-shape patterns that suggest a missing specialized
capability would shorten the intent→artefact path.
- **_performance.py** — Spec 042 — analyze.performance axis (AST-based decidable checks).

Rules shipped (v1):
  P001 — nested-loop on the same iterable (warn).
- **_quality.py** — Spec 042 — analyze.quality axis (decidable lint rules only).

Rules shipped (v1):
  Q001 — unused-import (warn).
- **_radon.py** — Spec 050 — radon wrapper.

Composes radon's cyclomatic complexity + maintainability index into
the agency Finding shape.
- **_ruff.py** — Spec 050 — ruff wrapper.

Composes ruff's 700+ Python lint rules into the agency Finding shape.
Degrades silently when ruff isn't on PATH (Spec 050 §"compose, don't
replace" — internal Q001-Q004 still fire in that case).

Subprocess + JSON; no Python-level ruff import (ruff is a Rust binary
anyway).
- **_security.py** — Spec 042 — analyze.security axis (decidable patterns only).

Rules shipped (v1):
  S001 — eval/exec call (fail).
- **_subprocess_analyzer.py** — Spec 286 — the shared subprocess-analyzer template (Template Method).

The ruff / bandit / radon wrappers all repeated the identical scaffold:

    which-guard → ``subprocess.run(argv, capture_output, text, timeout)``
    in a TimeoutExpired/OSError guard → returncode tolerance → ``json.loads``
    in a JSONDecodeError guard → payload→Finding mapping.

The only per-tool variation is the ``argv``, the acceptable return codes, and
the payload→Finding mapping.
- **_walk.py** — Shared file-walking helpers for the analyze axes (DRY).

Every axis (_quality, _security, _performance, _architecture) needs
the same: walk a tree for ``.py`` files (skipping ``__pycache__``,
``.venv``, ``.git``, etc.), and read each file safely.

### `agency/capabilities/branch/` (2 files)
- **__init__.py** — branch — finish a development branch.
- **_main.py** — branch — finish a development branch: detect state, then merge / open a PR /

Branch inspects the working tree and remote state and finishes the branch the appropriate way — merge when clean, a PR when review is needed, or a clear report of what blocks completion.

### `agency/capabilities/delegate/` (2 files)
- **__init__.py** — delegate — agent orchestration: fan-out + quota + join.
- **_main.py** — delegate — agent orchestration: fan-out + quota + join.

### `agency/capabilities/develop/` (2 files)
- **__init__.py** — develop — discipline-walk templates + scaffolds.
- **_main.py** — develop — the development-workflow capability.

### `agency/capabilities/discover/` (3 files)
- **__init__.py** — discover — guided intent-discovery capability (Spec 307 program · 308 scaffold).

The Intent pillar's prompt-shaped peer: it turns a one-sentence seed into a
grounded, clarity-gated, confirmed Intent by interleaving research-grounding
with AskUser elicitation.
- **_main.py** — discover — guided intent discovery (Spec 307 program · 308 scaffold).

Use when: a fresh or vague intent needs guided discovery BEFORE work begins —
an underspecified ask, a missing acceptance test, a "not sure what I want yet".
The capability turns a one-sentence seed into a grounded, clarity-gated,
confirmed Intent by interleaving research-grounding with AskUser elicitation.
Triggers:
- An underspecified ask arrives and the WHY is captured, not discovered
- An intent has no measurable acceptance criteria yet
- Work is about to start against an unconfirmed or ungrounded intent
Red flags:
- Starting work against an unconfirmed intent → run ``discover.interview`` first
- Inventing AskUser options instead of deriving them from evidence → ``discover.ground``
- Treating a one-line seed as a finished intent → walk ``guided-discovery``

Spec 308 is the SCAFFOLD: it lands the package, the consolidated ontology
(Spec 307's locked node/edge/enum/schema surface), this docstring-derived
SkillDoc, and the derived ``discover-usage`` walkable — an empty-but-discoverable
capability the 17 children (309-325) fill in.
- **ontology.py** — discover ontology — Spec 307 consolidated OntologyExtension (locked surface).

Registers the WHOLE intent-pillar program's node/edge/enum/schema surface ONCE
(Spec 307 §"The ontology"), so the 17 child specs (309-325) populate node
*instances* without ever re-touching the schema.

### `agency/capabilities/discover/clusters/` (7 files)
- **__init__.py** — discover.clusters — cluster mixins composed into the single DiscoverCapability.
- **_base.py** — discover.clusters._base — the shared mixin every child cluster composes.

Spec 308 establishes the foundation; child specs (309-325) add their helpers
here as they implement (``_record_turn`` for interview/clarify, ``_session`` /
``_session_of`` for the session lifecycle, ``_clarity_inputs`` for the Spec 322
score).
- **ask.py** — discover.ask — the reusable well-formed AskUser question primitive (Spec 310).

The ONE place the well-formed-question rules live (option count · recommended-
first · multiSelect gate · header budget · derive-not-invent).
- **clarify.py** — discover.clarify — the ambiguity-resolution loop (Spec 311).

Finds what is still vague in a draft Intent, asks ONE targeted question per
ambiguity (composing discover.ask — 310 owns the well-formed-question contract),
folds each verbatim answer back into the Intent BI-TEMPORALLY (intent.amend —
supersede, prior revision retained), and records a CLARIFIES trail — until the
Intent's residual ambiguity drops below threshold or a max-rounds budget is hit.

The ambiguity heuristics live in data/ambiguity-signals.json (the Driver seam,
Spec 147, sharpens questions from GROUNDS evidence in Slice 2).
- **interview.py** — discover.interview — the adaptive elicitation engine (Spec 309).

Guided-exploration core of the Spec 307 program: turns a one-sentence seed into a
DRAFT Intent by running an adaptive beat-chain, recording every turn as graph
provenance (Goal 2 — *how the WHY was discovered*).
- **refine.py** — discover.refine cluster — Intent clarity scoring + (Spec 320) refinement.

Spec 322 lands ``clarity`` here (the cluster that also holds ``refine``, Spec 320):
the Intent-readiness scorer the ``guided-discovery`` discipline's confirm gate
reads.
- **scope.py** — discover.scope cluster — structure-layer verbs (Spec 317 acceptance, 318 scope).

Spec 317 lands ``acceptance`` here: it derives testable, Gherkin-shaped acceptance
criteria from the Intent's ``deliverable`` — DERIVED, never invented.

### `agency/capabilities/doctrine/` (2 files)
- **__init__.py** — doctrine — queryable engineering principles + behavioral rules (Spec 303).
- **_main.py** — doctrine — queryable engineering principles + behavioral rules (Spec 303).

Closes the SuperClaude/superpowers port audit: PRINCIPLES + RULES were the only
unported aspect of that doctrine.

### `agency/capabilities/document/` (7 files)
- **__init__.py** — document — graph-native rendering + briefing (Spec 043).

Folder-form capability.
- **_explain.py** — ``document.explain`` — code → educational text via composition.

NO LLM.
- **_index_repo.py** — ``document.index_repo`` — the 94%-reduction repo briefing.
- **_interconnect.py** — graph<->markdown interconnect (Spec 292).

The premise flip: markdown files are no longer a one-way *rendered view* of
the graph — they are an editable PEER surface that round-trips back into it.

Mechanism (keep-both, bi-temporal, stable anchor):

- A participating ``.md`` file carries a stable ANCHOR on its first line::

      <!-- agency-node: document:abc12345 -->

  reusing the existing HTML-comment marker convention (cf.
- **_main.py** — document — graph-native rendering + briefing (Spec 043).
- **_render.py** — Scope renderers for ``document.render`` — graph → markdown.

Each function takes a Memory and returns the rendered markdown for
its scope.
- **_templates.py** — Markdown rendering primitives shared across render scopes.

### `agency/capabilities/dogfood/` (2 files)
- **__init__.py** — dogfood — graph-native observation ledgers (Spec 017 + 020 v2).

Folder-form per Spec 060 §Phase 3 — promoted from `dogfood.py` so the
capability can ship its own `templates/` + `schemas/` subfolders.
- **_main.py** — dogfood — graph-native observation ledgers (Spec 017).

### `agency/capabilities/dogfood/clusters/` (6 files)
- **__init__.py** — dogfood.clusters — cluster mixins composed into the single DogfoodCapability.

Spec 286 P3 — the ~1147-line ``dogfood`` god-class split into one mixin per
cluster.
- **_base.py** — dogfood.clusters._base — shared DogfoodCapability infrastructure (Spec 286 P3).

Dogfood's verbs lean on module-level helper functions (the amendment
classifier rules, the observation-header parser, the export version
constant) rather than instance-level driver wiring.
- **amendment.py** — dogfood.amendment — Reflection→spec-amendment classifier (Spec 150/147/279).
- **observe.py** — dogfood.observe — graph-native observation ledgers (Spec 017).
- **portage.py** — dogfood.portage — JSON export + replay for merge-conflict recovery (Spec 020).
- **session.py** — dogfood.session — session-tracking: decisions, boundary audit, replay (Spec 114/195/154).

### `agency/capabilities/gate/` (2 files)
- **__init__.py** — gate — a reusable, programmatic gate predicate.
- **_main.py** — gate — a reusable, programmatic gate predicate.

### `agency/capabilities/intent/` (2 files)
- **__init__.py** — intent — Spec-091 critical-thinking capability.
- **_main.py** — intent — critical-thinking methods that reason about the serving intent (Spec 026/091).

### `agency/capabilities/jules/` (7 files)
- **__init__.py** — jules — the agent capability (folder form per Spec 060 §Phase 3,
- **_main.py** — jules — the agent capability.
- **api.py** — Minimal, self-contained Jules REST client (vendored into the agency plugin).

A thin client for the Jules REST API — the two calls the `jules` capability needs
(`jules_create` and `jules_get`).
- **patch.py**
- **preambles.py** — Jules dispatch-prompt preambles + Mode A/B assembler (Spec 013 Phase 2).

Per ``Plan/013-…/DESIGN.md`` "Design — `_jules_preambles.py`":

- **One canonical preamble** (``PREAMBLE``) carrying the per-dispatch
  must-name tool list + a literal pointer to AGENTS.md + AGENCY_PROTOCOL.md.
- The doctrine (the five invariants from ``AGENCY_PROTOCOL.md``) lives at
  the repo root and is paid for once per snapshot / clone — NOT once per
  dispatch.
- ``assemble(source, starting_branch, prompt, preset_name=...)`` chooses
  Mode A (dogfood, ``source == DISPATCH_SELF_SOURCE``) vs Mode B
  (delegate, anything else).
- **skills.py** — Jules-specific Lifecycle skill templates (Spec 013 Phase 5+).

A skill IS a capability (CORE.md:47-62) — Lifecycle templates of atomic
gated step-graphs.
- **watch.py**

### `agency/capabilities/manage/` (2 files)
- **__init__.py** — manage — generic CRUD over every graph node type (Spec 293).
- **_main.py** — manage — generic CRUD over every graph node type (Spec 293).

The write/read management surface that completes the Memory pillar: a single,
capability-AGNOSTIC CRUD over EVERY ontology label, so every aspect of the
graph — Document, Intent, Track, Novel, Reflection, Session, … — has Create,
Read, Update, Amend and Retract without per-capability code.

### `agency/capabilities/mode/` (2 files)
- **__init__.py** — mode — SuperClaude behavioral modes, first-class (Spec 295).
- **_main.py** — mode — behavioral modes, first-class (Spec 295).

A native reimplementation of SuperClaude's behavioral modes: postures that
change HOW the agent operates.

### `agency/capabilities/music/` (7 files)
- **__init__.py** — music — clustered domain capability (Spec 093 master / Spec 094 lifecycle child).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module).
- **_main.py** — music — clustered domain capability (Spec 093 master + Specs 094-100 + 115).

Music graduates from ``examples/music.py`` into a first-class folder-form
capability under ``agency/capabilities/music/`` (Spec 094).
- **_slug.py** — music slug — single source of truth for the music capability's slug shape.

Both ``_main.py`` (verbs) and ``drivers_production.py`` (FileStateDriver disk
layout) need slugs.
- **config.py** — music config — Spec 115 production-binding config layer.

Loads `.agency/music-config.yaml` (per-project) with optional fallbacks at
`~/.agency-music/config.yaml` (user-global) and `$AGENCY_MUSIC_HOME/config.yaml`
(env override).
- **drivers.py** — music drivers — the five external I/O boundaries the music capability reaches
through, as Spec-002 ``Driver`` protocols (Option B: typed, named methods; the
uniform contract is the RETURN TYPE via the wrapping verb, not a ``dispatch(op)``).

Each driver is a marker ``Boundary`` exposing its own typed methods (the ``jules.py``
``create/get/list`` shape).
- **drivers_production.py** — music production drivers — Spec 115.

Real disk-writing + SQLite-backed implementations of the StateDriver +
DBDriver Protocols.
- **ontology.py** — music ontology — the consolidated ``OntologyExtension`` (nodes, enums,
edges, skills, schemas, templates) for the music capability.

Spec 094 (lifecycle child of 093) consolidates the ontology into its own
module so subsequent cluster children (095 lyrics, 096 audio, 097
catalogue, 098 promo, 099 research, 100 gates) extend it additively without
churning the cluster code module.

### `agency/capabilities/music/clusters/` (11 files)
- **__init__.py** — music clusters — per-cluster verb mixin modules (Spec 094 / Spec 286 P3).

The ``MusicCapability`` god-class splits into one mixin class per domain
cluster, composed into the single registered capability via multiple
inheritance (``_main.py``).
- **_base.py** — music clusters — shared base + module constants/helpers (Spec 286 Phase 3).

The per-cluster file split (Spec 094 design §"Module layout") relocates the
``MusicCapability`` god-class into cluster mixin classes, one per domain
cluster.
- **audio.py** — music audio cluster — mastering / mixing / QC / sheet-music / promo-video.

Spec 096 — 16 audio verbs + 2 composite gate verbs (measure · qc), plus the
007 audio verbs (master_album · analyze_mix · transcribe_sheet).
- **catalogue.py** — music catalogue cluster — DB tweets · streaming URLs · promo state.

Spec 097 — 11 catalogue verbs + 1 composite gate verb (tweet-schedule), plus
the 007 catalogue verbs (catalogue_status · verify_streaming).
- **cloud.py** — music cloud cluster — object-store publish via the CloudDriver.

``publish_asset`` (the CloudDriver banner verb from 007) — the generic
object-store publish entry point.
- **gates.py** — music gates cluster — cross-cutting computed gates + validation + health.

Spec 100 — 4 top-level verbs (validate_album · validate_sections · diagnose +
the 5 composite release/pre-gen gates) plus the 007 gates (pregen_check ·
release_check · music_health).
- **lifecycle.py** — music lifecycle cluster — ideas · albums · tracks · session (Spec 286 P3).

The lifecycle verbs (conceptualize · capture_idea · promote_idea · list_ideas ·
create_album · find_album · set_album_status* · create_track · list_tracks ·
set_track_status · rename_album · rename_track · album_progress ·
resume_session) relocate VERBATIM from ``_main.py`` into this mixin per Spec 094
design §"Module layout".
- **lyrics.py** — music lyrics cluster — text/prosody transforms + composite lyric gates.

Spec 095 — 13 transforms + the lyric composite gate verbs (prosody ·
pronunciation · repetition · explicit · name-exposure), plus the 007 text
verbs (count_syllables · lyric_report).
- **promo.py** — music promo cluster — promo copy · object-store publish · release package.

Spec 098 — 7 promo verbs + 1 composite gate verb (promo-review), plus the 007
promo verb (promo_copy).
- **research.py** — music research cluster — research scope · claims · verification.

Spec 099 — 8 research verbs + 1 composite gate verb (verify).
- **state.py** — music state cluster — album-status persistence + Spec-115 production binding.

``set_album_status`` (the StateDriver banner verb from 007) plus the Spec 115
production-binding verbs (get_config · load_override · get_reference ·
format_clipboard) that read config / reference / clipboard state.

### `agency/capabilities/music/migrations/` (2 files)
- **__init__.py** — music migrations — one-shot install / schema-migration ops.

Empty placeholder per Spec 094.
- **db_init.py** — Spec 097 — one-shot schema installer for the catalogue cluster's PostgreSQL backend.

Carries the bitwize ``schema.sql`` verbatim + the tweet table indexes that the
DBDriver methods (``create_tweet`` / ``list_tweets`` / ``search_tweets``) need
for sub-second response at scale.

### `agency/capabilities/novel/` (5 files)
- **__init__.py** — novel — long-form prose authoring capability (Spec 101 master).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module).
- **_main.py** — novel — minimum-viable-novel Slice 1 (Spec 101 master First-Principles Minimum).
- **_slug.py** — novel slug — single source of truth for the novel capability's slug shape.

Mirrors `agency/capabilities/music/_slug.py`.
- **config.py** — novel config — Spec 121 production-binding config layer.

Mirrors `agency/capabilities/music/config.py`: per-project
`.agency/novel-config.yaml`, global fallback, env override; mtime-cached
4-level resolution; minimal handrolled YAML parser when PyYAML missing;
`bootstrap()` writes default + creates content_root on first run.

Resolution order (first hit wins):
1.
- **drivers_production.py** — novel production drivers — Spec 121.

### `agency/capabilities/novel/clusters/` (11 files)
- **__init__.py** — novel.clusters — cluster mixins composed into the single NovelCapability.

Spec 286 P3 — the ~95-verb ``novel`` god-class split into one mixin per
SDLC/domain cluster.
- **_base.py** — novel.clusters._base — shared NovelCapability infrastructure (Spec 286 P3).

The production-driver auto-wiring (Spec 121) + NOT_FOUND guards extracted
verbatim from ``novel/_main.py`` into a base mixin every cluster mixin and
the composed ``NovelCapability`` inherit.
- **character_knowledge.py** — novel.character_knowledge — Character-knowledge cluster — knowledge ledger + anachronism audit + provenance (Spec 131).
- **codex.py** — novel.codex — Codex cluster — Novelcrafter-parity codex entries (Spec 132).
- **lifecycle.py** — novel.lifecycle — Lifecycle cluster — concept -> novel -> chapter -> scene -> render + idea/session (Spec 101/102).
- **manuscript.py** — novel.manuscript — Manuscript cluster — catalogue coherence, renderers, composite gates, FormatDriver export (Spec 106/107/108/124).
- **prose.py** — novel.prose — Prose cluster — driver-free prose analysis + editorial pipeline + craft gates (Spec 104/122).
- **research.py** — novel.research — Research cluster — claims + xcap research/prompt/thinking integration (Spec 105 + tight-integration).
- **storyform.py** — novel.storyform — Storyform cluster — Dramatica NCP decidable checks + coherence (Spec 103/120).
- **storytime.py** — novel.storytime — Story-time / narrative-time cluster — events, reveals, narrative beats (Spec 128).
- **world.py** — novel.world — World cluster — world sub-graph: cultures, religions, languages, magic, axioms (Spec 123).

### `agency/capabilities/panel/` (2 files)
- **__init__.py** — panel — multi-expert business analysis (Spec 294).
- **_main.py** — panel — multi-expert business analysis, first-class (Spec 294).

A native reimplementation of SuperClaude's Business Panel: nine strategic
thinkers, three interaction modes (discussion · debate · socratic), decidable
content-based mode selection.

### `agency/capabilities/persona/` (2 files)
- **__init__.py** — persona — specialist engineering personas, first-class (Spec 297).
- **_main.py** — persona — specialist engineering personas, first-class (Spec 297).

A native reimplementation of SuperClaude's specialist agents (architects,
engineers, analysts, mentors) as a built-in, dispatchable persona registry —
NOT ingested prompt files.

### `agency/capabilities/plugin/` (3 files)
- **__init__.py** — plugin — develop the agency Claude Code plugin from inside the engine.

Folder-form per Spec 060 §Phase 3.
- **_main.py** — The plugin-development capability — everything needed to develop a good plugin:

Plugin ports the plugin-development craft into compute: scaffolds, skill and command authoring, marketplace entries, and the lint rules that enforce the authoring doctrine.
- **_skills_client.py** — Spec 083 — the boundary to the Anthropic Skills API (`/v1/skills`).

Lazy, like `JulesClient`: needs the `anthropic` SDK (`pip install -e .[publish]`) +
`ANTHROPIC_API_KEY`, and raises a clear error AT CALL TIME when absent — so the
default never imports `anthropic` and `plugin.publish_skill(dry_run=True)` works
offline.

### `agency/capabilities/plugin/clusters/` (5 files)
- **__init__.py** — Cluster mixins for the `plugin` capability (Spec 286 P3).
- **authoring.py** — Authoring cluster — scaffolding + skill/command/marketplace/step-doc renders.

The pure template-render functions (no `self`, no `ctx`) live here as module
functions; `AuthoringMixin` carries the thin `@verb` wrappers.
- **lint.py** — Lint cluster — the authoring-doctrine rules as a polymorphic registry.

Spec 286 P3 OOP fix: the pre-split form spread each rule across THREE sites —
a ``_check_<rule>`` function, an entry in the ``_REMEDIATION`` dict, and a hand
wired call in ``lint_capability``.
- **publish.py** — Publish cluster — uploads a capability's Agent Skill to the Skills API.
- **reference.py** — Reference cluster — capability/verb reference lookup (the `help` map).

`help_map` is the pure renderer (no `self`, no `ctx`); `ReferenceMixin` carries
the thin `@verb`.

### `agency/capabilities/prompt/` (3 files)
- **__init__.py** — prompt — prompt-engineering capability (Spec 109).

Two-lineage capability:

1.
- **_main.py** — prompt — prompt-engineering substrate (Spec 109 · 129 · 304-306).

Author research dossiers, engineer token-budgeted prompts, route a draft to the
right one of 27 research-backed frameworks, and score prompts — and agency's own
functional docs — for clarity and anti-patterns.
- **ontology.py** — prompt ontology — Spec 109 consolidated OntologyExtension.

### `agency/capabilities/prompt/clusters/` (9 files)
- **__init__.py** — prompt.clusters — cluster mixins composed into the single PromptCapability.

Spec 286 P3 — the ~932-line ``prompt`` god-class split into one mixin per
section grouping.
- **_base.py** — prompt.clusters._base — shared PromptCapability infrastructure (Spec 286 P3).

The token-approximation primitive + clarity-scoring heuristic + the
doctrine-tunable budgets, extracted verbatim from ``prompt/_main.py`` into a
base module every cluster mixin imports.
- **_profiles.py** — prompt.clusters._profiles — goal-aware evaluation profiles (Spec 305/306).

``evaluate`` scores a prompt body against a criteria PROFILE selected by its
TARGET.
- **assembly.py** — prompt.assembly — Dynamic prompt assembly (Spec 127).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Walks the graph for a Scene (or Chapter) and composes a bounded prompt with
sourced provenance.
- **dossier.py** — prompt.dossier — Research-dossier lineage (Spec 109 Slice 1).
- **engineering.py** — prompt.engineering — Prompt-engineering lineage (Spec 109 Slice 1).
- **fragments.py** — prompt.fragments — Dramatica-as-prompt-fragments (Spec 129).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Each Dramatica ontology entry can carry a guidance fragment (second-person
agent imperative).
- **frameworks.py** — prompt.frameworks — the 27-framework library, first-class (Spec 304).

prompt-architect (ckelsoe, MIT) ships 27 research-backed prompt-engineering
frameworks across 7 intent categories.
- **gates.py** — prompt.gates — composite gate verbs (Spec 109 Slice 1).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

The 2 composite gate verbs called by walkable skills: token_budget_gate +
audit_gate.

### `agency/capabilities/recommend/` (2 files)
- **__init__.py** — recommend — request → capability routing, first-class (Spec 298).
- **_main.py** — recommend — request → capability routing, first-class (Spec 298).

A native reimplementation of SuperClaude's `sc-recommend`: given a free-text
request, recommend the most suitable agency capability + verb to use.

### `agency/capabilities/reflect/` (2 files)
- **__init__.py** — reflect — durable, scope-tagged cross-session memory.

Folder-form per Spec 060 §Phase 3 — promoted from `reflect.py` so the
capability can ship its own `templates/` + `schemas/`.
- **_main.py** — reflect — durable, scope-tagged cross-session memory.

### `agency/capabilities/research/` (7 files)
- **__init__.py** — research — graph-native lead + specialists + verifier (Spec 044).

Folder-form capability.
- **_findings.py** — Helper utilities reused across research lead / specialist / verify.
- **_lead.py** — research.lead — scope the question + plan specialists.

Pure planner.
- **_main.py** — research — lead + specialists + verifier (Spec 044).
- **_specialist.py** — research.specialist — one bounded sub-search per role.

Three roles ship in v1:
  codebase         — grep + AST walk over the repo (confidence 1.0)
  prior-reflections — reflect.recall_semantic (confidence = score)
  doc-corpus       — keyword + semantic match over docs/ (confidence = score)

The `web` role is reserved (Spec 044 line 102) but defers to v2 when
the WebSearchClient injector is non-None.
- **_verify.py** — research.verify — adversarial citation check.
- **_web.py** — Web-search boundary driver (Spec 044 + Spec 052).

Two shipped backends:
  DuckDuckGoClient — zero-config default.

### `agency/capabilities/select/` (2 files)
- **__init__.py** — select — complexity-scored approach selection (Spec 296).
- **_main.py** — select — complexity-scored approach selection, first-class (Spec 296).

A native, generalized reimplementation of SuperClaude's `sc-select-tool`: score
an operation's complexity and route it to the right approach archetype —
`semantic` (structure-aware, accurate), `pattern` (fast bulk edits), or `native`
(safe default).

### `agency/capabilities/shell/` (2 files)
- **__init__.py** — shell — a token-efficient, recorded, templated host-command boundary (Spec 073).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4.
- **_main.py** — shell — a token-efficient, recorded, templated host-command boundary (Spec 073).

### `agency/capabilities/skill_generator/` (2 files)
- **__init__.py** — skill_generator — generate a deploy-ready skill in one call.
- **_main.py** — skill_generator — generate a deploy-ready skill in one call.

### `agency/capabilities/skills/` (2 files)
- **__init__.py** — skills — the first-class registry over every capability's walkable skills (Spec 026).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4.
- **_main.py** — skills — the first-class registry over every capability's walkable skills (Spec 026).

### `agency/capabilities/subagent/` (2 files)
- **__init__.py** — subagent — subagent-driven-development as a composition.
- **_main.py** — subagent — subagent-driven-development as a composition.

### `agency/capabilities/symbols/` (2 files)
- **__init__.py** — symbols — token-efficient symbol compression (Spec 300).
- **_main.py** — symbols — token-efficient symbol compression, first-class (Spec 300).

### `agency/capabilities/thinking/` (2 files)
- **__init__.py** — thinking — critical-thinking capability (Spec 110).

Eight founding methods + new ones for adversarial review (red-team) and
recursive questioning (socratic).
- **_main.py** — thinking — critical-thinking capability (Spec 110 Slice 1).

10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite
(apply_full_review) + 1 walkable skill (critical-thinking).

Each method is a transform: returns a structured scaffold the agent fills
out.

### `agency/capabilities/workspace/` (2 files)
- **__init__.py** — workspace — isolate work in a git worktree + record a green baseline.
- **_main.py** — workspace — isolate work in a git worktree + record a green baseline.

### `agency/render/` (1 files)
- **__init__.py** — Spec 032 §H — engine-owned template files.

### `docs/examples/` (2 files)
- **author_a_plugin.py** — Example: author a tiny Claude Code plugin with the agency engine.

Walks the `plugin-dev` skill one phase at a time (progressive disclosure).
- **pressure_test_a_skill.py** — Example: pressure-test a discipline skill (Spec 011, dry-run walk).

Subagent pressure-tests ask whether a discipline skill actually changes a fresh
agent's behaviour under pressure — or whether the agent rationalises it away.

### `examples/` (3 files)
- **__init__.py** — Example out-of-tree extensions for the agency engine.

These are NOT part of the core plugin.
- **music.py** — DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music graduated from ``examples/`` into ``agency/capabilities/music/`` as a
first-class folder-form capability.
- **music_drivers.py** — DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music drivers graduated from ``examples/music_drivers.py`` into
``agency/capabilities/music/drivers.py`` as part of the Spec 094
migration.

### `scripts/` (11 files)
- **__init__.py** — Helper scripts (Spec 054 drift-management, Spec 149 derived-doc discipline,
Spec 053 test-suite slicing).
- **check_architecture.py** — Spec 157 Slice 1 — typed ArchitectureReport + wire-verb invariant audit.

Spec 019 commits to EXACTLY three wire verbs at the engine boundary
(`search` / `get_schema` / `execute`); every capability verb is reached
THROUGH them, never alongside.
- **check_codes_coverage.py** — Spec 151 — Codes-coverage CLI shim.

The audit core moved to :mod:`agency._codes_coverage` (Spec 151 Slice 3) so
the engine can import it without the dev-only ``scripts/`` tree.
- **check_collect_callers.py** — Spec 159 Slice 1 — derived audit of `dogfood.collect` callers.

Spec 150 closed the dogfood-loop pipeline (Slices 1+2: parse_amendment +
apply_amendment shipped).
- **check_response_prefix.py** — Spec 146 Slice 2 — `_check_response_prefix` AST lint rule.

Spec 146 Slice 1 shipped the typed `ResponseEnvelope(prefix, body)` split
+ `agency_welcome` wired through it.
- **check_scaffold_markers.py** — Spec 158 Slice 1 — capability scaffold-marker presence audit.

Walks `agency/capabilities/*` and reports which capabilities carry the
`# agency-scaffold: v1` marker on their main file.
- **check_schema_coverage.py** — Spec 153 — schema-coverage CLI shim.

The audit core moved to :mod:`agency._schema_coverage` (Spec 153 Slice 3)
so the engine can import it without the dev-only ``scripts/`` tree.
- **check_vision_goals.py** — Spec 149 Slice 1 — `vision_goals:` frontmatter validator.

The drift-derivation chain anchor (`Plan/_planning/charter.md`) wants every spec
to declare its Vision-goal mapping in frontmatter so the alignment matrix
(Spec 191), per-spec Followup (Spec 269), and closing audit (Spec 261) can
all derive from one source.
- **derive_docs.py** — Spec 149 Slice 2 — `derive-docs` core derivation library.

Spec 149 Slice 1 shipped the `vision_goals:` frontmatter validator + 129-
spec baseline.
- **gen-living-spec.py** — Phase B — generate a capability-indexed *living spec* from the REFACTORED code.

Rule 2 applied to specs: the spec's generated sections (Verbs / Ontology /
Skills) are DERIVED from the live registry, never hand-maintained — re-run to
refresh.
- **mcp_wire_smoke.py** — Drive the agency MCP server over stdio with raw JSON-RPC.

### `tests/` (13 files)
- **conftest.py** — Spec 016 v2 Phase 5 — shared engine/iid fixtures.

Eliminates the 13 duplicate fixture blocks the test suite carried
(claim verified verbatim by survey a7e6bd1) and removes a latent bug:
the legacy duplicates used `tempfile.mktemp(suffix=".db")` which is
deprecated since Python 2 (race condition — the predicted path isn't
guaranteed unique).
- **test_analyze_subprocess_analyzer.py** — Spec 286 — the shared SubprocessAnalyzer template scaffold.
- **test_develop_plan_execute.py** — Spec 287 — develop `plan-execute` discipline + Plan/PlanStep provenance.

A first-class plan-authoring → execution-with-checkpoints discipline
(superpowers writing-plans + executing-plans + subagent-driven-development;
superclaude sc-workflow + sc-task).
- **test_durable_writes.py** — Spec 282 Workstream C — durable batch writes.

Evidence (kohaerenzprotokoll): 97 NarrativeBeat nodes, only 12 PRECEDES edges.
Two distinct engine-side defects this guards against:

1.
- **test_entities.py** — Spec 289 Slice 1 — SQLModel entity models derived from the graph ontology.
- **test_entity_store.py** — Spec 289 Slice 2 — the canonical SQLite-backed entity store.
- **test_entity_store_mirror.py** — Spec 289 Slice 2b — Memory mirrors authoritative graph writes into the
graph-authoritative typed projection (EntityStore).

The invariant: the graph node stays write-authoritative; the entity row is a
ONE-WAY derived mirror keyed by node id.
- **test_error_severity.py** — Spec 282 — error severity taxonomy.

Replays the exact failure scenarios mined from
``kohaerenzprotokoll/.agency/session.db`` (1952 invocations, 626 failed):
``create_scene`` rejected 513× on a closed ``pov`` enum (PERMANENT — never
succeeds) versus the known ``Failed to set property 'vfrom' on edge N``
contention (TRANSIENT — retry helps).
- **test_host_bridge.py** — Spec 285 Slice 1 — HostBridge seam (sampling + elicitation boundary).
- **test_novel_storyform_node.py** — Spec 103 Slice 2 (Workstream D) — create_storyform / get_storyform.

Closes the documented ENGINE GAP: the storyform gates + checks read a
`Storyform` node, but no verb minted one.
- **test_projected_enum.py** — Spec 284 — projected-enum substrate.
- **test_render_driver_substrate.py** — Spec 283 Slice 1 (Workstream F) — capability render substrate.
- **test_skill_walk_part_b.py** — Spec 285 Slice 1 Part B — walk-level sampling + enforced assumption-gate.

### `tests/acceptance/` (69 files)
- **conftest.py** — Shared fixtures + helpers for the Gherkin acceptance suite.

Phase C — the flat `tests/test_*.py` are converted into behaviour scenarios
here (owner directive).
- **test_acceptance.py** — Acceptance — core engine behaviours: the code-mode wire contract, provenance
(the moat), and the capability surface.
- **test_analyze.py** — Acceptance — analyze capability (Spec 042, Spec 048, Spec 084).

Converted from: tests/test_analyze_graph.py, tests/test_analyze_capability.py,
tests/test_analyze_quality.py, tests/test_analyze_security.py,
tests/test_analyze_performance.py, tests/test_analyze_architecture.py,
tests/test_analyze_deps_integration.py.

Dropped (implementation / structural — not observable behaviour):
  - test_analyze_capability.test_capability_registered — registry membership is
    structural, not behaviour; the invoke paths already fail loudly if missing.
  - test_analyze_capability.test_capability_has_six_verbs — verb-set count is
    an implementation snapshot; new verbs should not require test update.
  - test_analyze_capability.test_ontology_declares_finding_severity_enum — enum
    shape is implementation; behaviour is that findings carry valid severities
    (tested via the finding-shape scenario).
  - test_analyze_capability.test_ontology_declares_analysis_axis_enum — same.
  - test_analyze_capability.test_code_analysis_skill_registered — skill phase
    names / gate flags are structural; behaviour is that the skill is walkable.
  - test_analyze_axis_registry.* (all 9 tests) — the axis-prefix registry is a
    private implementation detail (_build_axis_registry, _rule_axis, AXIS_PREFIXES);
    its observable effect is that rules land on the right axis in analyze.run
    output, which is covered by the run/quality/security/performance scenarios.
  - test_analyze_deps_integration.test_ruff_silent_when_missing — monkeypatches
    shutil.which; tests internal degradation logic, not observable output.
  - test_analyze_deps_integration.test_ruff_finds_long_line_when_present — skipped
    in CI if ruff absent; covered by quality scanner scenarios when ruff is present.
  - test_analyze_deps_integration.test_ruff_finds_unused_import_when_present —
    same rationale.
  - test_analyze_deps_integration.test_bandit_silent_when_missing — monkeypatch.
  - test_analyze_deps_integration.test_bandit_finds_eval_when_present — skip guard.
  - test_analyze_deps_integration.test_radon_* — skip guard + internal API.
  - test_analyze_deps_integration.test_quality_scan_composes_internal_plus_external —
    tool-presence conditional; not reliably testable as acceptance scenario.
  - test_analyze_deps_integration.test_quality_scan_silent_external_fallback —
    monkeypatches shutil.which.
  - test_analyze_performance.test_unbounded_while_true_flagged — P003 is an
    internal rule; the scenario is incomplete (no severity assertion needed for
    acceptance).
- **test_branch.py** — Acceptance — branch capability (Spec 046).

Converted from tests/test_branch*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- _infer_commit_type and _infer_scope private function internals
- The VCS client itself (real subprocess boundary)

GAPS: branch.assess and branch.finish with a REAL git repository are external
effects.
- **test_codes_coverage.py** — Acceptance — codes-coverage audit behaviour (Spec 151).

Grounds the Slice 2 gate that `.github/workflows/test.yml` runs (`--baseline
--strict`).
- **test_config.py** — Acceptance — unified config resolver + registry (Spec 328 Slice 1).

Behaviour: a registered key resolves env > file > default; config_set persists;
registered sections appear in the live set.
- **test_config_doctor.py** — Acceptance — unified config doctor (Spec 328 Slice 4).
- **test_config_wiring.py** — Acceptance — unified config wiring (Spec 328 Slice 3).

The three zero-manual-step generation points: `agency install` (here:
`install.scaffold_agency_dir`) creates the annotated config; the SessionStart
hook REPAIRS an existing one non-destructively but never creates one in an
arbitrary cwd.
- **test_context_neighbors.py** — Acceptance — CapabilityContext.neighbors() one-hop edge traversal (Spec 125).

Converted from tests/test_context_neighbors.py.
- **test_delegate.py** — Acceptance — delegate capability (Spec 040/041).
- **test_develop.py** — Acceptance — develop capability: scaffolding, linting, authoring discipline
walk, discipline cues for intent methods.
- **test_develop_maintain.py** — Acceptance — develop.maintain: the autolearning recurring-maintenance loop.
- **test_discover.py** — Acceptance — discover capability scaffold (Spec 308).

Behaviour: the drop-in shell is discoverable, registers the locked Spec 307
ontology surface, reuses research's Citation, and derives its Agent Skill —
all from adding one folder.
- **test_discover_acceptance.py** — Acceptance — discover.acceptance, Gherkin criteria derivation (Spec 317).
- **test_discover_ask.py** — Acceptance — discover.ask, the well-formed AskUser primitive (Spec 310).
- **test_discover_clarify.py** — Acceptance — discover.clarify, the ambiguity-resolution loop (Spec 311).
- **test_discover_clarity.py** — Acceptance — discover.clarity, the Intent readiness score (Spec 322).
- **test_discover_interview.py** — Acceptance — discover.interview, the adaptive elicitation engine (Spec 309).
- **test_discover_scope.py** — Acceptance — discover.scope, in/out boundary elicitation (Spec 318).
- **test_dispatch_decision_extended.py** — Acceptance — extended dispatch_decision signals S1, S6, S7, S8 (Spec 040).

Converted from tests/test_dispatch_decision_extended.py (behaviour: the new
seven signals and the full eleven-signal payload).
- **test_doctrine.py** — Acceptance — doctrine capability: queryable principles + rules (Spec 303).
- **test_document.py** — Acceptance — document capability (Spec 043, Spec 056).

Converted from: tests/test_document_render.py, tests/test_document_index_repo.py,
tests/test_document_explain.py, tests/test_document_scope_guards.py.

Dropped (implementation / structural — not observable behaviour):
  - test_document_render.test_render_reflections_text_truncated_to_500 —
    pinned to exactly 500 chars (magic number snapshot); converted to the
    invariant "content does not contain 600 consecutive identical characters".
  - test_document_scope_guards.test_lint_table_covers_root_intent_id — tests the
    internal `_check_node_id_guards` linter (a private plugin function that
    inspects capability definitions); not observable behaviour through the wire.
  - test_document_scope_guards.test_paths_scan_rejects_non_intent_root — tests
    internal _paths.scan directly; observable only via analyze.run behaviour
    (covered in analyze acceptance).
- **test_dogfood.py** — Acceptance — dogfood capability: graph-native ledgers, export/import,
amendment pipeline.
- **test_engine.py** — Acceptance — engine substrate: monitor, wire unwrap, lifespan, typed shapes,
ToolResult, branch.commit_smart, develop.estimate (Spec 012/019/021/046/059/171/175/176).

Converted from: test_engine_lifespan, test_engine_monitor, test_engine_unwrap_contract,
test_engine_brief_descriptions, test_micro_extensions_046, test_toolresult_convenience,
test_typed_shapes_wave1, test_typed_shapes_wave1_part2, test_typed_shapes_wave3.

Dropped (implementation / structural / not observable behaviour):
- test_monitor_event_json_roundtrip: already covered as "MonitorEvent serializes"
  in this suite.
- test_emit_autofills_ts_when_zero: internal timestamp auto-fill; not a wire
  behaviour.
- test_atomic_budget_holds_after_json_escaping: internal byte-counting of the
  POSIX write guarantee; covered by the "truncates to 4096 bytes" scenario.
- test_resolve_path_sibling_of_db: internal path resolution; covered by "prefer
  explicit then env" scenario.
- test_engine_owns_monitor / test_capability_context_emit_monitor_autofills /
  test_emit_monitor_noop_without_engine: internal wiring; the observable
  behaviour (events appear in the log file) is covered.
- All typed-shape FIELD / attribute introspection tests (wave1 / wave1_part2 /
  wave3): typed-shape construction invariants are implementation detail of the
  dataclass validators; we keep only the construction-rejection (ValueError)
  behaviours since those are observable contracts.
- test_guard_typed_shape / test_capability_row_typed_shape / etc.
- **test_frugal.py** — Acceptance — frugal core discipline level + render (Spec 326 Slice 1).
- **test_frugal_floor.py** — Acceptance — frugal safety-floor gate (Spec 326 Slice 4).

`_frugal.safety_floor_intact()` is a decidable predicate: at every level but off
the FULL render carries every safety-floor marker and the COMPACT render names
the floor.
- **test_frugal_stamp.py** — Acceptance — frugal M2 per-verb envelope stamp (Spec 326 Slice 2).

Every capability verb's wire return carries a byte-stable compact frugal stamp
(via engine._shape_wire_result); off omits it; agency_welcome carries it in its
cache-stable prefix.
- **test_gate.py** — Acceptance — gate capability + gate predicates (Spec 011).
- **test_hooks.py** — Acceptance — hook dispatch, BoundaryUse, foreign-hook install (Spec 076 / 195 / 280).
- **test_implicit_intent.py** — Acceptance — implicit intent_id via AGENCY_INTENT env var (Spec 018 Win 3).

Converted from tests/test_implicit_intent.py.
- **test_install.py** — Acceptance — install pipeline (Spec 029/031/032/062/064/065/092).
- **test_installer.py** — Acceptance — multi-agent self-installer (Spec 327).

surface_card → per-agent adapters (compact projection: frugal discipline + entry
pointers, NOT the full verb index); idempotent fenced-block merge; per-adapter
report; uninstall removes only the block.
- **test_intent.py** — Acceptance — intent capability: critical-thinking methods, chaining,
owners, path analysis, and skill projection.
- **test_jules.py** — Acceptance — jules capability.

Converted from tests/test_jules*.py (~17 files).
- **test_loop_events.py** — Acceptance — loop detection middleware and typed LoopEvent (Spec 011 / 156).
- **test_manage.py** — Acceptance — manage capability: generic CRUD (Spec 293).
- **test_mode.py** — Acceptance — mode capability (Spec 295).
- **test_music.py** — Acceptance — music capability (all clusters).

Converted from tests/test_music*.py (~11 files).
- **test_novel.py** — Acceptance — novel capability (Gherkin conversion).

Converted from tests/test_novel_capability.py, test_novel_lifecycle.py,
test_novel_lifecycle_slice2.py, test_novel_prose.py, test_novel_prose_slice2.py,
test_novel_manuscript.py, test_novel_research.py, test_novel_storyform.py,
test_novel_storyform_slice2.py, test_novel_storyform_completion.py,
test_novel_ncp_validation.py, test_novel_worldbuilding.py, test_novel_codex.py,
test_novel_character_knowledge.py, test_novel_story_time.py,
test_novel_gates_slice2.py, test_novel_editorial_pipeline.py,
test_novel_e2e.py, test_novel_integration_xcap.py,
test_novel_walkable_skills.py.

DROPPED (not behaviour — implementation / structural):
 - test_novel_capability_registers_five_mvn_verbs — verifies internal verb
   registry set; structural invariant, not observable behaviour.
 - test_novel_capability_lint_clean — internal lint check on docstring shape.
 - test_novel_capability_ships_bitwize_templates_plus_documented_extensions —
   enumerates a frozen template-name set; structural.
 - test_dramatica_ontology_vendored_with_304_entries — file-content count,
   structural vendoring check.
 - test_decidability_matrix_doc_vendored — file existence/content, structural.
 - test_novel_concept_schema_satisfied_by_skill_phases — schema/skill alignment
   check against internal data structures.
 - test_novel_concept_skill_terminates_in_hard_gate — verifies internal skill
   shape; checked indirectly via walk behaviour.
 - test_novel_concept_skill_walks_through_confirmation — drives SkillRun
   internals directly (not via invoke); implementation.
 - test_novel_concept_skill_extended_to_ten_phases — frozen phase count.
 - test_novel_concept_skill_walks_through_all_ten_phases — SkillRun internals.
 - test_novel_status_enum_bites / test_idea_status_enum_bites — raw
   Memory.record enum enforcement; tests internal schema guard, not cap verbs.
 - test_novel_claim_status_enum_bites — same.
 - test_idea_node_declared_with_status_enum / test_promoted_to_edge_declared /
   test_storyform_node_declared / test_known_fact_node_declared /
   test_knows_and_learned_in_edges_registered / test_story_time_event_node_declared /
   test_narrative_beat_node_declared / test_new_edges_registered /
   test_codex_entry_node_declared / test_codex_kind_enum_present /
   test_codex_of_edge_registered / test_scene_node_declared_with_pov_enum /
   test_scene_of_edge_declared / test_world_nodes_declared /
   test_world_axiom_severity_enum / test_part_of_world_edge_registered /
   test_novel_claim_node_declared — ontology registration assertions on
   internal data structures, not observable verb behaviour.
 - test_novel_capability_registers_* (multiple registration tests) — internal
   registry set membership; structural.
 - test_twelve_ncp_fixtures_ported_verbatim / test_fixtures_byte_identical_to_upstream —
   file-identity / vendoring audit; structural.
 - test_check_throughline_partition_does_not_fail_other_broken_fixtures /
   test_check_slot_fill_does_not_fail_other_broken_fixtures /
   test_check_storybeat_moment_refs_does_not_fail_other_broken_fixtures —
   test matrix correctness of other fixtures; structural.
 - test_check_report_shape_is_low_token — token budget proxy on JSON length;
   implementation concern.
 - test_validate_appreciations_canonical_set_size_463 /
   test_validate_narrative_functions_canonical_set_size_144 — frozen count
   snapshots against vendored data.
 - test_resolve_term_module_helper_exists / test_resolve_term_* — private
   module helper; implementation detail.
 - test_storyform_build_skill_registered / test_character_architect_* /
   test_world_bible_architect_* / test_scene_bridge_auditor_* /
   test_three_new_skills_registered — skill-shape / phase-count assertions
   on internal ontology structures.
 - test_compose_world_rules_injects_matched_codex / test_compose_pov_card_* /
   test_assemble_scene_brief_continuity_* — tests internal prompt.assemble_scene_brief
   via a different cap; xcap prompt tests belong in prompt acceptance suite.
 - test_developmental_editor_phases_bind_to_gate /
   test_line_editor_phases_bind_to_gate — verify internal skill phase index
   bindings; structural.
 - test_skills_registered (editorial_pipeline) — internal registry membership.
 - All test_novel_production.py tests — test FileNovelStateDriver disk I/O and
   monkeypatching; driver implementation detail, not observable verb behaviour.
 - All test_novel_format_driver.py tests — test FormatDriver disk I/O / fake
   drivers / file paths; driver implementation, requires monkeypatching.
 - test_novel_prose_wet.py tests — require monkeypatched AnthropicDriver /
   Completion stub; driver binding, not observable behaviour of the engine.
 - test_novel_scene_writer_skill.py — SkillRun walker internals.
 - test_novel_xcap_dogfood_analyze.py — internal xcap routing analysis,
   not observable behaviour.

GAPS:
 - publication_gate (requires FormatDriver disk writes) — needs production
   engine monkeypatching.
- **test_output_overflow.py** — Acceptance — output overflow capture and recall (Spec 154 Slice 1).

Converted from tests/test_output_overflow.py.
- **test_panel.py** — Acceptance — panel capability (Spec 294).
- **test_persona.py** — Acceptance — persona capability (Spec 297).
- **test_plugin_authoring.py** — Acceptance — plugin authoring behaviour.
- **test_prompt.py** — Acceptance — prompt capability (Spec 109/127/129).
- **test_recommend.py** — Acceptance — recommend capability (Spec 298).
- **test_reflect.py** — Acceptance — reflect (semantic recall).
- **test_reload.py** — Acceptance — agency_reload: mid-session capability reload (Spec 302 Slice 2).
- **test_render_substrate.py** — Acceptance — render substrate and response envelope (Spec 023 / 146 / 154).
- **test_research.py** — Acceptance — research capability (Spec 044, Spec 052, Spec 126, Spec 168).

Converted from: tests/test_research_capability.py, tests/test_research_verify.py,
tests/test_research_ingest_gdoc.py, tests/test_research_web.py,
tests/test_research_citation.py.

Dropped (implementation / structural — not observable behaviour):
  - test_research_capability.test_capability_registered — registry membership
    structural; loud failure on invoke covers it.
  - test_research_capability.test_capability_has_verbs — verb-set snapshot;
    new verbs should not force test update.
  - test_research_capability.test_ontology_research_status_enum — internal enum
    shape; observable effect is the status value returned by lead (tested).
  - test_research_capability.test_ontology_citation_source_kind_enum — same.
  - test_research_capability.test_ontology_verification_status_enum — same.
  - test_research_capability.test_deep_research_skill_registered — phase names /
    gate flags are structural; walkability is the behaviour.
  - test_research_capability.test_engine_accepts_web_search_kwarg — covered by
    "engine web_search kwarg overrides the default" scenario.
  - test_research_web.test_ddg_client_parses_related_topics — monkeypatches
    httpx; tests internal DDG client parsing logic, not the observable
    research verb surface.
  - test_research_web.test_ddg_client_returns_empty_on_failure — monkeypatches
    httpx.Client; internal degradation, not observable behaviour.
  - test_research_web.test_ddg_client_respects_k_limit — monkeypatches httpx.
  - test_research_web.test_resolve_defaults_to_duckduckgo — monkeypatches env;
    the observable fact (engine default is duckduckgo) is covered.
  - test_research_web.test_resolve_explicit_duckduckgo — env monkeypatch.
  - test_research_web.test_resolve_unknown_falls_back_silently — env monkeypatch.
  - test_research_web.test_reachability_check_passes_on_2xx — monkeypatches httpx
    (network mock); not observable from the wire surface.
  - test_research_web.test_reachability_check_fails_on_4xx — monkeypatches httpx.
  - test_research_web.test_reachability_check_fails_on_network_error — monkeypatch.
  - test_research_citation.test_citation_typed_shape — internal dataclass shape.
  - test_research_citation.test_citation_rejects_empty_url — internal validation.
  - test_research_citation.test_citation_rejects_invalid_backend — internal enum.
  - test_research_citation.test_citation_rejects_empty_hash — internal validation.
  - test_research_citation.test_compute_citation_hash_is_deterministic — partially
    converted (observable: hash length = 16 chars is now an invariant check).
  - test_research_citation.test_backend_set_equals_documented — internal Literal
    annotation shape; kept as "backend set" but converted to behavioural.
  - test_research_ingest_gdoc.test_ingest_gdoc_verbs_registered — structural.
  - test_research_ingest_gdoc.test_dispatch_contract_callback_kwargs — internal
    callback shape; observable via the verb's returned dict (tested).

GAPS (network-dependent — cannot run reliably in acceptance suite):
  - web-reachability check with real HTTP HEAD calls (2xx / 4xx / timeout).
    The underlying behaviour is: verify raises "web-reachability" check in the
    payload (tested via the vacuous-pass scenario with no web citations, and
    the three-check payload scenario).
- **test_search_isomorphism.py** — Acceptance — MCP/CLI search isomorphism (Spec 023 §F3.1).

Converted from tests/test_search_isomorphism.py.
- **test_select.py** — Acceptance — select capability (Spec 296).
- **test_session_driver.py** — Acceptance — session driver verbs (Spec 114).

Converted from tests/test_session_driver.py.
- **test_shell.py** — Acceptance — shell capability (Spec 073/075).
- **test_skill_generator.py** — Acceptance — skill_generator capability: author + lint a SKILL.md (Spec 028).
- **test_skill_phase_parse.py** — Acceptance — Skill/Phase parse boundary behaviour.

Converted from:
  tests/test_skill_phase_parse.py  (Spec 152 — typed parse_skill / parse_phase)

Dropped as implementation/structural (not observable behaviour):
  test_skill_walk_slices.py — render_phase / render_verb output format tests
    (T1/T2/T3 depth slices, snippet call_tool syntax, fallback text) are
    internal disclosure-helper details.
- **test_skill_walk.py** — Acceptance — skill walk behaviour.
- **test_skills_registry.py** — Acceptance — skills registry behaviour.

Converted from:
  tests/test_skills_index.py        (Spec 026 — skills.index graph promotion)
  tests/test_skill_first_discovery.py (Spec 025 — skill tag wiring on verbs)
  tests/test_skills_matcher_result.py (Spec 162 — MatcherResult typed shape)

Dropped as implementation/structural (not observable behaviour):
  test_skills_api_binding.py — verifies the Anthropic Python SDK signature;
    depends on [publish] extra that CI doesn't install.
- **test_subagent.py** — Acceptance — subagent capability (Spec 041).
- **test_surface_resolution.py** — Acceptance — surface resolution (Spec 023 §F3.2).

Converted from tests/test_surface_resolution.py.
- **test_symbols.py** — Acceptance — symbols capability (Spec 300).
- **test_template_schema.py** — Acceptance — template and schema bootstrap/lint/coverage behaviour.

Converted from:
  tests/test_template_bootstrap_wireup.py (Spec 060 Phase 1 — bootstrap wire-up)
  tests/test_template_folder_lint.py      (Spec 060 Phase 4 — lint rule)
  tests/test_template_schema_coverage.py  (Spec 153 — coverage audit)

Dropped as implementation/structural (not observable behaviour):
  test_path_safety.py — exercises an internal helper `_safe_path` that
    validates path-traversal guards inside the template loader.
- **test_thinking.py** — Acceptance — thinking capability: critical-thinking method scaffolds (Spec 110).
- **test_token_budget.py** — Acceptance — token budget (Spec 023 / 082).
- **test_typed_entities.py** — Acceptance — Spec 327: typed Intent + Capability core (the four-concept
interweave's load-bearing slice).
- **test_typed_fulfilment.py** — Acceptance — Spec 328: typed Intent fulfilment (the Intent-owned Gate +
AcceptanceCriterion).
- **test_typed_read_api.py** — Acceptance — Spec 330: the typed Intent read API (IntentStore) + parity gate.
- **test_typed_spine.py** — Acceptance — Spec 329: typed Lifecycle state + the Memory provenance spine.
- **test_welcome.py** — Acceptance — agency_welcome (Spec 029 / 030).
- **test_workspace.py** — Acceptance — workspace capability (Spec 002).

Converted from tests/test_workspace*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- VCS client internals (subprocess boundary)

GAPS: real git worktree creation requires a live git repository.
