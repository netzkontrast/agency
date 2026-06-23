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

**Capabilities:** `adr/`, `analyze/`, `branch/`, `clusters/`, `config/`, `delegate/`, `develop/`, `discover/`, `doctrine/`, `document/`, `dogfood/`, `frugal/`, `gate/`, `intent/`, `jules/`, `loop/`, `manage/`, `migrations/`, `mode/`, `music/`, `novel/`, `panel/`, `persona/`, `plugin/`, `prompt/`, `recommend/`, `reflect/`, `research/`, `select/`, `shell/`, `skill_generator/`, `skills/`, `subagent/`, `symbols/`, `thinking/`, `toolcalls/`, `workflow/`, `workspace/`

### `./` (1 files)
- **conftest.py** (3 symbols)

### `Plan/_research/novel-mvp-source/legacy-skills/dramatica-theory/scripts/` (1 files)
- **split_book.py** — Split the Dramatica book Markdown into thematic reference chunks.

Reads /home/claude/dramatica.md (output of pdf-to-markdown skill against
the source PDF) and writes 9 chunk files into ./references/.

Each chunk gets a written preamble describing what's in it and where it
sits in the source — so the SKILL.md can reference chunks by topic
without preloading them.

Boundaries are line-numbers verified against the source by inspecting
the headings. (6 symbols)

### `agency/` (73 files)
- **__init__.py** — agency — an installable Claude Code plugin: the v4 core on the real substrate.

Four concepts (Intent, Capability, Lifecycle, Memory) + a FastMCP engine, over a
real GraphQLite bi-temporal graph. (4 symbols)
- **__main__.py** — `python -m agency` — start the Agency MCP server (stdio).

Three console-script entry points (Spec 039):
  `agency`        — CLI for bash callers (see ``agency.cli:main``).
  `agency-mcp`    — MCP server entry; this module's :func:`main`.
  `agency-doctor` — bare-CLI health check; this module's
                    :func:`doctor_main`. (12 symbols)
- **_capability_loader.py** — Spec 032 §B — capability folder loader. (13 symbols)
- **_capture.py** — Capture-full helper — the no-truncate policy (user directive 2026-06-19).

Captured DATA — tool calls (pre/post), command output, stored provenance text —
is NEVER silently truncated: a dropped tail makes the record LIE about what
actually happened, which is worse than a larger record. (6 symbols)
- **_checks.py** — Spec 011 — structural Lifecycle checks (the auditable residue of a run).

A Lifecycle `check` is the post-hoc read over whatever a delegation/subagent
produced — same observe family as `COMPLETED ≠ done`/`verify` (CORE.md:31,33-35),
NOT a new capability's act. (4 symbols)
- **_clarity.py** — Intent clarity — the substrate readiness signals + score (Spec 307 §Refinement).

The clarity score is the home of the "is this intent clear enough to confirm?"
question. (5 symbols)
- **_codes_coverage.py** — Spec 151 — ToolResult Codes coverage audit (engine-side core).

Moved out of ``scripts/check_codes_coverage.py`` (Spec 151 Slice 3) so the
engine — ``agency_doctor`` — can import the audit WITHOUT depending on the
dev-only ``scripts/`` tree (the wheel packages only ``agency``; importing
``scripts.*`` at runtime would crash the installed plugin). (22 symbols)
- **_config.py** — Unified ``.agency/config.yaml`` — Spec 334 Slice 1 (resolver + registry).

A single home for all agency config. (29 symbols)
- **_coverage_gate.py** — Spec 169 Slice 1 — typed GateResult + pure evaluate() for the CI gate.

The CI gate has three concerns: coverage trend (non-decreasing per
capability), flake count (zero tolerance), and verb-test coverage (every
verb has a test). (9 symbols)
- **_db_path.py** — DB path resolution per Spec 020 — central .agency/session.db.

Resolution order (Spec 020 Done When item):
  1. (3 symbols)
- **_doctor_shapes.py** — Spec 170 Slice 1 — typed Field/Section/Report shapes for `agency_doctor`.

The doctor surface today is an ad-hoc dict with per-section dict bodies.
Spec 170 lifts it to a typed contract so every section has the same
shape + the invariants are enforced at construction:

  ready=False ⇒ hint is non-empty (pipx-HINT pattern, Spec 065 generalised)
  source ∈ {env, extra, graph, registry}  (where the value comes from)

Slice 1 ships the shapes + invariants offline-clean. (12 symbols)
- **_embedder_handle.py** — Spec 181 Slice 1 — typed EmbedderHandle for the reflect-embedder upgrade. (7 symbols)
- **_enhancement_stubs.py** — Wave 3-12 enhancement Slice 1 catalogue — typed stubs for every drafted spec.

Each EnhancementSliceStub records the Slice 1 commitment: the spec_id +
slug + wave. (10 symbols)
- **_entities.py** — Spec 289 — SQLModel typed entities derived from the graph ontology.

The ontology (`Ontology.nodes` = label→required fields, `Ontology.enums` =
(label,field)→allowed set) is the schema authority. (12 symbols)
- **_entity_store.py** — Spec 289 Slice 2 — the graph-authoritative typed projection.

Every graph data entity is MIRRORED into a typed row in a SQLModel
(``table=True``) table that shares graphqlite's ONE ``.db`` file. (48 symbols)
- **_enums.py** — Spec 284 — projected-enum substrate.

A *projected enum* is a field whose graph value is a closed enum, but whose
caller-facing parameter accepts free text and is PROJECTED onto a canonical
member — keeping the original rich text in a paired ``<field>_detail`` prop so
nothing is lost (the non-lossy contract). (3 symbols)
- **_envelope.py** — Spec 146 Slice 1 — engine-output-prefix discipline.

The Claude API's prompt-caching is a prefix-match: any byte change anywhere in
the cached prefix invalidates everything after it. (14 symbols)
- **_events.py** — Spec 349a — the pillar event bus.

A capability/intent/memory SUBSCRIBES to a hook event by declaring a handler;
the engine fans each hook out to the matching subscriptions, with a ``once_per``
dedup backed by the Spec 336 ephemeral store's SEPARATE ``event_marker`` table (so
it survives the fresh-process-per-hook model — Spec 349 review M5 — WITHOUT
polluting the captured tool-call rows). (11 symbols)
- **_frontmatter.py** — Spec 283 (+ minimal Spec 278) — frontmatter emit / parse / hash.

The render substrate writes each graph entity to a markdown file carrying a
YAML-ish frontmatter block (the node id + key fields, so a re-render is
byte-identical and `parse` reconstructs the slice). (9 symbols)
- **_frugal.py** — Frugal core discipline — Spec 332 Slice 1 (level + render).

Agency's own minimal-code reflex (a redevelopment, not a port): a ladder + a
non-negotiable safety floor. (24 symbols)
- **_hooks.py** — Spec 280 Slice 1 — hooks install verification + foreign-hook wrapping.

The agency plugin ALREADY ships hooks (`hooks/hooks.json` + Spec 076
unified-event-hook dispatcher). (24 symbols)
- **_host_bridge.py** — Spec 285 Slice 1 — the host-bridge seam.

`ctx.sample()` / `ctx.elicit()` live on the FastMCP ``Context``, which is
injected only into wired tools — capability verbs (and the ``skill_walk``
walker) receive the agency ``CapabilityContext`` and have no handle to the
client. (26 symbols)
- **_host_llm.py** — Spec 279 Slice 1 — host-LLM delegation envelope.

When the AnthropicDriver isn't capable (no ``ANTHROPIC_API_KEY`` + no
injected client), ``driver.backend()`` returns ``"none"`` and
``driver.complete`` raises ``AUTH_FAILED``. (17 symbols)
- **_install_adapters.py** — Spec 333 — multi-agent self-installer.

One ``surface_card`` (derived from the live registry + the Spec 332 frugal
discipline) projected into each agent's native instruction format. (22 symbols)
- **_invoke.py** — Spec 286 Phase-1 / A3 — the `Registry.invoke` decomposition.

`Registry.invoke` was a ~105-line god-method fusing five responsibilities. (15 symbols)
- **_lifecycle_events.py** — Spec 344 — typed ``LifecycleEvent`` shape + transition-class classifier.

Mirrors ``_loop_events.py`` (Spec 156): a pure, engine-free record so tests /
doctor / audit can build and assert a transition without an engine. (10 symbols)
- **_lifecycle_machines.py** — Spec 345 — machine registry for the generic state-machine substrate.

Reads machines.json at first access, resolves `derives` chains, validates
the terminal floor per-machine. (15 symbols)
- **_lifecycle_transitions.py** — Spec 340 — the enforced A2A transition table (the substrate state machine).

`ontology.py::LifecycleState` constrains the *value* of `state`; this module
constrains the *transitions* between values. (11 symbols)
- **_link_finding.py** — Spec 173 Slice 1 — typed LinkFinding for the reflection-edge linter.

Every Reflection in the graph MUST carry two edges: `SERVES` to an
Intent (Spec 002 provenance moat) and `OBSERVED_DURING` to the Event
that produced the observation (Spec 076 unified-hook discipline).

Spec 173 Slice 1 ships the typed lint finding so the audit + the CI
gate consume one shape. (9 symbols)
- **_llm.py** — Spec 092 G3 / Spec 331 — the LLM-decider boundary (an ``llm`` Driver on the
Spec-002 registry).

A constrained classifier the engine uses where a small judgement is needed without an
autonomous agent — today `intent.suggests`'s ``llm_select`` Matcher and
`delegate.dispatch_decision`'s optional S12 LLM tie-breaker. (35 symbols)
- **_loop.py** — agency/_loop.py — the lifecycle-spine loop module (Specs 362–369).

The looper port lives here: looper (https://github.com/ksimback/looper, by
Kevin Simback / @ksimback, MIT) reimplemented as the lifecycle SPINE, not a
capability. (72 symbols)
- **_loop_events.py** — Spec 156 Slice 1 — typed LoopEvent shape + pure loop detector.

The dogfood loop needs to know when an agent is repeating itself: 3 raw
`git commit` calls in a row, 4 identical Edit invocations, the same
spec being re-walked over and over. (9 symbols)
- **_monitor.py** — Spec 021 — the engine Monitor channel.

Claude Code's plugin system supports ``monitors/monitors.json`` — each entry is
a long-running shell command whose stdout lines are delivered to the agent as
notifications. (19 symbols)
- **_overflow.py** — Spec 154 Slice 1 — output overflow capture + recall (pure library).

When a verb returns more than the token budget (Spec 023), the engine
truncates — and the truncated tail was LOST, even though it might hold
the answer. (15 symbols)
- **_pillars.py** — Spec 375 — the pillar-skill source loader.

The three non-capability concepts of CORE.md's four (Intent · Lifecycle · Memory)
are first-class skills, authored as committed `skill.yaml` of `type: pillar` under
`agency/pillars/`. (8 symbols)
- **_predicates.py** — Spec 011 — decidable gate predicates (pure module helpers, not verbs).

A predicate that blocks a phase IS a `gate` (CLUSTERS:18). (9 symbols)
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
path (synthetic `ambiguous`, no dispatch). (9 symbols)
- **_prosody.py** — Shared prosody helpers — deterministic, driver-free text math.

