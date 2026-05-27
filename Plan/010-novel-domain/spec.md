---
spec_id: "010"
slug: novel-domain
status: draft
owner: "@agency"
depends_on: [001, 002, 003]
affects:
  - examples/novel.py
  - examples/novel/__init__.py
  - examples/novel/_layout.py
  - examples/novel/_dramatica.py
  - examples/novel/_ncp.py
  - examples/novel/_coherence.py
  - examples/novel/_prose.py
  - examples/novel/data/dramatica_ontology.json
  - examples/novel/data/ncp.schema.json
  - examples/__init__.py
  - docs/examples/author_a_novel.py
  - tests/test_novel_capability.py
  - tests/test_novel_coherence.py
  - tests/test_novel_skills.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 4
domain: novel
wave: 2
---

# Spec 010 — Novel Domain Capability

## Why

`the-agency-system` carries a deep, structurally-grounded novel domain: an on-disk
work layout (`novels/{author}/works/{genre}/{slug}/` with 7 root files + 7
subfolders, Plan 010), core CRUD handlers over works/chapters/scenes/characters
(Plan 011), a vendored Dramatica ontology (304 entries) + an NCP-v1.3.0
compiler/validator (Plan 012), 11 decidable structural-coherence checks (Plan
013), a 6-gate pre-drafting orchestrator + revision tracking (Plan 014), a 32-skill
catalogue (Plan 015), and a 10-builder prompt family (Plan 021). That is a whole
domain product expressed as MCP handlers + SKILL.md prose.

In **Agency** the same craft lands as ONE self-registering capability plus an
`OntologyExtension`. The contract is already in place: drop a module in
`agency/capabilities/` (or, for a domain, in `examples/` loaded via
`Engine(..., extra_capabilities=[…])`, exactly like `examples/music.py`), define a
`Capability` whose verbs are role-tagged `act`/`transform`/`effect`, carry the
node types / enums / skills / template-schemas the domain needs in
`Capability.ontology`, and the engine `discover()`s it, merges the ontology
strictly onto the core, and auto-wires one MCP tool per verb. The structural truth
(Dramatica/NCP) becomes `transform` verbs (decidable, no LLM); the editorial
pipeline becomes Lifecycle-template **skills** with hard gates; the pre-drafting
6-gate becomes a `gate.check` composition. **Code-mode IS the contract** — there is
no `novel_*` tool surface to maintain; the verbs are discovered via `search` and
called from inside `execute`.

This spec lands the novel domain as the second proof (after `music`) that a rich
external domain folds onto the four-concept substrate without bespoke wiring, and
the first proof that a domain can carry a non-trivial **vendored reference dataset**
(the Dramatica ontology) and a **schema-validation `transform`** (NCP) through the
`OntologyExtension` mechanism.

## Done When

- [ ] `examples/novel.py` defines a `NovelCapability(CapabilityBase)` with
  `name="novel"`, `home="capability"`, and an `OntologyExtension` that merges
  cleanly onto the core (`Engine(..., extra_capabilities=[NovelCapability.as_capability()])`
  raises no ontology-conflict error).
- [ ] The extension adds the node types `Work`, `Chapter`, `Scene`, `Character`,
  `Premise`, `Storyform`, `Coherence` with strict required-field schemas, the
  closed enums for `pov`, `revision_pass`, and `coherence_severity`, the editorial
  + conceptualizer + pre-drafting **skills** (Lifecycle templates), and the
  artefact schemas for `work`, `premise`, `ncp`, `coherence-report`,
  `scene-prompt`.
- [ ] The verb table (below) is implemented and role-tagged; every `act`/`effect`
  verb records provenance via `self.ctx` (Invocation `SERVES` intent, Artefacts
  `PRODUCES`d, Work/Coherence nodes recorded), and every `transform` verb is pure
  (no graph write, no disk write).
- [ ] `novel.scaffold(author, genre, slug, title)` (effect) records a `Work` node
  edged `SERVES` the intent and returns the 14-entry on-disk layout manifest (7
  root files + 7 subfolders) WITHOUT writing to disk unless `apply=True` —
  mirroring Agency's `dry_run` discipline through an explicit `apply` flag.