Lifted from music/_main.py + novel/_main.py post Round-1 sc-analyze
finding F2 ("_syllables_word duplicates music's _syllables; same
heuristic, two implementations, drift risk").

Both music's `lyric_report` family and novel's `analyze_readability`
need a syllable count; promoting to a shared module so one fix lands
in one place. (3 symbols)
- **_relevance.py** — Spec 350 Slice 1 — relevance filter (content-aware output trimmer).

Pure ``relevance_filter(text, profile) -> dict`` that extracts signal lines from
verbose output by include/exclude regex patterns + neighbour context. (10 symbols)
- **_reload_sync.py** — Keep the INSTALLED ``agency`` package in step with the source checkout the MCP
server runs in — the durable half of "update the installed version every time"
(Spec 302 Slice 3).

The pipx-only install doctrine (Spec 055/065) INTENDS an editable install
(``pipx install --editable …``) so the running server always imports the live
source. (10 symbols)
- **_render.py** — Spec 283 Slice 1 — the capability render substrate (graph → markdown view).

A capability declares a `RenderSpec`: a list of `RenderRule`s binding a node
`label` to (output_path, frontmatter, body, kind). (18 symbols)
- **_replay_invariants.py** — Spec 195 Slice 3 — monotone invariant verification for replay chains.

Spec 195 Slice 2 ships `dogfood.replay_events(for_intent_id)` which
returns events ordered with each event's `prior_event_id` pointing at
the previous event's id. (5 symbols)
- **_research_citation.py** — Spec 168 Slice 1 — typed Citation shape + backend-selection invariant. (10 symbols)
- **_retry.py** — Spec 282 — ``retry_transient``: the correct retry primitive.

Replaces the anti-pattern that produced the evidence retry storm
(``scripts/ingest_canon.py`` looping ``for attempt in range(1, 40)`` "while
progress is made"): retry a call ONLY when its result is a wire error envelope
classified ``transient``. (6 symbols)
- **_runner.py** — Spec 073 — the toolchain `runner` boundary.

A thin, stubbable boundary (like `JulesClient` / `GitClient`) so `dogfood`'s
toolchain verbs can be exercised in tests without shelling out. (5 symbols)
- **_schema_coverage.py** — Spec 153 — template/schema coverage audit (engine-side core).

Moved out of ``scripts/check_schema_coverage.py`` (Spec 153 Slice 3) so the
engine — ``agency_doctor`` — can import the audit WITHOUT depending on the
dev-only ``scripts/`` tree (the wheel packages only ``agency``). (15 symbols)
- **_session_snapshot.py** — Session-graph snapshot — portable SQLModel export/import (user directive 2026-06-19). (16 symbols)
- **_skill_load.py** — Spec 371 Slices 2-3 — load a capability's v2 Skill + read its provenance.

A capability's skill data DERIVES from its module docstring (rule 2 — no
duplicated authored file). (12 symbols)
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
- Top-level `kind` (e.g. (26 symbols)
- **_substrate_tools.py** — Substrate tools as a registered set — Spec 286 Phase 2 / A5.

The engine exposes a handful of WIRE TOOLS that are **not** capability verbs:
``lifecycle_gate`` · ``lifecycle_open`` · ``lifecycle_move`` ·
``lifecycle_close`` · ``memory_graph_provenance`` · ``hook_event`` ·
``intent_bootstrap`` · ``agency_install`` · ``agency_doctor`` ·
``agency_welcome``. (39 symbols)
- **_tokens.py** — Spec 082 — the token-count boundary.

ONE place to count tokens, with tiers (best first):
  1. (25 symbols)
- **_toolcalls.py** — Ephemeral tool-call store — Spec 336 S2.

Pre/post tool calls are high-volume and full-payload (no-truncate, Spec 336 S1).
Keeping them as `Event` nodes in the durable bi-temporal graph bloated
`session.db` (~95% of nodes were Events). (15 symbols)
- **_typed_shapes_wave1.py** — Spec 171 + 175 + 176 Slice 1 — typed shapes for the wave-1 batch. (17 symbols)
- **_typed_shapes_wave1_part2.py** — Wave-1 enhancement Slice 1 batch — 8 typed shapes.

Specs 155 / 160 / 163 / 166 / 167 / 172 / 174 / 177. (32 symbols)
- **_typed_shapes_wave3.py** — Wave-3 enhancement Slice 1 batch — substantive typed shapes (Specs 178/179/180/182/183).

Promotes 5 wave-3 specs from catalogue stub (agency/_enhancement_stubs.py)
to substantive Slice 1 code. (21 symbols)
- **_typed_shapes_waves4_12.py** — Waves 4-12 enhancement Slice 1 batch — substantive typed shapes.

Promotes every wave-4..12 spec (184-277, minus 195/281) from catalogue
stub to substantive Slice 1. (192 symbols)
- **_verb.py** — Spec 286 Phase-1 / A4 — the typed ``Verb`` value object.

A capability verb was historically an untyped ``dict`` —
``{"role", "fn", "inject", "tags", "param_enums", "name"?}`` — built by the
``@verb`` decorator (``fn._verb``), normalised by ``_wrap_method`` /
``Registry.register``, and **mutated in place** (``_wire_skill_tags`` does
``spec.setdefault("tags", set()).add(...)``). (10 symbols)
- **_wet_verify.py** — Spec 164 Slice 1 — typed VerifyResult shape for wet implementation-discipline phases.

The Slice 2 wet path (Spec 147 AnthropicDriver) runs the discipline-skill
verify step against a phase's outputs + the live graph; this slice ships
the typed return shape every verifier — wet OR scaffold (the deterministic
fallback) — coerces to.

Per Spec 050 graceful-degradation pattern: when `[anthropic]` is absent
(or the API key isn't provisioned), `matcher == "scaffold"` for every
discipline. (9 symbols)
- **_wire_envelope.py** — Spec 286 Phase-2 / A7 — `WireEnvelope`: the ONE owner of the wire-shape rule.

The "strip / re-wrap `{result}`" rule (Spec 019) and the Spec 282 failure
envelope (`{ok, error:{code,message,severity,retryable,trace_id}}`) were
duplicated across `engine._wire`/`engine._shape_wire_result` and
`cli._structured`. (7 symbols)
- **cache.py** — Spec 031 §E / Task 2.4 — atomic JSON cache for skill emit idempotency.

The cache lives at <cache_dir>/skill-cache.json — a single document mapping
capability name → {hash, files: [paths]}. (10 symbols)
- **capability.py** — Capability — the craft (the open concept). (82 symbols)
- **cli.py** — Bash-callable engine — the L3 layer of the harness-in-harness ladder (Click).

A bash-only agent (Jules, Codex, a raw LLM with a shell) has no MCP client and no
Skill loader. (46 symbols)
- **disclosure.py** — Adaptive disclosure renderer — Spec 023 Phase 1.

A pure rendering pass over Capability/Verb/Skill nodes. (22 symbols)
- **engine.py** — Engine — one FastMCP server + one graph.

**Code-mode IS the contract** (lean: no separate four-verb surface). (69 symbols)
- **install.py** — Setup for the Agency Plugin for Claude Code.

This is the "in setup" that maps the harness-in-harness MICRO-skills (the engine's
capability verbs) into MACRO-skills (the capabilities themselves) behind a single
`help` discovery surface. (66 symbols)
- **intent.py** — Intent — the human-owned root (why/what merged; deliverable is an attribute).

capture -> confirm -> (amend via supersede). (12 symbols)
- **lifecycle.py** — Lifecycle — the task/agent state-machine substrate (the Lifecycle PILLAR).

Peer to ``intent.py`` and ``memory.py``: the engine holds one ``Lifecycle``
(``engine.lifecycle``) and capabilities reach it via ``ctx.lifecycle`` (Spec 339).
It is NOT a capability — it is the pillar substrate. (34 symbols)
- **memory.py** — Memory — the moat. (49 symbols)
- **ontology.py** — Strict, EXTENSIBLE ontology for the agency graph.

The **core** defines the irreducible base: every node type's required-field
schema, the enumerated edge set, and the closed enums. (29 symbols)
- **skill.py** — Micro-step skill walker.

A skill is a Lifecycle of ordered Phases (a schema a capability contributes, e.g.
the `develop` or `plugin` skills). (10 symbols)
- **skill_emit.py** — Spec 031 §D + Spec 032 §G — per-capability skill emission pipeline. (39 symbols)
- **templates.py** — Templates — the prestructure for the resulting document of each step of a chain.

A small library of *living document* skeletons a Capability `act` fills in. (14 symbols)
- **toolresult.py** — ToolResult — the in-sandbox envelope a verb may return.

Per Spec 001 (Option C, the canon-aligned, token-lean choice): the envelope is
an INTERNAL Python dataclass, NOT the wire shape. (14 symbols)

### `agency/_drivers/` (2 files)
- **__init__.py** (1 symbols)
- **_anthropic.py** — Spec 147 — the canonical AnthropicDriver boundary (Slice 1: inference surface).

ONE typed surface every verb that needs LLM inference (thinking, prompt-composition,
the dogfood-classifier, scene-writer, …) wires through, so the engine stops doing it
"lossy-in-chat" (Spec 110) or via one-off shims (Spec 026's pending llm_select). (24 symbols)

### `agency/_middleware/` (2 files)
- **__init__.py** — Engine middleware — cross-cutting helpers that are NOT capabilities.

The canon (CORE.md:16-18) names loop-detection *middleware*, not a concept: it
is a fast-twitch self-interrupt signal an engine/hooks layer can run, never a
discoverable verb. (1 symbols)
- **loop.py** — Loop-detection middleware (Spec 011, port of the-agency-system Plan 119).

A pure, stdlib-only signal: do the recent messages / tool results repeat enough
to indicate the agent is stuck in a loop? Jaccard similarity over 3-char
shingles, pairwise max over the last 4 messages + last 5 tool results (≤ 9² = 81
pairs), detected when the max ≥ 0.7.

This is **middleware, not a concept** (CORE.md:17): `detect_loop` is never
registered as a capability verb and never sources its own history — the caller
(a future hooks layer) supplies `messages`/`tool_results`. (9 symbols)

### `agency/capabilities/` (3 files)
- **__init__.py** — Capabilities — discovered by REFLECTION, not hand-wired.

Drop a module in this package that defines a `Capability` instance OR a
`CapabilityBase` subclass at module level; `discover_capabilities()` finds both via the stdlib
reflection APIs (`pkgutil.iter_modules` to walk this package's directory +
`importlib` to import each module + `isinstance`/`issubclass` to pick them out).
The engine calls `discover_capabilities()` and registers everything, and auto-wires one MCP
tool per verb from the verb signature (`inspect.signature`). (6 symbols)
- **_embed.py** — Embedder boundary — pluggable semantic-ranking backend. (20 symbols)
- **_vcs.py** — _vcs — the version-control boundary the `workspace` and `branch` capabilities
talk to.

`VCSBackend` is a Protocol; `GitClient` is the default backend — real `git` (and
`gh` for PRs) via subprocess. (20 symbols)

### `agency/capabilities/adr/` (3 files)
- **__init__.py** — adr — architecture decision records, ported onto the substrate (Spec 354).

The enhanced WH(Y) ADR format (the `adr` repo) bound onto agency's primitives:
a strict `Decision` node, thematic-living ADRs (Documents), typed dependency
edges, and decidable WHY/MIN validation. (3 symbols)
- **_main.py** — adr — architecture decision records on the substrate (Spec 354, Slice 1).

Use when: an architectural decision must be RECORDED as a first-class,
queryable, gate-able artefact — its WH(Y) rationale, the alternatives neglected,
the trade-offs accepted — separate from the spec that implements it.
Triggers:
- A spec or design makes a choice whose rationale would otherwise be lost
- "Why did we decide X (and not Y)?" needs a durable, traversable answer
- An ADR must be validated against the WH(Y) format before approval
Red flags:
- Burying a decision in spec prose where it is lost at implementation time → draft it
- Hand-writing a Decision via `manage.create` without the WH(Y) discipline → use adr.draft
- Putting implementation detail in the decision → that belongs in the spec it REFINES

Slice 1 lands the decision-record primitive: `theme` (a thematic-living ADR =
a Document), `draft` (a WH(Y) `Decision` PART_OF a theme — recordable as a
`proposed` skeleton, completed incrementally), and `validate` (decidable WHY
rules DERIVED from the `decision` Schema — never an LLM gate).

Slice 2 adds the dependency + lifecycle surface: `read`/`update` (the domain
read + in-place mutator — never reach into `manage` for an ADR), `link` (typed
SPEC-001-C edges, enforcing DEP-001 no-cycle + DEP-003 no-depend-on-rejected),
`supersede` (the SPEC-001-C automatic actions over the core `SUPERSEDED_BY`
edge), `theme_status` (the SPEC-001-D aggregate, derived), `impact` (incoming
dependents to depth), and `render` (live decisions → the theme Document, with a
collapsed superseded-history appendix — panel B3).

Spec 355 Slice 1 adds the Definition-of-Done hinge: `dod_check` (the eight
SPEC-001-E criteria as decidable findings — DOCUMENTATION reuses 354 `validate`)
and `approve` (the gate — blocks on a failed automated criterion, pauses at the
human criteria via `ctx.elicit`, records a `Gate` node, and only the intent
OWNER may confirm or override; an agent may not self-approve). (64 symbols)
- **ontology.py** — adr ontology — the WH(Y) Decision node + its typed Schema + dependency edges
(Spec 354).

Reconciliations folded from the spec-panel (2026-06-20) and the
think-hard-about-the-ontology-and-Schema pass (owner directive, 2026-06-20):

- **AdrTheme is NOT a new node label** — a theme is a ``Document`` with
  ``kind="adr-theme"`` + a ``layer`` tag. (7 symbols)

### `agency/capabilities/analyze/` (20 files)
- **__init__.py** — analyze — multi-axis decidable code analysis (Spec 042).

Folder-form capability. (3 symbols)
- **_architecture.py** — Spec 042 / Spec 051 — analyze.architecture axis (dependency graph + structural).

Rules shipped:
  A001 — circular import (fail). (29 symbols)
- **_bandit.py** — Spec 050 — bandit wrapper.

Composes bandit's CWE-mapped Python security ruleset into the agency
Finding shape. (11 symbols)
- **_coverage.py** — Spec 383 §1 — source-coverage matrix loader (the brooks dozen).

The twelve classic software-engineering books are vendored as cited data in
``data/source-coverage.json`` (from brooks-lint ``_shared/source-coverage.md``).
This module is the single reader of that matrix — the companion to ``_decay``:
``decay-risks.json`` says WHICH risk a symptom evidences, ``source-coverage.json``
says WHICH principle of WHICH book grounds the Iron-Law Source, and lists the
``do_not_ignore`` guardrails that keep a citation from becoming shallow
book-name-dropping.

One book registry, two consumers: every book a decay risk cites
(``decay-risks.json`` ``sources[].book``) MUST exist here (the grounding
invariant — Spec 383). (5 symbols)
- **_decay.py** — Spec 354 — decay-risk knowledge loader + decidable→risk tagger (the bridge).

The twelve decay risks (R1-R6 code, T1-T6 test) are vendored as cited data in
``data/decay-risks.json`` (from brooks-lint ``_shared/decay-risks.md`` +
``test-decay-risks.md``). (9 symbols)
- **_findings.py** — Spec 042 — Finding shape (the contract).

Every analyze.* axis returns a list of Finding value objects. (13 symbols)
- **_main.py** — analyze — multi-axis decidable code analysis (Spec 042).

Analyze runs decidable transforms over source and reports findings on the quality, security, performance, and architecture axes as graph nodes the orchestrator can reason about, rather than prose opinions. (30 symbols)
- **_migrate.py** — Spec 385 — one-time brooks-lint → agency quality migration (pure helpers).

A project mid-stream on the brooks-lint plugin has two sidecar files: a
``.brooks-lint.yaml`` config and a ``.brooks-lint-history.json`` trend. (6 symbols)
- **_paths.py** — Spec 048 — analyze.paths axis.

Surfaces intent-shape patterns that suggest a missing specialized
capability would shorten the intent→artefact path. (12 symbols)
- **_performance.py** — Spec 042 — analyze.performance axis (AST-based decidable checks).

Rules shipped (v1):
  P001 — nested-loop on the same iterable (warn). (15 symbols)
- **_quality.py** — Spec 042 — analyze.quality axis (decidable lint rules only).

Rules shipped (v1):
  Q001 — unused-import (warn). (18 symbols)
- **_radon.py** — Spec 050 — radon wrapper.

Composes radon's cyclomatic complexity + maintainability index into
the agency Finding shape. (18 symbols)
- **_report.py** — Spec 382 §4 / 384 — report-render helpers (tiering · summary · mermaid · the
quality-report render itself).

``analyze.report`` delegates here: ``render_quality_report`` renders the Spec 384
templates (``quality-report.md`` + ``iron-law-finding.md`` via ``ctx.render``) and
applies the INTERIM ``<!-- BEGIN IF -->`` / authoring-comment processing — Spec 388
replaces this whole strip path with a Jinja ``{% if %}`` engine, a one-file delete
here. (13 symbols)
- **_review.py** — Shared review core (Spec 380): scope-detect · merge · Iron Law gate · classify.

This module is the single engine both develop.review (interactive) and
analyze.review (headless/CI) drive. (24 symbols)
- **_ruff.py** — Spec 050 — ruff wrapper.

Composes ruff's 700+ Python lint rules into the agency Finding shape.
Degrades silently when ruff isn't on PATH (Spec 050 §"compose, don't
replace" — internal Q001-Q004 still fire in that case).

Subprocess + JSON; no Python-level ruff import (ruff is a Rust binary
anyway). (11 symbols)
- **_sarif.py** — Spec 382 §1 — SARIF 2.1.0 emit, straight from structured Findings.

Agency findings are born structured (Spec 360 ``Finding`` nodes), so SARIF renders
with NO parsing step — brooks-lint's ``report-parse.mjs`` is dropped. (12 symbols)
- **_score.py** — Spec 381 — Health Score (computed, preset-weighted) + leverage ranking.

Pure functions over the recorded Findings. (22 symbols)
- **_security.py** — Spec 042 — analyze.security axis (decidable patterns only).

Rules shipped (v1):
  S001 — eval/exec call (fail). (18 symbols)
- **_subprocess_analyzer.py** — Spec 286 — the shared subprocess-analyzer template (Template Method).

The ruff / bandit / radon wrappers all repeated the identical scaffold:

    which-guard → ``subprocess.run(argv, capture_output, text, timeout)``
    in a TimeoutExpired/OSError guard → returncode tolerance → ``json.loads``
    in a JSONDecodeError guard → payload→Finding mapping.

The only per-tool variation is the ``argv``, the acceptable return codes, and
the payload→Finding mapping. (14 symbols)
- **_walk.py** — Shared file-walking helpers for the analyze axes (DRY).

Every axis (_quality, _security, _performance, _architecture) needs
the same: walk a tree for ``.py`` files (skipping ``__pycache__``,
``.venv``, ``.git``, etc.), and read each file safely. (5 symbols)

### `agency/capabilities/branch/` (2 files)
- **__init__.py** — branch — finish a development branch. (2 symbols)
- **_main.py** — branch — finish a development branch: detect state, then merge / open a PR /

Branch inspects the working tree and remote state and finishes the branch the appropriate way — merge when clean, a PR when review is needed, or a clear report of what blocks completion. (14 symbols)

### `agency/capabilities/config/` (2 files)
- **__init__.py** — config — read & persist unified .agency/config.yaml values. (2 symbols)
- **_main.py** — config — read & persist unified .agency/config.yaml values.

Config exposes get / set / list over the unified config resolver so an agent or
the CLI can inspect and change agency configuration without hand-editing the
file. (7 symbols)

### `agency/capabilities/delegate/` (2 files)
- **__init__.py** — delegate — agent orchestration: fan-out + quota + join. (2 symbols)
- **_main.py** — delegate — agent orchestration: fan-out + quota + join. (26 symbols)

### `agency/capabilities/develop/` (2 files)
- **__init__.py** — develop — discipline-walk templates + scaffolds. (2 symbols)
- **_main.py** — develop — the development-workflow capability.

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance. (59 symbols)

### `agency/capabilities/discover/` (3 files)
- **__init__.py** — discover — guided intent-discovery capability (Spec 307 program · 308 scaffold).

The Intent pillar's prompt-shaped peer: it turns a one-sentence seed into a
grounded, clarity-gated, confirmed Intent by interleaving research-grounding
with AskUser elicitation. (3 symbols)
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
capability the 17 children (309-325) fill in. (7 symbols)
- **ontology.py** — discover ontology — Spec 307 consolidated OntologyExtension (locked surface).

Registers the WHOLE intent-pillar program's node/edge/enum/schema surface ONCE
(Spec 307 §"The ontology"), so the 17 child specs (309-325) populate node
*instances* without ever re-touching the schema. (11 symbols)

### `agency/capabilities/discover/clusters/` (7 files)
- **__init__.py** — discover.clusters — cluster mixins composed into the single DiscoverCapability. (8 symbols)
- **_base.py** — discover.clusters._base — the shared mixin every child cluster composes.

Spec 308 establishes the foundation; child specs (309-325) add their helpers
here as they implement (``_record_turn`` for interview/clarify, ``_session`` /
``_session_of`` for the session lifecycle, ``_clarity_inputs`` for the Spec 322
score). (7 symbols)
- **ask.py** — discover.ask — the reusable well-formed AskUser question primitive (Spec 310).

The ONE place the well-formed-question rules live (option count · recommended-
first · multiSelect gate · header budget · derive-not-invent). (13 symbols)
- **clarify.py** — discover.clarify — the ambiguity-resolution loop (Spec 311).

Finds what is still vague in a draft Intent, asks ONE targeted question per
ambiguity (composing discover.ask — 310 owns the well-formed-question contract),
folds each verbatim answer back into the Intent BI-TEMPORALLY (intent.amend —
supersede, prior revision retained), and records a CLARIFIES trail — until the
Intent's residual ambiguity drops below threshold or a max-rounds budget is hit.

The ambiguity heuristics live in data/ambiguity-signals.json (the Driver seam,
Spec 147, sharpens questions from GROUNDS evidence in Slice 2). (11 symbols)
- **interview.py** — discover.interview — the adaptive elicitation engine (Spec 309).

Guided-exploration core of the Spec 307 program: turns a one-sentence seed into a
DRAFT Intent by running an adaptive beat-chain, recording every turn as graph
provenance (Goal 2 — *how the WHY was discovered*). (15 symbols)
- **refine.py** — discover.refine cluster — Intent clarity scoring + (Spec 320) refinement.

Spec 322 lands ``clarity`` here (the cluster that also holds ``refine``, Spec 320):
the Intent-readiness scorer the ``guided-discovery`` discipline's confirm gate
reads. (7 symbols)
- **scope.py** — discover.scope cluster — structure-layer verbs (Spec 317 acceptance, 318 scope).

Spec 317 lands ``acceptance`` here: it derives testable, Gherkin-shaped acceptance
criteria from the Intent's ``deliverable`` — DERIVED, never invented. (12 symbols)

### `agency/capabilities/doctrine/` (2 files)
- **__init__.py** — doctrine — queryable engineering principles + behavioral rules (Spec 303). (2 symbols)
- **_main.py** — doctrine — queryable engineering principles + behavioral rules (Spec 303).

Closes the SuperClaude/superpowers port audit: PRINCIPLES + RULES were the only
unported aspect of that doctrine. (16 symbols)

### `agency/capabilities/document/` (7 files)
- **__init__.py** — document — graph-native rendering + briefing (Spec 043).

Folder-form capability. (3 symbols)
- **_explain.py** — ``document.explain`` — code → educational text via composition.

NO LLM. (16 symbols)
- **_index_repo.py** — ``document.index_repo`` — the 94%-reduction repo briefing.

Sources the file list + per-file symbol counts from the **codegraph** index when
it is initialized (``codegraph files --json`` — complete + gitignore-accurate),
falling back to a filesystem walk otherwise; reads first-sentence brief slices
from module docstrings; and synthesises a deterministic PROJECT_INDEX.md. (15 symbols)
- **_interconnect.py** — graph<->markdown interconnect (Spec 292).

The premise flip: markdown files are no longer a one-way *rendered view* of
the graph — they are an editable PEER surface that round-trips back into it.

Mechanism (keep-both, bi-temporal, stable anchor):

- A participating ``.md`` file carries a stable ANCHOR on its first line::

      <!-- agency-node: document:abc12345 -->

  reusing the existing HTML-comment marker convention (cf. (11 symbols)
- **_main.py** — document — graph-native rendering + briefing (Spec 043).

Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph. (27 symbols)
- **_render.py** — Scope renderers for ``document.render`` — graph → markdown.

Each function takes a Memory and returns the rendered markdown for
its scope. (9 symbols)
- **_templates.py** — Markdown rendering primitives shared across render scopes. (7 symbols)

### `agency/capabilities/dogfood/` (2 files)
- **__init__.py** — dogfood — graph-native observation ledgers (Spec 017 + 020 v2).

Folder-form per Spec 060 §Phase 3 — promoted from `dogfood.py` so the
capability can ship its own `templates/` + `schemas/` subfolders. (2 symbols)
- **_main.py** — dogfood — graph-native observation ledgers (Spec 017). (9 symbols)

### `agency/capabilities/dogfood/clusters/` (6 files)
- **__init__.py** — dogfood.clusters — cluster mixins composed into the single DogfoodCapability.

Spec 286 P3 — the ~1147-line ``dogfood`` god-class split into one mixin per
cluster. (7 symbols)
- **_base.py** — dogfood.clusters._base — shared DogfoodCapability infrastructure (Spec 286 P3).

Dogfood's verbs lean on module-level helper functions (the amendment
classifier rules, the observation-header parser, the export version
constant) rather than instance-level driver wiring. (2 symbols)
- **amendment.py** — dogfood.amendment — Reflection→spec-amendment classifier (Spec 150/147/279). (29 symbols)
- **observe.py** — dogfood.observe — graph-native observation ledgers (Spec 017). (12 symbols)
- **portage.py** — dogfood.portage — JSON export + replay for merge-conflict recovery (Spec 020). (13 symbols)
- **session.py** — dogfood.session — session-tracking: decisions, boundary audit, replay (Spec 114/195/154). (8 symbols)

### `agency/capabilities/frugal/` (2 files)
- **__init__.py** — frugal — the minimal-code discipline as a capability (Spec 348, ponytail port).

Folder-form: the verbs WRAP the core ``agency/_frugal.py`` (Spec 332 — the single
source for the ladder + safety floor), exposing the discipline as a discoverable,
CLI-mirrored, MCP-wired capability. (2 symbols)
- **_main.py** — frugal — the lazy-senior-dev discipline as a capability (Spec 348, the ponytail port).

Frugal forces the laziest solution that actually works: the ladder
YAGNI -> stdlib -> native -> installed-dep -> one line -> minimum, with a
non-negotiable safety floor (validate / secure / accessibility never cut). (34 symbols)

### `agency/capabilities/gate/` (2 files)
- **__init__.py** — gate — a reusable, programmatic gate predicate. (2 symbols)
- **_main.py** — gate — a reusable, programmatic gate predicate. (6 symbols)

### `agency/capabilities/intent/` (3 files)
- **__init__.py** — intent — Spec-091 critical-thinking capability. (2 symbols)
- **_brooks.py** — Brooks-lint — decidable conceptual-integrity heuristics (Spec 359).

The 9th `intent` critical-thinking pass, grounded in Fred Brooks (*The Mythical
Man-Month*, *No Silver Bullet*). (15 symbols)
- **_main.py** — intent — critical-thinking methods that reason about the serving intent (Spec 026/091). (18 symbols)

### `agency/capabilities/jules/` (7 files)
- **__init__.py** — jules — the agent capability (folder form per Spec 060 §Phase 3, (2 symbols)
- **_main.py** — jules — the agent capability. (61 symbols)
- **api.py** — Minimal, self-contained Jules REST client (vendored into the agency plugin).

A thin client for the Jules REST API — the two calls the `jules` capability needs
(`jules_create` and `jules_get`). (33 symbols)
- **patch.py** (5 symbols)
- **preambles.py** — Jules dispatch-prompt preambles + Mode A/B assembler (Spec 013 Phase 2).

Per ``Plan/013-…/DESIGN.md`` "Design — `_jules_preambles.py`":

- **One canonical preamble** (``PREAMBLE``) carrying the per-dispatch
  must-name tool list + a literal pointer to AGENTS.md + AGENCY_PROTOCOL.md.
- The doctrine (the five invariants from ``AGENCY_PROTOCOL.md``) lives at
  the repo root and is paid for once per snapshot / clone — NOT once per
  dispatch.
- ``assemble(source, starting_branch, prompt, preset_name=...)`` chooses
  Mode A (dogfood, ``source == DISPATCH_SELF_SOURCE``) vs Mode B
  (delegate, anything else). (12 symbols)
- **skills.py** — Jules-specific Lifecycle skill templates (Spec 013 Phase 5+).

A skill IS a capability (CORE.md:47-62) — Lifecycle templates of atomic
gated step-graphs. (8 symbols)
- **watch.py** (25 symbols)

### `agency/capabilities/loop/` (2 files)
- **__init__.py** — loop — design + run a verified agent loop (the looper port; Specs 362–369, 387). (2 symbols)
- **_main.py** — loop — design + run a verified agent loop (the looper port; Specs 362–369, 387).

The **wired surface** of the looper port: thin verbs delegating to the
lifecycle-spine logic in ``agency/_loop.py`` so the loop is discoverable
(``search``), schema'd (``get_schema``), runnable (``execute``/CLI), and — the
point of Spec 387 W1 — records an ``Invocation`` on every call (the provenance
moat the bare spine functions bypassed). (21 symbols)

### `agency/capabilities/manage/` (2 files)
- **__init__.py** — manage — generic CRUD over every graph node type (Spec 293). (2 symbols)
- **_main.py** — manage — generic CRUD over every graph node type (Spec 293).

The write/read management surface that completes the Memory pillar: a single,
capability-AGNOSTIC CRUD over EVERY ontology label, so every aspect of the
graph — Document, Intent, Track, Novel, Reflection, Session, … — has Create,
Read, Update, Amend and Retract without per-capability code. (35 symbols)

### `agency/capabilities/mode/` (2 files)
- **__init__.py** — mode — SuperClaude behavioral modes, first-class (Spec 295). (2 symbols)
- **_main.py** — mode — behavioral modes, first-class (Spec 295).

A native reimplementation of SuperClaude's behavioral modes: postures that
change HOW the agent operates. (11 symbols)

### `agency/capabilities/music/` (7 files)
- **__init__.py** — music — clustered domain capability (Spec 093 master / Spec 094 lifecycle child).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module). (3 symbols)
- **_main.py** — music — clustered domain capability (Spec 093 master + Specs 094-100 + 115).

Music graduates from ``examples/music.py`` into a first-class folder-form
capability under ``agency/capabilities/music/`` (Spec 094). (6 symbols)
- **_slug.py** — music slug — single source of truth for the music capability's slug shape.

Both ``_main.py`` (verbs) and ``drivers_production.py`` (FileStateDriver disk
layout) need slugs. (3 symbols)
- **config.py** — music config — Spec 115 production-binding config layer.

Loads `.agency/music-config.yaml` (per-project) with optional fallbacks at
`~/.agency-music/config.yaml` (user-global) and `$AGENCY_MUSIC_HOME/config.yaml`
(env override). (25 symbols)
- **drivers.py** — music drivers — the five external I/O boundaries the music capability reaches
through, as Spec-002 ``Driver`` protocols (Option B: typed, named methods; the
uniform contract is the RETURN TYPE via the wrapping verb, not a ``dispatch(op)``).

Each driver is a marker ``Boundary`` exposing its own typed methods (the ``jules.py``
``create/get/list`` shape). (145 symbols)
- **drivers_production.py** — music production drivers — Spec 115.

Real disk-writing + SQLite-backed implementations of the StateDriver +
DBDriver Protocols. (46 symbols)
- **ontology.py** — music ontology — the consolidated ``OntologyExtension`` (nodes, enums,
edges, skills, schemas, templates) for the music capability.

Spec 094 (lifecycle child of 093) consolidates the ontology into its own
module so subsequent cluster children (095 lyrics, 096 audio, 097
catalogue, 098 promo, 099 research, 100 gates) extend it additively without
churning the cluster code module. (26 symbols)

### `agency/capabilities/music/clusters/` (11 files)
- **__init__.py** — music clusters — per-cluster verb mixin modules (Spec 094 / Spec 286 P3).

The ``MusicCapability`` god-class splits into one mixin class per domain
cluster, composed into the single registered capability via multiple
inheritance (``_main.py``). (11 symbols)
- **_base.py** — music clusters — shared base + module constants/helpers (Spec 286 Phase 3).

The per-cluster file split (Spec 094 design §"Module layout") relocates the
``MusicCapability`` god-class into cluster mixin classes, one per domain
cluster. (25 symbols)
- **audio.py** — music audio cluster — mastering / mixing / QC / sheet-music / promo-video.

Spec 096 — 16 audio verbs + 2 composite gate verbs (measure · qc), plus the
007 audio verbs (master_album · analyze_mix · transcribe_sheet). (26 symbols)
- **catalogue.py** — music catalogue cluster — DB tweets · streaming URLs · promo state.

Spec 097 — 11 catalogue verbs + 1 composite gate verb (tweet-schedule), plus
the 007 catalogue verbs (catalogue_status · verify_streaming). (20 symbols)
- **cloud.py** — music cloud cluster — object-store publish via the CloudDriver.

``publish_asset`` (the CloudDriver banner verb from 007) — the generic
object-store publish entry point. (6 symbols)
- **gates.py** — music gates cluster — cross-cutting computed gates + validation + health.

Spec 100 — 4 top-level verbs (validate_album · validate_sections · diagnose +
the 5 composite release/pre-gen gates) plus the 007 gates (pregen_check ·
release_check · music_health). (16 symbols)
- **lifecycle.py** — music lifecycle cluster — ideas · albums · tracks · session (Spec 286 P3).

The lifecycle verbs (conceptualize · capture_idea · promote_idea · list_ideas ·
create_album · find_album · set_album_status* · create_track · list_tracks ·
set_track_status · rename_album · rename_track · album_progress ·
resume_session) relocate VERBATIM from ``_main.py`` into this mixin per Spec 094
design §"Module layout". (19 symbols)
- **lyrics.py** — music lyrics cluster — text/prosody transforms + composite lyric gates.

Spec 095 — 13 transforms + the lyric composite gate verbs (prosody ·
pronunciation · repetition · explicit · name-exposure), plus the 007 text
verbs (count_syllables · lyric_report). (25 symbols)
- **promo.py** — music promo cluster — promo copy · object-store publish · release package.

Spec 098 — 7 promo verbs + 1 composite gate verb (promo-review), plus the 007
promo verb (promo_copy). (13 symbols)
- **research.py** — music research cluster — research scope · claims · verification.

Spec 099 — 8 research verbs + 1 composite gate verb (verify). (15 symbols)
- **state.py** — music state cluster — album-status persistence + Spec-115 production binding.

``set_album_status`` (the StateDriver banner verb from 007) plus the Spec 115
production-binding verbs (get_config · load_override · get_reference ·
format_clipboard) that read config / reference / clipboard state. (11 symbols)

### `agency/capabilities/music/migrations/` (2 files)
- **__init__.py** — music migrations — one-shot install / schema-migration ops.

Empty placeholder per Spec 094. (1 symbols)
- **db_init.py** — Spec 097 — one-shot schema installer for the catalogue cluster's PostgreSQL backend.

Carries the bitwize ``schema.sql`` verbatim + the tweet table indexes that the
DBDriver methods (``create_tweet`` / ``list_tweets`` / ``search_tweets``) need
for sub-second response at scale. (3 symbols)

### `agency/capabilities/novel/` (5 files)
- **__init__.py** — novel — long-form prose authoring capability (Spec 101 master).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module). (3 symbols)
- **_main.py** — novel — minimum-viable-novel Slice 1 (Spec 101 master First-Principles Minimum). (60 symbols)
- **_slug.py** — novel slug — single source of truth for the novel capability's slug shape.

Mirrors `agency/capabilities/music/_slug.py`. (3 symbols)
- **config.py** — novel config — Spec 121 production-binding config layer.

Mirrors `agency/capabilities/music/config.py`: per-project
`.agency/novel-config.yaml`, global fallback, env override; mtime-cached
4-level resolution; minimal handrolled YAML parser when PyYAML missing;
`bootstrap()` writes default + creates content_root on first run.

Resolution order (first hit wins):
1. (24 symbols)
- **drivers_production.py** — novel production drivers — Spec 121. (30 symbols)

### `agency/capabilities/novel/clusters/` (11 files)
- **__init__.py** — novel.clusters — cluster mixins composed into the single NovelCapability.

Spec 286 P3 — the ~95-verb ``novel`` god-class split into one mixin per
SDLC/domain cluster. (12 symbols)
- **_base.py** — novel.clusters._base — shared NovelCapability infrastructure (Spec 286 P3).

The production-driver auto-wiring (Spec 121) + NOT_FOUND guards extracted
verbatim from ``novel/_main.py`` into a base mixin every cluster mixin and
the composed ``NovelCapability`` inherit. (11 symbols)
- **character_knowledge.py** — novel.character_knowledge — Character-knowledge cluster — knowledge ledger + anachronism audit + provenance (Spec 131). (8 symbols)
- **codex.py** — novel.codex — Codex cluster — Novelcrafter-parity codex entries (Spec 132). (10 symbols)
- **lifecycle.py** — novel.lifecycle — Lifecycle cluster — concept -> novel -> chapter -> scene -> render + idea/session (Spec 101/102). (31 symbols)
- **manuscript.py** — novel.manuscript — Manuscript cluster — catalogue coherence, renderers, composite gates, FormatDriver export (Spec 106/107/108/124). (18 symbols)
- **prose.py** — novel.prose — Prose cluster — driver-free prose analysis + editorial pipeline + craft gates (Spec 104/122). (21 symbols)
- **research.py** — novel.research — Research cluster — claims + xcap research/prompt/thinking integration (Spec 105 + tight-integration). (12 symbols)
- **storyform.py** — novel.storyform — Storyform cluster — Dramatica NCP decidable checks + coherence (Spec 103/120). (23 symbols)
- **storytime.py** — novel.storytime — Story-time / narrative-time cluster — events, reveals, narrative beats (Spec 128). (10 symbols)
- **world.py** — novel.world — World cluster — world sub-graph: cultures, religions, languages, magic, axioms (Spec 123). (15 symbols)

### `agency/capabilities/panel/` (2 files)
- **__init__.py** — panel — multi-expert business analysis (Spec 294). (2 symbols)
- **_main.py** — panel — multi-expert business analysis, first-class (Spec 294).

A native reimplementation of SuperClaude's Business Panel: nine strategic
thinkers, three interaction modes (discussion · debate · socratic), decidable
content-based mode selection. (15 symbols)

### `agency/capabilities/persona/` (2 files)
- **__init__.py** — persona — specialist engineering personas, first-class (Spec 297). (2 symbols)
- **_main.py** — persona — specialist engineering personas, first-class (Spec 297).

A native reimplementation of SuperClaude's specialist agents (architects,
engineers, analysts, mentors) as a built-in, dispatchable persona registry —
NOT ingested prompt files. (12 symbols)

### `agency/capabilities/plugin/` (3 files)
- **__init__.py** — plugin — develop the agency Claude Code plugin from inside the engine.

Folder-form per Spec 060 §Phase 3. (2 symbols)
- **_main.py** — The plugin-development capability — everything needed to develop a good plugin:

Plugin ports the plugin-development craft into compute: scaffolds, skill and command authoring, marketplace entries, and the lint rules that enforce the authoring doctrine. (11 symbols)
- **_skills_client.py** — Spec 083 — the boundary to the Anthropic Skills API (`/v1/skills`).

Lazy, like `JulesClient`: needs the `anthropic` SDK (`pip install -e .[publish]`) +
`ANTHROPIC_API_KEY`, and raises a clear error AT CALL TIME when absent — so the
default never imports `anthropic` and `plugin.publish_skill(dry_run=True)` works
offline. (5 symbols)

### `agency/capabilities/plugin/clusters/` (5 files)
- **__init__.py** — Cluster mixins for the `plugin` capability (Spec 286 P3). (6 symbols)
- **authoring.py** — Authoring cluster — scaffolding + skill/command/marketplace/step-doc renders.

The pure template-render functions (no `self`, no `ctx`) live here as module
functions; `AuthoringMixin` carries the thin `@verb` wrappers. (16 symbols)
- **lint.py** — Lint cluster — the authoring-doctrine rules as a polymorphic registry.

Spec 286 P3 OOP fix: the pre-split form spread each rule across THREE sites —
a ``_check_<rule>`` function, an entry in the ``_REMEDIATION`` dict, and a hand
wired call in ``lint_capability``. (90 symbols)
- **publish.py** — Publish cluster — uploads a capability's Agent Skill to the Skills API. (4 symbols)
- **reference.py** — Reference cluster — capability/verb reference lookup (the `help` map).

`help_map` is the pure renderer (no `self`, no `ctx`); `ReferenceMixin` carries
the thin `@verb`. (5 symbols)

### `agency/capabilities/prompt/` (3 files)
- **__init__.py** — prompt — prompt-engineering capability (Spec 109).

Two-lineage capability:

1. (3 symbols)
- **_main.py** — prompt — prompt-engineering substrate (Spec 109 · 129 · 304-306).

Author research dossiers, engineer token-budgeted prompts, route a draft to the
right one of 27 research-backed frameworks, and score prompts — and agency's own
functional docs — for clarity and anti-patterns. (10 symbols)
- **ontology.py** — prompt ontology — Spec 109 consolidated OntologyExtension. (16 symbols)

### `agency/capabilities/prompt/clusters/` (9 files)
- **__init__.py** — prompt.clusters — cluster mixins composed into the single PromptCapability.

Spec 286 P3 — the ~932-line ``prompt`` god-class split into one mixin per
section grouping. (9 symbols)
- **_base.py** — prompt.clusters._base — shared PromptCapability infrastructure (Spec 286 P3).

The token-approximation primitive + clarity-scoring heuristic + the
doctrine-tunable budgets, extracted verbatim from ``prompt/_main.py`` into a
base module every cluster mixin imports. (11 symbols)
- **_profiles.py** — prompt.clusters._profiles — goal-aware evaluation profiles (Spec 305/306).

``evaluate`` scores a prompt body against a criteria PROFILE selected by its
TARGET. (34 symbols)
- **assembly.py** — prompt.assembly — Dynamic prompt assembly (Spec 127).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Walks the graph for a Scene (or Chapter) and composes a bounded prompt with
sourced provenance. (21 symbols)
- **dossier.py** — prompt.dossier — Research-dossier lineage (Spec 109 Slice 1). (12 symbols)
- **engineering.py** — prompt.engineering — Prompt-engineering lineage (Spec 109 Slice 1). (9 symbols)
- **fragments.py** — prompt.fragments — Dramatica-as-prompt-fragments (Spec 129).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Each Dramatica ontology entry can carry a guidance fragment (second-person
agent imperative). (20 symbols)
- **frameworks.py** — prompt.frameworks — the 27-framework library, first-class (Spec 304).

prompt-architect (ckelsoe, MIT) ships 27 research-backed prompt-engineering
frameworks across 7 intent categories. (34 symbols)
- **gates.py** — prompt.gates — composite gate verbs (Spec 109 Slice 1).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

The 2 composite gate verbs called by walkable skills: token_budget_gate +
audit_gate. (7 symbols)

### `agency/capabilities/recommend/` (2 files)
- **__init__.py** — recommend — request → capability routing, first-class (Spec 298). (2 symbols)
- **_main.py** — recommend — request → capability routing, first-class (Spec 298).

A native reimplementation of SuperClaude's `sc-recommend`: given a free-text
request, recommend the most suitable agency capability + verb to use. (12 symbols)

### `agency/capabilities/reflect/` (2 files)
- **__init__.py** — reflect — durable, scope-tagged cross-session memory.

Folder-form per Spec 060 §Phase 3 — promoted from `reflect.py` so the
capability can ship its own `templates/` + `schemas/`. (2 symbols)
- **_main.py** — reflect — durable, scope-tagged cross-session memory. (11 symbols)

### `agency/capabilities/research/` (7 files)
- **__init__.py** — research — graph-native lead + specialists + verifier (Spec 044).

Folder-form capability. (3 symbols)
- **_findings.py** — Helper utilities reused across research lead / specialist / verify. (3 symbols)
- **_lead.py** — research.lead — scope the question + plan specialists.

Pure planner. (3 symbols)
- **_main.py** — research — lead + specialists + verifier (Spec 044). (21 symbols)
- **_specialist.py** — research.specialist — one bounded sub-search per role.

Three roles ship in v1:
  codebase         — grep + AST walk over the repo (confidence 1.0)
  prior-reflections — reflect.recall_semantic (confidence = score)
  doc-corpus       — keyword + semantic match over docs/ (confidence = score)

The `web` role is reserved (Spec 044 line 102) but defers to v2 when
the WebSearchClient injector is non-None. (12 symbols)
- **_verify.py** — research.verify — adversarial citation check. (11 symbols)
- **_web.py** — Web-search boundary driver (Spec 044 + Spec 052).

Two shipped backends:
  DuckDuckGoClient — zero-config default. (11 symbols)

### `agency/capabilities/select/` (2 files)
- **__init__.py** — select — complexity-scored approach selection (Spec 296). (2 symbols)
- **_main.py** — select — complexity-scored approach selection, first-class (Spec 296).

A native, generalized reimplementation of SuperClaude's `sc-select-tool`: score
an operation's complexity and route it to the right approach archetype —
`semantic` (structure-aware, accurate), `pattern` (fast bulk edits), or `native`
(safe default). (13 symbols)

### `agency/capabilities/shell/` (2 files)
- **__init__.py** — shell — a token-efficient, recorded, templated host-command boundary (Spec 073).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4. (2 symbols)
- **_main.py** — shell — a token-efficient, recorded, templated host-command boundary (Spec 073). (26 symbols)

### `agency/capabilities/skill_generator/` (2 files)
- **__init__.py** — skill_generator — generate a deploy-ready skill in one call. (2 symbols)
- **_main.py** — skill_generator — author a deploy-ready skill, grounded in real code. (18 symbols)

### `agency/capabilities/skills/` (2 files)
- **__init__.py** — skills — the first-class registry over every capability's walkable skills (Spec 026).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4. (2 symbols)
- **_main.py** — skills — the first-class registry over every capability's walkable skills (Spec 026). (22 symbols)

### `agency/capabilities/subagent/` (2 files)
- **__init__.py** — subagent — subagent-driven-development as a composition. (2 symbols)
- **_main.py** — subagent — subagent-driven-development as a composition. (6 symbols)

### `agency/capabilities/symbols/` (2 files)
- **__init__.py** — symbols — token-efficient symbol compression (Spec 300). (2 symbols)
- **_main.py** — symbols — token-efficient symbol compression, first-class (Spec 300). (11 symbols)

### `agency/capabilities/thinking/` (2 files)
- **__init__.py** — thinking — critical-thinking capability (Spec 110).

Eight founding methods + new ones for adversarial review (red-team) and
recursive questioning (socratic). (3 symbols)
- **_main.py** — thinking — critical-thinking capability (Spec 110 Slice 1).

10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite
(apply_full_review) + 1 walkable skill (critical-thinking).

Each method is a transform: returns a structured scaffold the agent fills
out. (21 symbols)

### `agency/capabilities/toolcalls/` (3 files)
- **__init__.py** — toolcalls — the ephemeral tool-call capture surface (Spec 336). (2 symbols)
- **_export.py** — Spec 336 S4 — distil the ephemeral tool-call capture into a durable export. (8 symbols)
- **_main.py** — toolcalls — the ephemeral tool-call capture surface (Spec 336).

Every pre/post tool call (Bash/Read/Edit/…) is captured in FULL into a local,
gitignored `.agency/toolcalls.db` — OFF the durable provenance graph, so the graph
stays the moat (Intents/Invocations/Gates) while **no capture data is lost**
(Spec 336 S2). (10 symbols)

### `agency/capabilities/workflow/` (3 files)
- **__init__.py** — workflow — the repo-development lifecycle (Spec 357). (3 symbols)
- **_main.py** — workflow — the repo-development lifecycle: specs as first-class Lifecycles.

Use when: a spec must move through its development stages (draft → open →
inprogress → done, or superseded) as a TRACKED, queryable Lifecycle — not a
hand-edited status field. (18 symbols)
- **ontology.py** — workflow ontology — the spec-state Lifecycle binding (Spec 357).

No new node label: a spec's state IS a ``Lifecycle`` on the Spec 345 ``spec``
machine (states draft → open → inprogress → done, + superseded). (6 symbols)

### `agency/capabilities/workspace/` (2 files)
- **__init__.py** — workspace — isolate work in a git worktree + record a green baseline. (2 symbols)
- **_main.py** — workspace — isolate work in a git worktree + record a green baseline. (8 symbols)

### `agency/render/` (1 files)
- **__init__.py** — Spec 032 §H — engine-owned template files. (1 symbols)

### `docs/examples/` (2 files)
- **author_a_plugin.py** — Example: author a tiny Claude Code plugin with the agency engine.

Walks the `plugin-dev` skill one phase at a time (progressive disclosure). (7 symbols)
- **pressure_test_a_skill.py** — Example: pressure-test a discipline skill (Spec 011, dry-run walk).

Subagent pressure-tests ask whether a discipline skill actually changes a fresh
agent's behaviour under pressure — or whether the agent rationalises it away. (7 symbols)

### `examples/` (3 files)
- **__init__.py** — Example out-of-tree extensions for the agency engine.

These are NOT part of the core plugin. (1 symbols)
- **music.py** — DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music graduated from ``examples/`` into ``agency/capabilities/music/`` as a
first-class folder-form capability. (6 symbols)
- **music_drivers.py** — DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music drivers graduated from ``examples/music_drivers.py`` into
``agency/capabilities/music/drivers.py`` as part of the Spec 094
migration. (4 symbols)

### `scripts/` (13 files)
- **__init__.py** — Helper scripts (Spec 054 drift-management, Spec 149 derived-doc discipline,
Spec 053 test-suite slicing). (1 symbols)
- **check_architecture.py** — Spec 157 Slice 1 — typed ArchitectureReport + wire-verb invariant audit.

Spec 019 commits to EXACTLY three wire verbs at the engine boundary
(`search` / `get_schema` / `execute`); every capability verb is reached
THROUGH them, never alongside. (10 symbols)
- **check_codes_coverage.py** — Spec 151 — Codes-coverage CLI shim.

The audit core moved to :mod:`agency._codes_coverage` (Spec 151 Slice 3) so
the engine can import it without the dev-only ``scripts/`` tree. (5 symbols)
- **check_collect_callers.py** — Spec 159 Slice 1 — derived audit of `dogfood.collect` callers.

Spec 150 closed the dogfood-loop pipeline (Slices 1+2: parse_amendment +
apply_amendment shipped). (12 symbols)
- **check_response_prefix.py** — Spec 146 Slice 2 — `_check_response_prefix` AST lint rule.

Spec 146 Slice 1 shipped the typed `ResponseEnvelope(prefix, body)` split
+ `agency_welcome` wired through it. (78 symbols)
- **check_scaffold_markers.py** — Spec 158 Slice 1 — capability scaffold-marker presence audit.

Walks `agency/capabilities/*` and reports which capabilities carry the
`# agency-scaffold: v1` marker on their main file. (16 symbols)
- **check_schema_coverage.py** — Spec 153 — schema-coverage CLI shim.

The audit core moved to :mod:`agency._schema_coverage` (Spec 153 Slice 3)
so the engine can import it without the dev-only ``scripts/`` tree. (5 symbols)
- **check_vision_goals.py** — Spec 149 Slice 1 — `vision_goals:` frontmatter validator.

The drift-derivation chain anchor (`Plan/_planning/charter.md`) wants every spec
to declare its Vision-goal mapping in frontmatter so the alignment matrix
(Spec 191), per-spec Followup (Spec 269), and closing audit (Spec 261) can
all derive from one source. (23 symbols)
- **derive_docs.py** — Spec 149 Slice 2 — `derive-docs` core derivation library.

Spec 149 Slice 1 shipped the `vision_goals:` frontmatter validator + 129-
spec baseline. (29 symbols)
- **followup_derive.py** — Spec 269 — per-spec Followup Implementation Status: derived FollowupBlock.

Per CLAUDE.md rule 4 the per-spec deep state lives in each spec.md's
`## Followup — Implementation Status` section. (24 symbols)
- **gen-living-spec.py** — Phase B — generate a capability-indexed *living spec* from the REFACTORED code.

Rule 2 applied to specs: the spec's generated sections (Verbs / Ontology /
Skills) are DERIVED from the live registry, never hand-maintained — re-run to
refresh. (13 symbols)
- **mcp_wire_smoke.py** — Drive the agency MCP server over stdio with raw JSON-RPC. (11 symbols)
- **vision_matrix.py** — Spec 191 — live vision-alignment matrix derivation.

Spec 072 produced the SPEC-VISION-ALIGNMENT matrix by hand; it goes stale
the first time a spec ships. (33 symbols)

### `tests/` (19 files)
- **conftest.py** — Spec 016 v2 Phase 5 — shared engine/iid fixtures.

Eliminates the 13 duplicate fixture blocks the test suite carried
(claim verified verbatim by survey a7e6bd1) and removes a latent bug:
the legacy duplicates used `tempfile.mktemp(suffix=".db")` which is
deprecated since Python 2 (race condition — the predicted path isn't
guaranteed unique). (13 symbols)
- **test__research_citation.py** (8 symbols)
- **test_analyze_subprocess_analyzer.py** — Spec 286 — the shared SubprocessAnalyzer template scaffold. (21 symbols)
- **test_cli_chain_fields.py** (13 symbols)
- **test_develop_plan_execute.py** — Spec 287 — develop `plan-execute` discipline + Plan/PlanStep provenance.

A first-class plan-authoring → execution-with-checkpoints discipline
(superpowers writing-plans + executing-plans + subagent-driven-development;
superclaude sc-workflow + sc-task). (10 symbols)
- **test_durable_writes.py** — Spec 282 Workstream C — durable batch writes.

Evidence (kohaerenzprotokoll): 97 NarrativeBeat nodes, only 12 PRECEDES edges.
Two distinct engine-side defects this guards against:

1. (13 symbols)
- **test_entities.py** — Spec 289 Slice 1 — SQLModel entity models derived from the graph ontology. (9 symbols)
- **test_entity_store.py** — Spec 289 Slice 2 — the canonical SQLite-backed entity store. (8 symbols)
- **test_entity_store_mirror.py** — Spec 289 Slice 2b — Memory mirrors authoritative graph writes into the
graph-authoritative typed projection (EntityStore).

The invariant: the graph node stays write-authoritative; the entity row is a
ONE-WAY derived mirror keyed by node id. (12 symbols)
- **test_error_severity.py** — Spec 282 — error severity taxonomy.

Replays the exact failure scenarios mined from
``kohaerenzprotokoll/.agency/session.db`` (1952 invocations, 626 failed):
``create_scene`` rejected 513× on a closed ``pov`` enum (PERMANENT — never
succeeds) versus the known ``Failed to set property 'vfrom' on edge N``
contention (TRANSIENT — retry helps). (30 symbols)
- **test_host_bridge.py** — Spec 285 Slice 1 — HostBridge seam (sampling + elicitation boundary). (50 symbols)
- **test_install_hint.py** (5 symbols)
- **test_lifecycle_resume.py** (4 symbols)
- **test_novel_storyform_node.py** — Spec 103 Slice 2 (Workstream D) — create_storyform / get_storyform.

Closes the documented ENGINE GAP: the storyform gates + checks read a
`Storyform` node, but no verb minted one. (13 symbols)
- **test_projected_enum.py** — Spec 284 — projected-enum substrate. (19 symbols)
- **test_render_driver_substrate.py** — Spec 283 Slice 1 (Workstream F) — capability render substrate. (20 symbols)
- **test_session_snapshot.py** — Session-graph snapshot export/import — round-trip + value-only (Spec follow-up). (5 symbols)
- **test_skill_emit.py** (10 symbols)
- **test_skill_walk_part_b.py** — Spec 285 Slice 1 Part B — walk-level sampling + enforced assumption-gate. (29 symbols)

### `tests/acceptance/` (133 files)
- **conftest.py** — Shared fixtures + helpers for the Gherkin acceptance suite.

Phase C — the flat `tests/test_*.py` are converted into behaviour scenarios
here (owner directive). (16 symbols)
- **test_acceptance.py** — Acceptance — core engine behaviours: the code-mode wire contract, provenance
(the moat), and the capability surface. (22 symbols)
- **test_adr.py** — Acceptance — ADR ontology + capability, author & validate (Spec 354 Slice 1). (43 symbols)
- **test_adr_dod.py** — Acceptance — ADR Definition-of-Done gate (Spec 355 Slice 1). (23 symbols)
- **test_adr_extract.py** — Acceptance — ADR spec→decision extraction + ready predicate (Spec 356 Slice 1). (26 symbols)
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
    acceptance). (83 symbols)
- **test_branch.py** — Acceptance — branch capability (Spec 046).

Converted from tests/test_branch*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- _infer_commit_type and _infer_scope private function internals
- The VCS client itself (real subprocess boundary)

GAPS: branch.assess and branch.finish with a REAL git repository are external
effects. (42 symbols)
- **test_brooks_lint.py** — Acceptance — Brooks-lint conceptual-integrity pass (Spec 359). (14 symbols)
- **test_capability_skill_migration.py** — Acceptance — capability skill migration (Spec 378 Slice 1, frugal A6 + phase-fill).

The core develop disciplines gain real inline phase `instructions` (A1), validated
the same as any skill (the schema doesn't care whether the data is auto-derived or
capability-authored — A6). (17 symbols)
- **test_codes_coverage.py** — Acceptance — codes-coverage audit behaviour (Spec 151).

Grounds the Slice 2 gate that `.github/workflows/test.yml` runs (`--baseline
--strict`). (19 symbols)
- **test_command_v2.py** — Acceptance — Command v2 (Spec 376).

The generated `/agency-<slug>` commands are CURATED: one per discipline + one per
pillar, NOT a top-N alpha cap. (21 symbols)
- **test_config.py** — Acceptance — unified config resolver + registry (Spec 334 Slice 1).

Behaviour: a registered key resolves env > file > default; config_set persists;
registered sections appear in the live set. (30 symbols)
- **test_config_capability.py** — Acceptance — user-facing config capability (Spec 334 Slice 8).