- [ ] `novel.coherence_check(storyform)` (transform) runs the 11 decidable checks
  against the vendored Dramatica ontology and returns the compact report shape
  `{status, violations:int, checks:{<11 keys>:{status, items?}}}`; a clean
  storyform serialises in ≤ 80 tokens (PASS checks carry no `items`).
- [ ] `novel.ncp_validate(doc)` (transform) validates a doc against the pinned
  NCP-v1.3.0 schema and returns `{ok, errors:[...]}`; it never raises on a
  malformed doc (only on unreadable input).
- [ ] `novel.dramatica_lookup(...)` (transform) resolves elements + checks
  dynamic-pair reciprocity against the 304-entry ontology bundled under
  `examples/novel/data/`.
- [ ] `novel.pre_drafting_gate(work_id, ...)` (act) composes `gate.check` for each
  of the 6 gates against the work's `Lifecycle`; `chapter` drafting is `done` only
  when all 6 PASS (a failing gate records a `BLOCKED_ON` edge + an
  `input-required` pause, exactly like `gate.check`).
- [ ] The conceptualizer skill `work-concept` ends in a **hard** confirm gate
  (mirrors `examples/music.py`'s `album-concept`); the editorial skill
  `manuscript-revision` walks structural → line → copy → proof passes with a hard
  final gate; the engine's skill walker can walk each one phase-at-a-time
  (progressive disclosure: `current()` returns only the active phase).
- [ ] `pytest -q tests/test_novel_capability.py tests/test_novel_coherence.py
  tests/test_novel_skills.py` passes; the existing suite (`pytest -q`) still
  passes (no regression to the 56 baseline).
- [ ] `python docs/examples/author_a_novel.py` runs end-to-end: scaffold a work →
  conceptualize (walk the gated skill) → validate NCP → coherence-check →
  pre-drafting-gate → build a scene prompt, printing the provenance subgraph for
  the intent.
- [ ] `docs/vision/CORE.md` is NOT modified by this spec — the domain proves the
  extension contract; it does not change the canon.

## Design

### Where it lives (core vs examples)

Per `agency/CLAUDE.md`: "Domain capabilities live OUT of the core as example
extensions in `examples/`." The novel domain follows `examples/music.py` exactly —
it ships under `examples/novel.py` (with a `examples/novel/` package for the
vendored data + the heavier helper modules), loaded via the engine's
`extra_capabilities` extension point. This keeps the self-bootstrapping harness
minimal while exercising the extension contract at a far higher fidelity than
`music` does (vendored dataset + schema validation + 11-check coherence engine + a
multi-skill editorial pipeline). See **Open Questions** for the core-vs-examples
decision record.

### OntologyExtension — node types, enums, skills, schemas

The capability OWNS this fragment; the engine merges it strictly onto the core
(`Ontology.extend`). Node schemas are the irreducible required fields enforced live
by `Memory.record`.

**Node types** (`nodes={label: [required_fields]}`):

| Node | Required fields | Notes |
|---|---|---|
| `Work` | `author`, `genre`, `slug`, `title` | the album-analogue; the conceptualizer's output |
| `Chapter` | `work`, `index`, `title`, `pov` | `pov` enum-constrained |
| `Scene` | `work`, `chapter`, `index`, `throughline` | the bar-analogue |
| `Character` | `work`, `name`, `archetype` | a `players[]` slot |
| `Premise` | `logline`, `central_question` | a pre-work idea (promotable to a `Work`) |
| `Storyform` | `work`, `resolve`, `growth`, `approach` | the Dramatica spine |
| `Coherence` | `work`, `status`, `violations` | a recorded coherence run (`status` enum) |

**Enums** (`enums={(label, field): {allowed}}` — widen-only, never clobber):

- `("Chapter", "pov"): {"1st", "3rd_limited", "3rd_omniscient", "2nd"}`
- `("Coherence", "status"): {"PASS", "FAIL"}`
- `("Coherence", "severity"): {"fail", "warn", "info"}` (on violation items)
- revision passes (carried on a `revision_pass` artefact field):
  `{"structural", "line", "copy", "proof"}`

**Edges** (`edges={...}` — unioned onto the core set): `COHERES_WITH` (a `Scene`/
`Chapter` → `Storyform`), `REVISES` (a later draft Artefact → the prior). All other
relations reuse core edges (`SERVES`, `PRODUCES`, `PASSED`/`BLOCKED_ON`,
`PRECEDES`, `HAS_PHASE`, `DERIVED_FROM`, `VALIDATES_AGAINST`).

**Artefact/template schemas** (`schemas={name: [required]}` — power `ctx.validate`):
`work` `[author, genre, slug, title]`, `premise` `[logline, central_question]`,
`ncp` `[storyform, players, scenes, metadata]`, `coherence-report` `[work, status]`,
`scene-prompt` `[work, scene, prompt]`.

**Skills** (`skills={name: skill_schema}` — Lifecycle templates the engine walker
walks; each is an ordered phase-graph, final phase often `gate: "hard"`):

- `work-concept` (kind `conceptualizer`) — the novel parallel of `album-concept`:
  `foundation → premise → storyform → cast → structure → world → confirmation(hard)`.
  Output of phase `confirmation` flips the work into a drafting-ready Lifecycle.
- `pre-drafting-check` (kind `orchestrator`) — wraps the 6-gate predicate; one
  phase per gate, a hard final phase that admits chapter drafting.
- `manuscript-revision` (kind `discipline`) — multi-pass editorial walk:
  `structural → line → copy → proof(hard)`; each pass records a `REVISES` edge.
- `scene-bridge-audit` (kind `discipline`) — the Q1–Q5 scene-bridge judgement walk
  (judgement, not a `transform` — it stays a skill, per the-agency-system's
  "tools assert structure, skills assert meaning").

### Verb table (role-tagged)

| Verb | Role | What | Provenance |
|---|---|---|---|
| `scaffold` | effect | Record a `Work` + return the 14-entry layout manifest; write to disk only when `apply=True`. | `Work` recorded, `SERVES` intent; on `apply` an `Artefact{kind:work}` `PRODUCES`d |
| `conceptualize` | act | Render a work-concept document (the album-concept analogue); the body the `work-concept` skill's phases fill. | `Artefact{kind:work}` `PRODUCES`d, `DERIVED_FROM` the `work-concept` Template |
| `promote_premise` | act | Turn a `Premise` node into a scaffolded `Work` (calls `scaffold` via `ctx.call`). | `Premise` `SUPERSEDED_BY` the new `Work` |
| `dramatica_lookup` | transform | Resolve elements / classes / variations + `check_dynamic_pair_reciprocity` over the 304-entry ontology. | none (pure) |
| `ncp_validate` | transform | Validate a doc against the pinned NCP-v1.3.0 JSON Schema; `{ok, errors}`, never raises on bad data. | none (pure) |
| `ncp_compile` | transform | Expand `storyform`+`cast`+`premise`+scenes into a full NCP doc (uses `dramatica_lookup`); returns the doc, does not write. | none (pure) |
| `coherence_check` | transform | Run the 11 decidable checks; return the compact report shape. | none (pure) |
| `coherence_correct` | act | Apply mechanical autofixes (`pair_reciprocity`, `slot_typing`) named in an explicit `autofix` set; records a `Coherence` node + a corrected `Artefact`. | `Coherence` recorded, corrected `Artefact` `REVISES` the input |
| `pre_drafting_gate` | act | Compose `gate.check` for each of the 6 gates on the work's `Lifecycle`; done iff all PASS. | one `Gate` per check, `PASSED`/`BLOCKED_ON` edges via `gate` |
| `build_scene_prompt` | transform | Entity-grounded, idempotent, source-traceable scene prompt (`<voice><world><beat><task>`), composing character/world/throughline/bridge fragments. | none (pure; idempotent — no timestamps/UUIDs) |
| `analyze_prose` | transform | Readability + rhythm + POV-violation scan over a passage. | none (pure) |

Role assignment follows the core contract: `transform` = stateless compute (the
structural-truth + analysis surface — decidable, replayable), `act` = a craft write
that records graph provenance (conceptualize, correct, gate), `effect` = an external
side-effect (disk write on `scaffold(apply=True)`).

### The 11 decidable coherence checks (the `transform` engine)

Ported as pure functions over the bundled ontology + an NCP doc (no LLM):
`pair_reciprocity`, `ktad_coverage`, `quad_completeness`, `slot_fill`,
`throughline_partition`, `crucial_element_placement`, `resolve_outcome_judgment`,
`approach_concern`, `mental_sex_problem_solving`, `signpost_permutation`,
`storybeat_moment_refs`. `coherence_check` fans them out and merges into the
token-cheap report; `coherence_correct` only flips the two mechanically-decidable
ones. Anything requiring judgement (the Q1–Q5 scene bridge) stays a **skill**, not a
verb.

### Dramatica + NCP libraries

- **Dramatica**: bundle the 304-entry ontology + the dynamic-pair index as data
  under `examples/novel/data/dramatica_ontology.json` (vendored from the-agency-system
  `maintenance/schemas/narrative-ontology/ontology.json` at the pinned SHA; record
  provenance in a sibling `.sha` file since JSON can't host comments). `_dramatica.py`
  is a lazy-loading navigator (`by_id`, `by_class/type/variation/element`,
  `by_dynamic_pair`, `check_dynamic_pair_reciprocity`). The 75 canonical
  dynamic-pair reciprocities are covered parametrically in
  `tests/test_novel_coherence.py`.
- **NCP**: pin the v1.3.0 schema under `examples/novel/data/ncp.schema.json` (with a
  `.sha`). `_ncp.py` ships `validate(doc)` (jsonschema Draft 2020-12) and
  `compile(work)`. See **Open Questions** on the `jsonschema` dependency.

### Migration / coverage map (the-agency-system → Agency)

| the-agency-system (Plan @ SHA) | Agency landing |
|---|---|
| 010 on-disk layout (11 templates) | `OntologyExtension.templates` + `scaffold` layout manifest; templates as named generator bodies, not files |
| 011 core handlers (~25 `novel_*` CRUD) | `Work`/`Chapter`/`Scene`/`Character`/`Premise` node types + `scaffold`/`conceptualize`/`promote_premise` verbs; CRUD IS graph `record`/`recall` via `ctx`, not a tool-per-entity surface |
| 012 Dramatica + NCP libs | `examples/novel/data/` vendored dataset + `_dramatica.py`/`_ncp.py` + `dramatica_lookup`/`ncp_validate`/`ncp_compile` transforms |
| 013 structural handlers (11 checks + prose) | `coherence_check`/`coherence_correct`/`analyze_prose` transforms; 11 checks as pure fns |
| 014 6-gate + revision + promo | `pre_drafting_gate` (act, composes `gate`) + `manuscript-revision` skill (the 4 passes) ; promo deferred (see scope cut) |
| 015 32-skill catalogue | the 4 Lifecycle-template skills in the extension + installable SKILL.md via `plugin.author_skill`; the prose catalogue is generated, not hand-ported |
| 021 10 prompt-builders | `build_scene_prompt` transform (the canonical composing builder) ; the other 9 builders deferred to v2 (see scope cut) |
| 016 agentic layer | OUT — that is Spec 011 (agentic-capabilities) |

## Files

- **Create**:
  - `examples/novel.py` — `NovelCapability` + the `OntologyExtension` (the public
    extension; mirrors `examples/music.py` shape).
  - `examples/novel/__init__.py` — re-exports `NovelCapability`.
  - `examples/novel/_layout.py` — the 14-entry layout manifest + slug rules.
  - `examples/novel/_dramatica.py` — the lazy navigator over the bundled ontology.
  - `examples/novel/_ncp.py` — NCP `validate` + `compile`.
  - `examples/novel/_coherence.py` — the 11 decidable checks + the report merge.
  - `examples/novel/_prose.py` — readability / rhythm / POV scan; scene-prompt assembly.
  - `examples/novel/data/dramatica_ontology.json` (+ `.sha`) — vendored 304-entry dataset.
  - `examples/novel/data/ncp.schema.json` (+ `.sha`) — pinned NCP v1.3.0 schema.
  - `docs/examples/author_a_novel.py` — the end-to-end runnable example.
  - `tests/test_novel_capability.py`, `tests/test_novel_coherence.py`,
    `tests/test_novel_skills.py`.
- **Modify**:
  - `examples/__init__.py` — export `NovelCapability` alongside `MusicCapability`.
- **Do not modify**: `agency/` core (engine, capability, ontology, memory, skill,
  templates) — the domain must land purely through the extension contract. If it
  cannot, that is a finding to escalate, not a core edit to slip in.

## Open Questions / Needs Research

1. **Core vs examples/.** This spec lands novel in `examples/` to match `music`
   and keep the harness minimal. But novel is materially heavier (vendored dataset,
   schema validation, 11-check engine). Should it instead ship as a first-class
   `agency/capabilities/novel.py` once the domain is proven? Decision needed before
   v2; the verb/ontology contract is identical either way, so the move is cheap.
2. **Dramatica/NCP vendoring.** The 304-entry ontology + v1.3.0 schema are vendored
   as bundled data under `examples/novel/data/`. Is that the right home, or should
   large reference datasets live outside the package (e.g. fetched/installed)? And
   does the engine's strict ontology-merge need any awareness of capability-bundled
   data files, or is data purely the capability's private concern (current
   assumption)?
3. **`jsonschema` dependency.** `ncp_validate` wants `jsonschema` (Draft 2020-12).
   The core has zero hard third-party deps beyond `fastmcp`. Do we add `jsonschema`
   to `requirements.txt`, vendor a minimal validator, or hand-roll the v1.3.0
   structural checks in stdlib? (Leaning hand-rolled for v1 to keep the core
   dependency-free; flag in the PR.)
4. **v1 scope cut.** Proposed v1 = scaffold + conceptualize + the structural-truth
   transforms (dramatica/ncp/coherence) + `pre_drafting_gate` + the 4 skills +
   `build_scene_prompt`. **Deferred to v2**: the other 9 prompt-builders, promo
   authoring, the full 32-skill prose catalogue, prose-analysis depth beyond a
   minimal rule set, world-consistency/timeline checks. Is this the right v1 line?
5. **Disk vs graph as source of truth.** the-agency-system writes files under
   `novels/`; Agency's substrate is the graph. Is `scaffold(apply=True)`'s disk
   write even desirable, or should the work live purely as graph nodes with disk
   export a separate `effect`? (Current design: graph is canonical; `apply=True` is
   an optional export.)
6. **Skill walker vs `gate` composition for the 6-gate.** `pre_drafting_gate`
   composes `gate.check`; `pre-drafting-check` is also a skill. Is the duplication
   intentional (verb = programmatic, skill = walkable UI) or should one defer to the
   other?

## Evidence

- Exemplar spec format: `/home/user/the-agency-system/Plan/108-context-mode-integration/spec.md`
- Research: `/home/user/agency/research/capability-specs/specs/novel.md`,
  `/home/user/agency/research/capability-specs/capability-catalogue.md` (rows 20-25)
- Agency extension contract: `/home/user/agency/agency/capability.py`
  (`OntologyExtension`, `CapabilityBase`, `@verb`), `/home/user/agency/agency/ontology.py`
  (`Ontology.extend` strict-merge + enums widen), `/home/user/agency/agency/engine.py`
  (`extra_capabilities` extension point, auto-wiring), `/home/user/agency/agency/skill.py`
  (the walker: progressive disclosure + hard gate), `/home/user/agency/examples/music.py`
  (the domain-capability template this spec follows).
- Source depth (the-agency-system @ 0a6a9e71): `Plan/010-novel-on-disk-layout`,
  `Plan/011-novel-handlers-core`, `Plan/012-dramatica-and-ncp-libs`,
  `Plan/013-novel-handlers-structural` (the 11 checks + report shape),
  `Plan/014-novel-gates-and-revision` (the 6 gates + 4 revision passes),
  `Plan/015-novel-skills-catalogue` (the 32-skill parity table),
  `Plan/021-novel-prompt-builder-family` (the 10-builder DAG + scene-builder contract).