Behaviour: get / set / list verbs over the unified config, driven through the
real Engine registry (records provenance like any verb). (16 symbols)
- **test_config_doctor.py** — Acceptance — unified config doctor (Spec 334 Slice 4). (17 symbols)
- **test_config_readpath.py** — Acceptance — unified config read-path unification (Spec 334 Slice 6).

Behaviour: a capability's own `*.load()` consults the unified `config_get`
as a live-but-lowest-priority source. (18 symbols)
- **test_config_wiring.py** — Acceptance — unified config wiring (Spec 334 Slice 3).

The three zero-manual-step generation points: `agency install` (here:
`install.scaffold_agency_dir`) creates the annotated config; the SessionStart
hook REPAIRS an existing one non-destructively but never creates one in an
arbitrary cwd. (18 symbols)
- **test_context_neighbors.py** — Acceptance — CapabilityContext.neighbors() one-hop edge traversal (Spec 125).

Converted from tests/test_context_neighbors.py. (23 symbols)
- **test_decay_risk.py** — Acceptance — decay-risk Finding shape + decay knowledge (Spec 354).

The foundation slice of the Spec 353 brooks-lint port: the Finding value object
learns the Iron Law (Symptom → Source → Consequence → Remedy) and a derived
severity tier, the twelve decay risks are vendored as cited data, and the
decidable findings analyze already produces are tagged with the risk code + book
source they evidence. (42 symbols)
- **test_delegate.py** — Acceptance — delegate capability (Spec 040/041). (60 symbols)
- **test_derive_docs.py** — Acceptance — derive-docs fence rewrite (Spec 149 Slice 2.2).

Tests the HTML-comment fence mechanism:
  <!-- derived:<id> --> ... (34 symbols)
- **test_develop.py** — Acceptance — develop capability: scaffolding, linting, authoring discipline
walk, discipline cues for intent methods. (88 symbols)
- **test_develop_maintain.py** — Acceptance — develop.maintain: the autolearning recurring-maintenance loop. (19 symbols)
- **test_discover.py** — Acceptance — discover capability scaffold (Spec 308).

Behaviour: the drop-in shell is discoverable, registers the locked Spec 307
ontology surface, reuses research's Citation, and derives its Agent Skill —
all from adding one folder. (13 symbols)
- **test_discover_acceptance.py** — Acceptance — discover.acceptance, Gherkin criteria derivation (Spec 317). (10 symbols)
- **test_discover_ask.py** — Acceptance — discover.ask, the well-formed AskUser primitive (Spec 310). (21 symbols)
- **test_discover_clarify.py** — Acceptance — discover.clarify, the ambiguity-resolution loop (Spec 311). (14 symbols)
- **test_discover_clarity.py** — Acceptance — discover.clarity, the Intent readiness score (Spec 322). (23 symbols)
- **test_discover_interview.py** — Acceptance — discover.interview, the adaptive elicitation engine (Spec 309). (12 symbols)
- **test_discover_scope.py** — Acceptance — discover.scope, in/out boundary elicitation (Spec 318). (12 symbols)
- **test_dispatch_decision_extended.py** — Acceptance — extended dispatch_decision signals S1, S6, S7, S8 (Spec 040).

Converted from tests/test_dispatch_decision_extended.py (behaviour: the new
seven signals and the full eleven-signal payload). (17 symbols)
- **test_doctrine.py** — Acceptance — doctrine capability: queryable principles + rules (Spec 303). (18 symbols)
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
    (covered in analyze acceptance). (133 symbols)
- **test_dogfood.py** — Acceptance — dogfood capability: graph-native ledgers, export/import,
amendment pipeline. (156 symbols)
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
- test_guard_typed_shape / test_capability_row_typed_shape / etc. (74 symbols)
- **test_events.py** — Acceptance — the pillar event bus's declarative subscriptions (Spec 349b §2).

A capability declares `subscriptions = [Subscription(...)]`; the engine bootstrap
loop reads them and registers each handler on `agency/_events.py`. (14 symbols)
- **test_fidelity.py** — Acceptance — no-truncate-or-paginate data fidelity (Spec 336 S1).

Behaviour: `paginate` returns one page + a read-continuation cursor + instruction,
and walking the cursor reconstructs the COMPLETE set — the tail is reachable, never
truncated. (12 symbols)
- **test_followup_derive.py** — Acceptance — per-spec Followup derived metrics (Spec 269).

The FollowupBlock's metrics are COMPUTED (test_count from affects+collection,
Done-When ratio parsed from the spec body, recent_commits from git log, status
from frontmatter) — never hand-pinned. (29 symbols)
- **test_frugal.py** — Acceptance — frugal core discipline level + render (Spec 332 Slice 1). (28 symbols)
- **test_frugal_capability.py** — Acceptance — frugal capability (Spec 348 Slice 1, the ponytail port).

Behaviour: the discipline is a discoverable capability whose verbs wrap the core
_frugal module — read/switch the level, pull the ruleset (the MCP port), show the
help card. (64 symbols)
- **test_frugal_embedded.py** — Acceptance — Frugal embedded in lifecycle (Spec 347). (20 symbols)
- **test_frugal_floor.py** — Acceptance — frugal safety-floor gate (Spec 332 Slice 4).

`_frugal.safety_floor_intact()` is a decidable predicate: at every level but off
the FULL render carries every safety-floor marker and the COMPACT render names
the floor. (14 symbols)
- **test_frugal_stamp.py** — Acceptance — frugal M2 per-verb envelope stamp (Spec 332 Slice 2).

Every capability verb's wire return carries a byte-stable compact frugal stamp
(via engine._shape_wire_result); off omits it; agency_welcome carries it in its
cache-stable prefix. (21 symbols)
- **test_gate.py** — Acceptance — gate capability + gate predicates (Spec 011). (34 symbols)
- **test_guided_discovery_skill.py** — Acceptance — guided-discovery discipline skill registration (Spec 322 Slice 3). (14 symbols)
- **test_health_score.py** — Acceptance — Spec 381: Health Score (computed, preset-weighted).

Behaviour-only: the score is asserted as a RELATIONSHIP across presets and a
computed value from live findings (rule 8 — never a pinned snapshot). (14 symbols)
- **test_hooks.py** — Acceptance — hook dispatch, BoundaryUse, foreign-hook install (Spec 076 / 195 / 280). (91 symbols)
- **test_implicit_intent.py** — Acceptance — implicit intent_id via AGENCY_INTENT env var (Spec 018 Win 3).

Converted from tests/test_implicit_intent.py. (20 symbols)
- **test_install.py** — Acceptance — install pipeline (Spec 029/031/032/062/064/065/092). (72 symbols)
- **test_installer.py** — Acceptance — multi-agent self-installer (Spec 333).

surface_card → per-agent adapters (compact projection: frugal discipline + entry
pointers, NOT the full verb index); idempotent fenced-block merge; per-adapter
report; uninstall removes only the block. (35 symbols)
- **test_intent.py** — Acceptance — intent capability: critical-thinking methods, chaining,
owners, path analysis, and skill projection. (70 symbols)
- **test_jules.py** — Acceptance — jules capability.

Converted from tests/test_jules*.py (~17 files). (136 symbols)
- **test_lifecycle.py** — Acceptance — Lifecycle pillar substrate (Spec 339).

Behaviour of the hardened `agency/lifecycle.py` substrate write frame:
`open` mints `submitted`, `move` is the sole state-shaped writer that validates
the target state + refuses a no-op, `close` drives to a terminal state. (47 symbols)
- **test_lifecycle_generic_sm.py** — Acceptance — Lifecycle generic state machine (Spec 345).

The lifecycle substrate accepts a named machine parameter; A2A is the default
(backward-compatible). (21 symbols)
- **test_lifecycle_management.py** — Acceptance — the lifecycle-management discipline + resume + board (Spec 343). (21 symbols)
- **test_lifecycle_observe.py** — Acceptance — the Lifecycle observe frame (Spec 341), REUSED on `manage`. (21 symbols)
- **test_lifecycle_parameterization.py** — Acceptance — Agent as a Lifecycle parameterization (Spec 342).

An agent IS a Lifecycle parameterization: a named machine variant (Spec 345)
whose transitions insert an observer state (verify / in-review) so
COMPLETED != done. (42 symbols)
- **test_loop_advance.py** — Acceptance — the loop walk reducer (Spec 366 advance, looper run() on the spine).

advance() reads the machine state, runs the gate (criteria 364 + council verdict
365), consults control_evaluate, then moves via the lifecycle pillar (the sole
state writer). (25 symbols)
- **test_loop_capability.py** — Acceptance — the loop capability (Spec 387 W1): reachable + provenance-recording.

The dormant-surface audit as a STANDING test: the looper port's verbs are on the
wire surface, schema'd, and record an `Invocation` when invoked — the moat the
bare spine functions (363-369) bypassed. (10 symbols)
- **test_loop_control.py** — Acceptance — the loop termination evaluator (Spec 366; ported from looper). (7 symbols)
- **test_loop_council.py** — Acceptance — the loop council (Spec 365, looper port on the lifecycle spine).

A council member is a reviewer (notes) or a judge (a gating verdict) bound to a
model family — reuse of persona (297) + panel (294), stored on the loop as the
spine interim. (19 symbols)
- **test_loop_emit.py** — Acceptance — loop spec + emission (Spec 368, graph → portable artefacts).

compile() projects the spine loop into looper's loop.resolved.json shape (the
same contract the ported runner reads); emit() renders the portable workspace as
anchored documents. (19 symbols)
- **test_loop_events.py** — Acceptance — loop detection middleware and typed LoopEvent (Spec 011 / 156). (34 symbols)
- **test_loop_goal.py** — Acceptance — loop goal coaching (Spec 363; frame_goal / critique_goal). (22 symbols)
- **test_loop_machine.py** — Acceptance — the loop machine (Spec 366, looper port on the lifecycle spine).

The looper port registers a "loop" state machine in machines.json (the Spec 345
data-seam). (17 symbols)
- **test_loop_open.py** — Acceptance — opening a loop (Spec 366; _loop.open). (15 symbols)
- **test_loop_runner.py** — Acceptance — loop external runner, model detection & egress (Spec 369).

The out-of-session twin: model detection (metadata only, secret-free), the ported
stdlib run-loop.py, and the egress-consent gate (cross-vendor consent + redaction)
for both surfaces. (26 symbols)
- **test_loop_verify.py** — Acceptance — loop verification as typed gates (Spec 364). (22 symbols)
- **test_loop_wizard.py** — Acceptance — the loop-design wizard (Spec 367, looper's interview as a skill).

The 7-stage interview is a walkable skill registered into the develop ontology
(no new capability). (26 symbols)
- **test_manage.py** — Acceptance — manage capability: generic CRUD (Spec 293). (39 symbols)
- **test_mode.py** — Acceptance — mode capability (Spec 295). (14 symbols)
- **test_music.py** — Acceptance — music capability (all clusters).

Converted from tests/test_music*.py (~11 files). (279 symbols)
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
   engine monkeypatching. (308 symbols)
- **test_output_overflow.py** — Acceptance — output overflow capture and recall (Spec 154 Slice 1).

Converted from tests/test_output_overflow.py. (31 symbols)
- **test_panel.py** — Acceptance — panel capability (Spec 294). (15 symbols)
- **test_persona.py** — Acceptance — persona capability (Spec 297). (13 symbols)
- **test_pillar_skills.py** — Acceptance — pillar skills (Spec 375 Slice 1).

The three concept pillars (intent · lifecycle · memory) are committed `skill.yaml`
of `type: pillar`, loaded by `agency._pillars.load_pillars`, validated against the
371 schema, and rendered by `install.generate`. (26 symbols)
- **test_plugin_authoring.py** — Acceptance — plugin authoring behaviour. (65 symbols)
- **test_prompt.py** — Acceptance — prompt capability (Spec 109/127/129). (133 symbols)
- **test_quality_chain.py** — Acceptance — Spec 380 §judgment: the subagent walks the Brooks review chain.

The judgment subagent is driven by the vendored, mode-aware Brooks REVIEW CHAIN
(the ordered review methodology), not a flat risk-dump. (20 symbols)
- **test_quality_config.py** — Acceptance — Spec 381 §2: quality config block (tunability + validation).

Behaviour-only: the config filters findings before scoring and surfaces
validation notes (never fatal). (14 symbols)
- **test_quality_corpus.py** — Acceptance — Spec 383 Slice 2: the paired decidable corpus + coverage matrix.

Grounds every DECIDABLE decay risk (R1/R4/R5 — those with a `decidable` rule-id
mapping) with a positive fixture (the symptom IS flagged with the right risk +
Iron Law) and a negative "What Not to Flag" fixture (the symptom-shaped-but-
legitimate case is NOT flagged — the load-bearing half). (16 symbols)
- **test_quality_coverage.py** — Acceptance — Spec 383: source-coverage grounding + SARIF property test. (18 symbols)
- **test_quality_gate.py** — Acceptance — Spec 382 §2/§3: the quality CI gate. (15 symbols)
- **test_quality_judgment.py** — Acceptance — Spec 380 §judgment: the LLM judgment pass (the wet-corpus unblock).

The judgment pass produces the reasoning-heavy decay findings (R2/R3/R6/T1–T6)
the decidable scanners cannot. (18 symbols)
- **test_quality_migration.py** — Acceptance — Spec 385: brooks-lint sidecars → agency quality surface. (8 symbols)
- **test_quality_report.py** — Acceptance — Spec 382 §4: the Iron-Law report render path.

Behaviour-only: the report projects structured findings — sorted by tier, each as
the Iron Law block, empty tiers omitted, mermaid in audit mode only. (12 symbols)
- **test_quality_report_render.py** — Acceptance — Spec 384 close-out: the report-render verb (analyze.report).

Closes 384's flagship scenario — the quality report RENDERS from the ported
templates (quality-report.md + iron-law-finding.md) rather than a print, and is a
round-trippable Document graph node (Spec 292). (6 symbols)
- **test_quality_review.py** — Acceptance — Spec 380: six quality modes + develop.review seam.

Behaviour-only: assert what the verbs and pure functions DO (roles, phase structure,
return shapes, Iron Law gate predicate, merge contract). (43 symbols)
- **test_quality_review_approval.py** — Acceptance — Spec 380 develop.review: subagent judgment + final approval elicit.

The interactive review runs the judgment pass (fulfilled by a SUBAGENT — no
external LLM) and then ELICITS the human to approve/reject the LLM-proposed
judgment findings before they merge. (24 symbols)
- **test_quality_run.py** — Acceptance — Spec 381 §3: QualityRun history graph node + trend.

Behaviour-only: a run is a graph node (not a sidecar file); the trend is a query
that reads only prior COMPLETE same-mode runs. (15 symbols)
- **test_quality_sarif.py** — Acceptance — Spec 382 §1: SARIF emit from structured findings.

Behaviour-only: SARIF validity + the rule set DERIVED from the live registry
(rule 8 — never pinned) + the truncation locator. (18 symbols)
- **test_quality_templates.py** — Acceptance — Spec 384: brooks prose → agency templates + references.

The prose half of the Spec 379 port lands on agency's template doctrine (Spec 060
`<!-- AGENT: -->` render assets) + the on-demand reference surface
(`develop.reference`). (18 symbols)
- **test_quality_triage.py** — Acceptance — Spec 381 §4: triage (suppression + acknowledgement). (20 symbols)
- **test_quality_wet.py** — Acceptance — Spec 383 Slice 2b: the brooks JUDGMENT corpus (`-m wet`).

The decidable risks have a paired fixture corpus (quality_corpus.feature). (8 symbols)
- **test_recommend.py** — Acceptance — recommend capability (Spec 298). (10 symbols)
- **test_reflect.py** — Acceptance — reflect (semantic recall). (11 symbols)
- **test_relevance.py** — Acceptance — relevance filter (Spec 350 Slices 1, 2, and 3). (64 symbols)
- **test_reload.py** — Acceptance — agency_reload: mid-session capability reload (Spec 302 Slice 2). (13 symbols)
- **test_render_substrate.py** — Acceptance — render substrate and response envelope (Spec 023 / 146 / 154). (68 symbols)
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
    the three-check payload scenario). (92 symbols)
- **test_search_isomorphism.py** — Acceptance — MCP/CLI search isomorphism (Spec 023 §F3.1).

Converted from tests/test_search_isomorphism.py. (13 symbols)
- **test_select.py** — Acceptance — select capability (Spec 296). (14 symbols)
- **test_session_driver.py** — Acceptance — session driver verbs (Spec 114).

Converted from tests/test_session_driver.py. (29 symbols)
- **test_shell.py** — Acceptance — shell capability (Spec 073/075). (57 symbols)
- **test_skill_author.py** — Acceptance — skill authoring grounding context (Spec 374 Slice 1).

The grounding builder (`skill_generator.ground`) reads a capability's live
surface — verbs, signatures (sans injected params), docstrings, ontology — into
a structured dict. (38 symbols)
- **test_skill_call_examples.py** — Acceptance — Spec 390: generated skills teach the CALL (code-mode examples).

A fresh agent following a SKILL.md must learn not just WHEN to use a capability
but HOW to call it through the MCP — the prefixed `capability_<cap>_<verb>` wire
name, threaded with the serving `intent_id`, inside a code-mode block. (6 symbols)
- **test_skill_generator.py** — Acceptance — skill_generator capability: author + lint a SKILL.md (Spec 028). (10 symbols)
- **test_skill_lint.py** — Acceptance — strict skill-schema lint (Spec 377 Slice 1).

`plugin.lint_skill_schema` validates a 371 Skill dict against the strict contract
(per-type completeness, R1 trigger, self-containment, no-stub, verb-resolves). (15 symbols)
- **test_skill_load.py** — Acceptance — load_skill + skill_source (Spec 371 Slices 2-3).

A capability's v2 Skill DERIVES from its docstring SkillDoc (the back-compat
shim, owner=auto) unless the capability SHIPS a `skill.yaml` (the A6 authored
override, owner=capability). (13 symbols)
- **test_skill_phase_parse.py** — Acceptance — Skill/Phase parse boundary behaviour.

Converted from:
  tests/test_skill_phase_parse.py  (Spec 152 — typed parse_skill / parse_phase)

Dropped as implementation/structural (not observable behaviour):
  test_skill_walk_slices.py — render_phase / render_verb output format tests
    (T1/T2/T3 depth slices, snippet call_tool syntax, fallback text) are
    internal disclosure-helper details. (36 symbols)
- **test_skill_render_v2.py** — Acceptance — per-type skill rendering (Spec 373).

`render_typed_skill` is the ONE renderer: it selects `render/skill/<type>.md` by
the Skill's `type` and inlines the schema-driven data body (overview / when-to-use
/ example / common-mistakes / references) self-contained (A1). (15 symbols)
- **test_skill_schema_v2.py** — Acceptance — Skill schema v2 (Spec 371): the layered, type-classified
Phase + Skill data model.

The v2 schema is what 372–378 consume. (28 symbols)
- **test_skill_walk.py** — Acceptance — skill walk behaviour. (33 symbols)
- **test_skills_registry.py** — Acceptance — skills registry behaviour.

Converted from:
  tests/test_skills_index.py        (Spec 026 — skills.index graph promotion)
  tests/test_skill_first_discovery.py (Spec 025 — skill tag wiring on verbs)
  tests/test_skills_matcher_result.py (Spec 162 — MatcherResult typed shape)

Dropped as implementation/structural (not observable behaviour):
  test_skills_api_binding.py — verifies the Anthropic Python SDK signature;
    depends on [publish] extra that CI doesn't install. (29 symbols)
- **test_spec_done_cascade.py** — Acceptance — finish_spec, the done-cascade trigger (Spec 388).

`workflow.finish_spec` moves a spec to /done across all three state
representations (folder + frontmatter + node) in one call. (11 symbols)
- **test_spec_state.py** — Acceptance — spec-state lifecycle (Spec 357): specs as Lifecycles. (22 symbols)
- **test_subagent.py** — Acceptance — subagent capability (Spec 041). (18 symbols)
- **test_surface_resolution.py** — Acceptance — surface resolution (Spec 023 §F3.2).

Converted from tests/test_surface_resolution.py. (16 symbols)
- **test_symbols.py** — Acceptance — symbols capability (Spec 300). (11 symbols)
- **test_template_schema.py** — Acceptance — template and schema bootstrap/lint/coverage behaviour.

Converted from:
  tests/test_template_bootstrap_wireup.py (Spec 060 Phase 1 — bootstrap wire-up)
  tests/test_template_folder_lint.py      (Spec 060 Phase 4 — lint rule)
  tests/test_template_schema_coverage.py  (Spec 153 — coverage audit)

Dropped as implementation/structural (not observable behaviour):
  test_path_safety.py — exercises an internal helper `_safe_path` that
    validates path-traversal guards inside the template loader. (109 symbols)
- **test_thinking.py** — Acceptance — thinking capability: critical-thinking method scaffolds (Spec 110). (16 symbols)
- **test_token_budget.py** — Acceptance — token budget (Spec 023 / 082). (19 symbols)
- **test_token_count_api.py** — Acceptance — TokenCounter typed result + cache + band (Spec 201).

The authoritative `messages.count_tokens` backend already ships (Spec 082).
These scenarios guard Spec 201's additions, network-free via a forced proxy
counter: the typed `CountResult`, the per-(content, model) cache, and the
band-agreement helper. (20 symbols)
- **test_toolcalls.py** — Acceptance — the toolcalls capability (Spec 336 S2).

The clear, discoverable MCP surface over the ephemeral tool-call store: stats,
top (frequency ranking), and prune. (38 symbols)
- **test_typed_entities.py** — Acceptance — Spec 327: typed Intent + Capability core (the four-concept
interweave's load-bearing slice). (27 symbols)
- **test_typed_fulfilment.py** — Acceptance — Spec 328: typed Intent fulfilment (the Intent-owned Gate +
AcceptanceCriterion). (23 symbols)
- **test_typed_read_api.py** — Acceptance — Spec 330: the typed Intent read API (IntentStore) + parity gate. (21 symbols)
- **test_typed_spine.py** — Acceptance — Spec 329: typed Lifecycle state + the Memory provenance spine. (24 symbols)
- **test_vision_matrix.py** — Acceptance — live vision-alignment matrix (Spec 191).

The matrix is DERIVED from each spec's `vision_goals:` + `status:`
frontmatter (Spec 149), never hand-maintained. (34 symbols)
- **test_welcome.py** — Acceptance — agency_welcome (Spec 029 / 030). (38 symbols)
- **test_wet_generation.py** — Acceptance — use-case model selection + OpenRouter-first generation (Spec 352).

All selection logic is network-free. (68 symbols)
- **test_workflow_skill.py** — Acceptance — the develop-spec repo-development workflow (Spec 358). (20 symbols)
- **test_workspace.py** — Acceptance — workspace capability (Spec 002).

Converted from tests/test_workspace*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- VCS client internals (subprocess boundary)

GAPS: real git worktree creation requires a live git repository. (30 symbols)
