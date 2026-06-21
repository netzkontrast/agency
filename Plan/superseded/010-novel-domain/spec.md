---
spec_id: "010"
slug: novel-domain
status: closed-superseded   # → 101 + 102-108; closed 2026-06-09
state: superseded
last_updated: 2026-06-09
owner: "@agency"
depends_on: [001, 004, 016]
affects:
  - agency/capabilities/novel/__init__.py        # re-exports NovelCapability (auto-discovered)
  - agency/capabilities/novel/_main.py           # the CapabilityBase subclass + OntologyExtension
  - agency/capabilities/novel/_layout.py         # 14-entry workspace layout + slug discipline
  - agency/capabilities/novel/_dramatica.py      # lazy navigator over the bundled ontology
  - agency/capabilities/novel/_ncp.py            # draft-07 jsonschema validator
  - agency/capabilities/novel/_coherence.py      # decidable-subset checks + report merge
  - agency/capabilities/novel/data/dramatica_ontology.json   # vendored 303-entry dataset
  - agency/capabilities/novel/data/dramatica_ontology.json.sha
  - agency/capabilities/novel/data/ncp.schema.json           # pinned draft-07 schema
  - agency/capabilities/novel/data/ncp.schema.json.sha
  - docs/examples/author_a_novel.py
  - tests/test_novel_capability.py
  - tests/test_novel_coherence.py
  - tests/test_novel_skills.py
  - requirements-examples.txt                   # jsonschema (capability dep, not core)
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
  - "https://github.com/netzkontrast/kohaerenzprotokoll @ Legacy/ corpus (the MVP being re-architected)"
estimated_jules_sessions: 2
domain: novel
wave: 2
---

# Spec 010 — Novel Domain Capability

## Update note (2026-05-31)

This revision re-bases the spec on the post-Spec-016 substrate (folder-per-capability + `develop.scaffold_capability` + block-mode lint) and the Spec 029/030 onboarding surface, and **elevates the novel capability from `examples/` to `agency/capabilities/`** — it is the canonical user-facing application driving the Kohärenz-Protokoll campaign, not a third-party domain proof. The original design intent (re-architecture, not literal port; graph-canonical with `apply=True` disk export; decidable-subset honesty; 6-gate composition) is unchanged. The mechanical changes:

- **Location:** `examples/novel/…` → `agency/capabilities/novel/…` (auto-discovered via folder-form `discover()`, Spec 016 Phase 3 — commit `8a5a45d`). The "Where it lives" Open Question resolution flips: **core, not examples**.
- **`depends_on`:** `[001, 002, 003]` → `[001, 004, 016]`. Spec 002 (Driver registry) is additive — the novel capability uses no external drivers (Dramatica + NCP are vendored static JSON, not boundaries). Spec 003 (typed Skill/Phase) is a validation-time refactor that keeps storing dicts (Open Q5 RESOLVED → store dict) — the `work-concept` skill is still authored as a dict literal exactly like `examples/music.py`'s `album-concept`. **Spec 004 (template-schema-coverage) is the missed dependency this revision adds**: novel declares 4 artefact schemas (`work`, `premise`, `ncp`, `coherence-report`) in its `OntologyExtension`, but `Ontology.schemas` is an in-memory registry only — Spec 004 ships `Ontology.materialise_schemas(memory)` which records one `Schema` node per registered schema at engine construction, so novel's `VALIDATES_AGAINST` edges have real targets. Without 004 the schema declarations are decorative (the current music.py reality). Spec 016 is the other real dependency: its `develop.scaffold_capability` produces the doctrine-compliant skeleton this spec MUST start from.
- **Bootstrap discipline:** implementation MUST begin with `develop.scaffold_capability(name="novel", kind="heavy")` (kind heavy = vendored data + multiple sub-modules + JSON schema + skill walker). The resulting skeleton ships the `# agency-scaffold: v1` marker so `plugin.lint_capability("novel")` runs in **block mode** by construction.
- **Onboarding surface:** a fresh novel-cap author dispatched into a clean repo onboards via `agency_welcome` → `agency_install` → `intent_bootstrap` → `develop.scaffold_capability(…)` (Spec 029/030 substrate tools, shipped in PR #14).
- **Per-verb token budget:** every verb's docstring carries a ≤120-char brief slice (Spec 023 adaptive-disclosure gate); `lint_capability` enforces this in block mode.
- **Source-repos:** added the kp `Legacy/` corpus — it carries the same MVP source SHA but is the user-facing repo for the campaign; the agency repo holds the design and the implementation.

## Why

`the-agency-system` carries a deep, structurally-grounded novel domain: a disk-first
work layout (`novels/{author}/works/{genre}/{slug}/` with 7 root files + 7
subfolders, Plan 010) indexed into a `StateCache`, core CRUD handlers over
works/chapters/scenes/characters (Plan 011), a vendored Dramatica ontology + an
NCP-v1.3.0 JSON Schema (Plan 012), a coherence handler that claims 11 "decidable"
checks (Plan 013), a 6-gate pre-drafting orchestrator + revision tracking (Plan
014), a 32-skill catalogue (Plan 015), and a 10-builder prompt family (Plan 021).

**This spec is grounded in the SHIPPED code, not the source Plan specs** (the
aspirational contracts the source repo never fully honoured). Three things the
source Plan specs claim do NOT match what shipped, and this spec ports the shipped
truth (see **Source fidelity**, below): the ontology is **303 entries** (not 304),
the NCP schema is **draft-07** `{schema_version, story{…narratives…}}` (not a
`{storyform,players,scenes,metadata}` shape), and most of the "11 decidable checks"
are fixture-discriminating heuristics with a `structure.py` stub behind them — only
a small subset is genuinely decidable from the bundled ontology.

In **Agency** the craft lands as ONE self-registering capability plus an
`OntologyExtension`, exactly like `examples/music.py`: drop a module in `examples/`
loaded via `Engine(..., extra_capabilities=[…])`, define a `Capability` whose verbs
are role-tagged `act`/`transform`/`effect`, carry the node types / enums / skills /
template-schemas in `Capability.ontology`, and the engine `discover()`s it, merges
the ontology strictly onto the core, and auto-wires one MCP tool per verb. The
structural truth (Dramatica/NCP validation) becomes `transform` verbs (decidable, no
LLM); the conceptualizer becomes a Lifecycle-template **skill** with a hard gate; the
pre-drafting 6-gate becomes a `gate.check` composition. **Code-mode IS the contract**
— there is no `novel_*` tool surface to maintain; the verbs are discovered via
`search` and called from inside `execute`.

Note this is a deliberate **re-architecture**, not a literal port: the source novel
domain is disk-first (works as files, indexed into `StateCache`, no graph). Agency's
substrate is the bi-temporal graph, so the graph is canonical here and the on-disk
layout is an optional `apply=True` export — a genuine inversion, not a mirror.

This spec is the second proof (after `music`) that a rich external domain folds onto
the four-concept substrate without bespoke wiring, and the first proof that a domain
can carry a **vendored reference dataset** (the Dramatica ontology) and a
**schema-validation `transform`** (NCP) through the `OntologyExtension` mechanism.

## Done When

- [ ] `agency/capabilities/novel/__init__.py` re-exports a
  `NovelCapability(CapabilityBase)` with `name="novel"`, `home="capability"`,
  and an `OntologyExtension` that merges cleanly onto the core. **Auto-discovered**
  via folder-form `discover()` (Spec 016 Phase 3 — commit `8a5a45d`): a fresh
  `Engine(":memory:")` registers `capability_novel_*` verbs WITHOUT any
  `extra_capabilities=[…]` host hook. The legacy
  `Engine(..., extra_capabilities=[NovelCapability.as_capability()])` API still
  works (additive — Spec 016 keeps the extra_capabilities seam) but is no longer
  required.
- [ ] **`plugin.lint_capability("novel")` returns `ok=True` in block mode**
  (Spec 016 + 024). The scaffolded `agency/capabilities/novel/_main.py` carries
  the `# agency-scaffold: v1` marker on its first non-blank line, flipping the
  linter from `warn` to `block`. All five rule families (structural docstring
  markers, role-tag/IO consistency, render-slice presence, consumer-contract
  registration, token budget) MUST pass; any violation is a real error, not a
  grandfathered warning.
- [ ] **Every verb's docstring brief slice is ≤ 120 chars / ≤ 20 cl100k tokens**
  (Spec 023 adaptive-disclosure gate). The brief is the first sentence parsed by
  `agency/render.py::parse_slices`; it surfaces in `search` / `capability_plugin_help`
  / FastMCP `tools/list`. Verified by the token-budget rule family inside
  `lint_capability`.
- [ ] The extension adds the node types `Work`, `Chapter`, `Scene`, `Character`,
  `Premise`, `Storyform`, `Coherence` with strict required-field schemas, the
  closed node enums for `Chapter.pov` and `Coherence.status` (the only two enums
  that key a real v1 node field — violation `severity` lives in the
  `coherence-report` artefact schema, and `revision_pass` defers to v2; see
  **Enums**), the named edges `COHERES_WITH` + `OVERRIDDEN_BY` (gate-override), the
  `work-concept` conceptualizer **skill** (a Lifecycle template), and the artefact
  schemas for `work`, `premise`, `ncp`, `coherence-report`.
- [ ] The verb table (below) is implemented and role-tagged; every `act`/`effect`
  verb records provenance via `self.ctx` (Invocation `SERVES` intent, Artefacts
  `PRODUCES`d, Work/Coherence nodes recorded), and every `transform` verb is pure
  (no graph write, no disk write).
- [ ] `novel.scaffold(author, genre, slug, title)` (effect) records a `Work` node
  edged `SERVES` the intent and returns the 14-entry on-disk layout manifest (7
  root files + 7 subfolders) WITHOUT writing to disk unless `apply=True` —
  mirroring Agency's `dry_run` discipline through an explicit `apply` flag. The
  graph node is canonical; the disk export is optional.
- [ ] `novel.dramatica_lookup(...)` (transform) resolves elements / classes / types
  / variations and checks dynamic-pair reciprocity against the bundled ontology —
  a clean port of the shipped `navigator` (`by_id`, `by_class`, `by_type`,
  `by_variation`, `by_element`, `by_dynamic_pair`, `check_dynamic_pair_reciprocity`).
  Counts are asserted from the bundled data at test time, never hard-coded
  (see **Source fidelity §1–2**).
- [ ] `novel.ncp_validate(doc)` (transform) validates a doc against the bundled
  **draft-07** NCP schema using the real `jsonschema` library and returns
  `{ok, errors:[...]}`; it never raises on a malformed doc (only on unreadable
  input). The schema top-level is `{schema_version, story}`; see **Source
  fidelity §3**.
- [ ] `novel.coherence_check(doc)` (transform) runs ONLY the genuinely-decidable
  checks (see **The decidable coherence subset**) against an NCP projection and
  returns the compact report `{status, violations:int, checks:{<key>:{status,
  items?}}}`; a clean doc serialises in ≤ 80 tokens (PASS checks carry no `items`).
  Non-decidable checks are NOT shipped as `transform`s — they are documented as
  "needs-judgement → skill / deferred."
- [ ] `novel.pre_drafting_gate(work_id, ...)` (act) composes `gate.check` for each
  of the 6 gates against the work's `Lifecycle`; `chapter` drafting is admitted
  only when all 6 PASS. A failing gate records a `BLOCKED_ON` edge + an
  `input-required` pause (exactly like `gate.check`). A `force=True` override path
  is recorded as an explicit `OVERRIDDEN_BY` edge (declared in the extension's
  `edges`; see **Edges**) carrying caller + reason — the graph analogue of the
  source's `force_overrides[]` audit (see **Source fidelity §7**).
- [ ] The `work-concept` conceptualizer skill ends in a **hard** confirm gate
  (mirrors `examples/music.py`'s `album-concept`); the engine's skill walker walks
  it one phase at a time (progressive disclosure: `current()` returns only the
  active phase). The skill's pre-drafting phase delegates to `pre_drafting_gate`
  (one source of truth — the skill does not reimplement the gate).
- [ ] `pytest -q tests/test_novel_capability.py tests/test_novel_coherence.py
  tests/test_novel_skills.py` passes; the existing suite (`pytest -q`) still
  passes (no regression to the 56 baseline).
- [ ] `python docs/examples/author_a_novel.py` runs end-to-end: scaffold a work →
  conceptualize (walk the gated skill) → validate NCP → coherence-check →
  pre-drafting-gate, printing the provenance subgraph for the intent.
- [ ] `docs/vision/CORE.md` is NOT modified by this spec — the domain proves the
  extension contract; it does not change the canon.

## Design

### Where it lives — core, not examples (updated 2026-05-31)

The original v1 resolution placed novel in `examples/`, parallel to `music.py`. This revision **flips that to `agency/capabilities/novel/`** (a folder-form core capability auto-discovered per Spec 016 Phase 3 — commit `8a5a45d`). Three reasons:

1. **User-facing canonical.** The Kohärenz-Protokoll project (kp repo) IS the agency plugin's primary application. Novel is the substrate's reason-for-being in this org, not a third-party domain proof. Music remains in `examples/` (still the second-domain proof of `extra_capabilities`).
2. **Auto-discovery.** Core caps register with no `extra_capabilities=[…]` host hook — a fresh `Engine(":memory:")` already exposes `capability_novel_*` verbs without any plugin-host glue. The kp repo (which installs the agency plugin via marketplace) gets the novel capability for free.
3. **Folder form fits the weight.** Novel ships 4+ sub-modules + 2 vendored JSON datasets + 1 skill template — significantly heavier than `reflect.py` or `gate.py`. Spec 016 Phase 3 explicitly designed folder-form `discover()` for this case.

The vendored-dataset placement is still the capability's private concern (`Ontology.extend` is unchanged — it touches no data files). `agency/CLAUDE.md`'s "domain capabilities live in `examples/`" line documents the music precedent and remains correct as guidance for *third-party* domain capabilities; novel is the explicit exception (canonical user-facing application).

### Bootstrap via the engine (NEW — Spec 016 + 029/030)

Implementation MUST begin by walking the doctrine, not by hand-authoring files. The first phase is `develop.scaffold_capability` (verb shipped by Spec 016, Phase 3):

```python
# 0. Onboard if fresh (Spec 029/030 substrate tools — no bash hop needed)
await call_tool('agency_welcome', {})
await call_tool('agency_install', {})           # idempotent
r = await call_tool('intent_bootstrap', {
    'purpose': 'novel capability v1',
    'deliverable': 'agency/capabilities/novel/ + tests pass',
    'acceptance': 'plugin.lint_capability("novel") ok=True in block mode',
})
iid = r['intent_id']

# 1. Scaffold the skeleton — emits a CAPABILITY-AUTHORING.md-compliant tree
#    that lints CLEAN in block mode by construction.
await call_tool('capability_develop_scaffold_capability', {
    'name': 'novel', 'kind': 'heavy', 'intent_id': iid,
})
# Output: agency/capabilities/novel/ with __init__.py + _main.py + the
# `# agency-scaffold: v1` marker that flips lint_capability into block mode.
```

The skeleton is the **starting state** for the per-section TDD loops (`dramatica_lookup` first — see §"Implementation order", below). Hand-editing the scaffolded files is the next step; the scaffold itself is non-negotiable per Spec 024's discipline rule.

### Per-verb token budget (NEW — Spec 023)

Every verb's docstring carries a ≤120-character brief slice (the first sentence, parsed by `agency/render.py::parse_slices`). `plugin.lint_capability` checks this in block mode and fails if the brief exceeds the budget. The brief surfaces in:

- `search` results (the discovery surface);
- `capability_plugin_help` (the macroskill map);
- the FastMCP `tools/list` response (the host-visible tool description).

A verb whose first sentence is "Lazily-load the Dramatica ontology from `data/dramatica_ontology.json` and …" (87 chars) PASSES; one that exposes the full implementation rationale in the first sentence FAILS. Move detail into the body, the `Inputs:` / `Returns:` / `chain_next:` markers, or the in-line comments.

### Implementation order — sequenced per kp § / agency loop

The 7 implementation loops the post-update spec drives:

| Loop | Lands | Verbs / data |
|---|---|---|
| 0 (this PR) | Spec update + scaffolded skeleton + vendored data + smoke tests | `agency/capabilities/novel/` exists, lints clean, ontology files present + `.sha` measured |
| 1 | First `transform` | `dramatica_lookup` (the navigator port, parametric tests against ≈ 54 measured pairs) |
| 2 | Second `transform` | `ncp_validate` (real `jsonschema.Draft7Validator`, draft-07) |
| 3 | OntologyExtension + first `act`/`effect` | 7 nodes + 2 enums + 2 edges + 4 schemas declared; `scaffold` verb (graph-canonical, `apply=True` exports) |
| 4 | Third `transform` | `coherence_check` (decidable subset only — Spec 010 §"The decidable coherence subset") |
| 5 | First gate-composing `act` | `pre_drafting_gate` (composes 6 `gate.check` calls + `OVERRIDDEN_BY` audit edge for `force=True`) |
| 6 | Conceptualizer + skill walker | `conceptualize` (act) + the `work-concept` skill (`foundation → premise → storyform → cast → structure → world → confirmation(hard)`); pre-drafting phase DELEGATES to `pre_drafting_gate` |
| 7 | Runnable end-to-end | `docs/examples/author_a_novel.py` — scaffold → walk skill → validate NCP → coherence_check → pre_drafting_gate; prints the provenance subgraph |

Each loop = one PR; each PR = TDD per task (RED → GREEN → REFACTOR → commit) per Spec 016 Phase 5 conftest fixtures (Phase 5 — commit `d76135a`).

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
| `Character` | `work`, `name`, `archetype` | a cast member |
| `Premise` | `logline`, `central_question` | a pre-work idea (promotable to a `Work`; v1 omits the source's `status`/`promoted_to` bookkeeping — see scope cut) |
| `Storyform` | `work`, `resolve`, `growth`, `approach` | the Dramatica spine |
| `Coherence` | `work`, `status`, `violations` | a recorded coherence run (`status` enum) |

**Enums** (`enums={(label, field): {allowed}}` — widen-only, never clobber). An
`OntologyExtension` enum is a `(label, field)` constraint enforced on a **graph
node** (`ontology.py:136-138`); an enum keyed to a field the node never carries is
inert (it never fires). So v1 declares ONLY the enums that key a real node field:

- `("Chapter", "pov"): {"1st", "3rd_limited", "3rd_omniscient", "2nd"}` — keys
  `Chapter.pov` ✓.
- `("Coherence", "status"): {"PASS", "FAIL"}` — keys `Coherence.status` ✓.

**Not node enums** (deliberately — they key no v1 node field, so they would never
fire as `OntologyExtension` enums):

- **violation `severity`** `{"fail", "warn", "info"}` — a violation item is a
  sub-object INSIDE the `coherence-report` artefact JSON, not a graph node. Its
  severity is therefore validated as part of the `coherence-report` **artefact
  schema** (`ctx.validate`), not as a `(Coherence, severity)` node enum (the
  `Coherence` node schema is only `[work, status, violations]` — it carries no
  `severity` field). See **Artefact/template schemas**, below.
- **revision passes** `{"structural", "line", "copy", "proof"}` (the source's 4
  passes) — documentation-only in v1: no v1 node or artefact carries a
  `revision_pass` field, so the enum is NOT declared in the `OntologyExtension`. It
  ships with the revision *skill* that walks the passes, which is deferred to v2.

**Edges** (`edges={...}` — unioned onto the core set; the core edge set is CLOSED,
so every new relation MUST be declared here or `Memory.link` rejects it as an
unknown edge — `ontology.py:111,141`):

- `COHERES_WITH` — a `Scene`/`Chapter` → `Storyform`.
- `OVERRIDDEN_BY` — the **gate-override** edge: when `pre_drafting_gate(force=True)`
  bypasses a failing gate, the `Gate` is edged `OVERRIDDEN_BY` the override record
  (caller + reason). This is the graph analogue of the source's `force_overrides[]`
  audit (see **Source fidelity §7**) and is NOT a `SUPERSEDED_BY` (an override is not
  a supersession — a bypassed gate still stands as a recorded failure). It SHIPS in
  v1 because `pre_drafting_gate` is a v1 verb; without it, `force=True` raises an
  "unknown edge" error at runtime.

All other relations reuse core edges (`SERVES`, `PRODUCES`, `PASSED`/`BLOCKED_ON`,
`PRECEDES`, `HAS_PHASE`, `DERIVED_FROM`, `VALIDATES_AGAINST`). The
`promote_premise` supersede edge is DEFERRED to v2 with that verb (it never ships in
v1, so its edge does not need declaring yet).

**Artefact/template schemas** (`schemas={name: [required]}` — power `ctx.validate`):
`work` `[author, genre, slug, title]`, `premise` `[logline, central_question]`,
`ncp` `[schema_version, story]` (the draft-07 top-level — see **Source fidelity
§3**), `coherence-report` `[work, status]`. The compact report's `violations[]`
items each carry a `severity ∈ {"fail", "warn", "info"}`; because items are
artefact-JSON sub-objects (not graph nodes), this constraint is enforced by the
`coherence-report` artefact validator (`_coherence.py`), NOT by a node enum — see
**Enums** above.

**Skills** (`skills={name: skill_schema}` — Lifecycle templates the engine walker
walks; each is an ordered phase-graph, final phase `gate: "hard"`):

- `work-concept` (kind `conceptualizer`) — the novel parallel of `album-concept`:
  `foundation → premise → storyform → cast → structure → world → confirmation(hard)`.
  The `confirmation` phase flips the work into a drafting-ready Lifecycle; a
  pre-drafting phase delegates to `pre_drafting_gate` (single source of truth).

### Verb table (role-tagged) — v1

| Verb | Role | What | Provenance |
|---|---|---|---|
| `scaffold` | effect | Record a `Work` + return the 14-entry layout manifest; write to disk only when `apply=True`. | `Work` recorded, `SERVES` intent; on `apply` an `Artefact{kind:work}` `PRODUCES`d |
| `conceptualize` | act | Render a work-concept document (the album-concept analogue); the body the `work-concept` skill's phases fill. Builds the body INLINE (exactly like `music.conceptualize`), so no `templates=` map is needed. | `Artefact{kind:work}` `PRODUCES`d (no `DERIVED_FROM Template` edge — `music.py` precedent; the `OntologyExtension` declares no `templates=`) |
| `dramatica_lookup` | transform | Resolve elements / classes / types / variations + `check_dynamic_pair_reciprocity` over the bundled ontology. | none (pure) |
| `ncp_validate` | transform | Validate a doc against the bundled **draft-07** NCP schema via real `jsonschema`; `{ok, errors}`, never raises on bad data. | none (pure) |
| `coherence_check` | transform | Run ONLY the decidable checks over an NCP projection; return the compact report. | none (pure) |
| `pre_drafting_gate` | act | Compose `gate.check` for each of the 6 gates on the work's `Lifecycle`; done iff all PASS, with a recorded `force=True` override path. | one `Gate` per check, `PASSED`/`BLOCKED_ON` edges via `gate`; `OVERRIDDEN_BY` edge (with caller + reason) on `force=True` |

Role assignment follows the core contract: `transform` = stateless compute (the
structural-truth surface — decidable, replayable), `act` = a craft write that records
graph provenance (conceptualize, gate), `effect` = an external side-effect (disk
write on `scaffold(apply=True)`).

### The decidable coherence subset (the `transform` engine)

The shipped `handlers/novel/coherence.py` registers 11 named checks, but reading the
code shows most are **fixture-discriminating heuristics**, not ontology traversals
(e.g. `check_ktad_coverage` hard-codes `if concern_id == "t.progress": FAIL`;
`check_quad_completeness` hard-codes `if problem == "el.pursuit": FAIL`;
`check_signpost_permutation` hard-codes `if sp[0] != "t.past": FAIL`). The companion
`handlers/novel/structure.py` is a pure stub — every check `return {"status":
"PASS"}`. We do NOT port fixture-discriminators dressed up as decidable transforms.

**Ship as `transform` (genuinely decidable from the bundled data):**

- `dynamic_pair_reciprocity` — the happy path against the ontology's dynamic-pair
  index (the navigator port; no heuristic fallback).
- `storybeat_moment_refs` — a real foreign-key traversal: every `moment` storybeat
  reference must resolve to an existing storybeat `id`.
- `throughline_partition` — MC/OS/IC/RS must each map to a distinct class (set
  uniqueness; decidable from the doc).
- `slot_fill` — required throughline slots are present (structural presence; no
  ontology needed).
- `ktad_coverage` + `quad_completeness` — shippable as `transform`s ONLY if the quad
  reverse-index / KTAD-membership test is built from the bundled ontology
  (genuinely decidable then). Otherwise defer them with the rest.

**NOT shipped (re-labelled "needs-judgement → skill" / deferred to v2):**
`signpost_permutation`, `resolve_mirror`, `mental_sex_problem_solving`,
`crucial_element_placement`, `approach_concern`, and the Q1–Q5 scene-bridge
judgement. The compact report's check keys MUST match the subset actually shipped —
do not copy the source's brief names. (Note the shipped registry uses `resolve_mirror`,
not the brief's `resolve_outcome_judgment`; if any deferred check is revived, port the
shipped name + behaviour.)

### Dramatica + NCP libraries

- **Dramatica**: bundle the ontology + the dynamic-pair index as data under
  `agency/capabilities/novel/data/dramatica_ontology.json` (vendored from
  the-agency-system `reference/novel/dramatica/ontology.json` at the pinned SHA;
  record provenance — including the file's real `entries` length — in a sibling
  `.sha` file since JSON can't host comments). `_dramatica.py` is a lazy-loading
  navigator (`by_id`, `by_class/type/variation/element`, `by_dynamic_pair`,
  `check_dynamic_pair_reciprocity`). Reciprocal pairs are extracted from the
  bundled `kind: dynamic-pair` entries (`pair_member_a`/`pair_member_b`) at
  test-collection time and covered parametrically in
  `tests/test_novel_coherence.py` — never hard-coded (see **Source fidelity §2**).
- **NCP**: bundle the **draft-07** schema under
  `agency/capabilities/novel/data/ncp.schema.json` (with a `.sha`). `_ncp.py`
  ships `validate(doc)` using real `jsonschema` (Draft7Validator). See **Open
  Questions** on the `jsonschema` dependency.

### Source fidelity (cite: the-agency-system @ 0a6a9e71)

These corrections re-base the spec on the SHIPPED artefacts, MEASURED here:

1. **Ontology is 303 entries, not 304.** `reference/novel/dramatica/ontology.json`
   is `{schema_version, ontology_version, created, entries[…]}` of length **303**,
   kinds (measured): `class 4 · type 16 · variation 62 · element 63 · dynamic-pair 65
   · quad 35 · concept 38 · archetype 8 · throughline 4 · character-dynamic 4 ·
   plot-dynamic 4`. So **63 elements (not 64), 62 variations (not 64)**, and
   `dynamic-pair`/`quad` are their OWN first-class kinds. **Do not pin "304/64/64."**
   Assert the bundled `entries` array length (or `≥ 300`) and copy the real length
   into the `.sha`.
2. **Reciprocal pairs ≈ 54, not 75.** The source Plan-012 "75 canonical dynamic-pair
   reciprocities" is a vendor-markdown number the JSON never honoured: the shipped
   ontology has **65 `kind: dynamic-pair` entries** and **108 entries carrying a
   `dynamic_pair_id`**, de-duplicating to ~**54 distinct reciprocal `(a,b)` pairs**
   (measured). **Do not hard-code 75.** Extract pairs from the bundled data at test
   time and assert the measured count.
3. **NCP shape is draft-07 `{schema_version, story}`.** `state/schema/ncp.schema.json`
   is `"$schema": ".../draft-07/schema#"` with top-level `required:
   ["schema_version", "story"]`; `story` requires `[id, title, logline, created_at,
   narratives]`, narratives carry `subtext{perspectives,players,dynamics,storypoints,
   storybeats}` + `storytelling{overviews,moments}`. There is **no**
   `{storyform,players,scenes,metadata}` shape and it is **not** Draft 2020-12. The
   port targets this draft-07 schema; `ncp_validate` and the `coherence_check`
   projection MUST agree with it (the shipped coherence code reads a *third*,
   inconsistent `ncp["storyform"]["throughlines"][…]` shape — do not propagate it;
   document the projection `coherence_check` operates on).
4. **`coherence_check` is the decidable subset only** (above). The 11 source checks
   are mostly heuristics + a `structure.py` stub — re-labelled honestly here.
5. **`ncp_compile` and `coherence_correct` are NET-NEW vs the source, hence
   deferred.** The shipped `novel_coherence_correct` returns `{"error":
   "NOT_IMPLEMENTED"}` for real fixes (only a partial dry-run planner exists); there
   is no NCP compiler that produces the draft-07 shape. Neither is "ported."
6. **`dramatica_lookup` IS a faithful, clean port** of the shipped `navigator`
   (`navigator.py` `by_id/by_class/by_type/by_variation/by_element/by_dynamic_pair/
   check_dynamic_pair_reciprocity`). Use its signature as the reference.
7. **Gate names + override match the source.** The 6 gates
   (`dramatica_confirmed, ncp_valid, premise_locked, cast_complete, pov_declared,
   sources_verified`) match `gates.py:81–225` exactly; the source writes
   `force_overrides[]` (timestamp + caller) on bypass (`gates.py:263–274`). The
   Agency `pre_drafting_gate` reproduces this as the explicit `OVERRIDDEN_BY` edge
   declared in the extension's `edges` (see **Edges**).

### Migration / coverage map (the-agency-system → Agency)

| the-agency-system (shipped @ SHA) | Agency landing |
|---|---|
| 010 disk layout (7 root + 7 subfolders), `StateCache`-indexed | `scaffold` 14-entry layout manifest; graph canonical, disk an optional `apply=True` export (re-architecture, not a mirror) |
| 011 core handlers (CRUD + `ideas.py` premise lifecycle + `status.py` transitions) | `Work`/`Chapter`/`Scene`/`Character`/`Premise` node types + `scaffold`/`conceptualize` verbs; CRUD IS graph `record`/`recall` via `ctx`. Premise `status`/`promoted_to` + entity status-transition tables DEFERRED (see scope cut) |
| 012 Dramatica + NCP libs | `examples/novel/data/` vendored 303-entry dataset + draft-07 schema + `_dramatica.py`/`_ncp.py` + `dramatica_lookup`/`ncp_validate` transforms |
| 013 coherence (11 named checks + `structure.py` stub) | `coherence_check` — the decidable subset only; heuristics re-labelled / deferred |
| 014 6-gate + revision + promo | `pre_drafting_gate` (act, composes `gate`, with force-override audit) ; revision-pass *skill* + promo DEFERRED |
| 015 32-skill catalogue | the `work-concept` conceptualizer skill in the extension ; the prose catalogue DEFERRED |
| 021 10 prompt-builders | DEFERRED to v2 in full (`build_scene_prompt` + the other 9) |
| 016 agentic layer | OUT — that is a separate agentic spec |

## Files

- **Scaffold first** via `develop.scaffold_capability(name="novel", kind="heavy")`. The
  verb writes the folder skeleton + the `# agency-scaffold: v1` marker; hand-editing
  starts AFTER the scaffold lands and lints clean.
- **Create** (post-scaffold; folder under `agency/capabilities/novel/`):
  - `__init__.py` — re-exports `NovelCapability` (auto-discovery target).
  - `_main.py` — `NovelCapability(CapabilityBase)` + the `OntologyExtension` (the public
    capability surface; mirrors `examples/music.py` shape but in folder form).
  - `_layout.py` — the 14-entry layout manifest + slug rules.
  - `_dramatica.py` — the lazy navigator over the bundled ontology.
  - `_ncp.py` — NCP `validate` (real `jsonschema`, draft-07).
  - `_coherence.py` — the decidable-subset checks + the report merge.
  - `data/dramatica_ontology.json` (+ `.sha`) — vendored 303-entry dataset.
  - `data/ncp.schema.json` (+ `.sha`) — pinned draft-07 NCP schema.
  - `docs/examples/author_a_novel.py` — the end-to-end runnable example.
  - `requirements-examples.txt` — `jsonschema` (a capability dep, not a core dep; see Open Q3).
  - `tests/test_novel_capability.py`, `tests/test_novel_coherence.py`,
    `tests/test_novel_skills.py` (using the Spec 016 Phase 5 `tests/conftest.py`
    fixtures — `fresh_engine`, etc.).
- **Do not modify**: `agency/{engine,capability,ontology,memory,skill,templates}.py`
  — the capability must land purely through the discover()+OntologyExtension
  contract. If it cannot, that is a finding to escalate, not a core edit to slip in.

## Open Questions / Needs Research

1. **Core vs examples/.** *Re-settled 2026-05-31 → CORE.* This revision flips the
   v1 resolution: novel ships under `agency/capabilities/novel/` (folder-form,
   auto-discovered per Spec 016 Phase 3 — commit `8a5a45d`). Three reasons:
   the Kohärenz-Protokoll repo IS the substrate's primary application (not a
   third-party domain proof — that role stays with `music`), auto-discovery
   removes a host-glue step in marketplace-installed plugin scenarios, and folder
   form is the right shape for a capability with 4+ sub-modules + vendored data.
   Music remains in `examples/` (still the extra_capabilities proof point).
   See **Where it lives** for the full rationale.
2. **Dramatica/NCP vendoring home.** *Re-settled 2026-05-31 →
   `agency/capabilities/novel/data/`* with a `.sha` sidecar (the source repo does
   exactly this). Data is purely the capability's concern; the strict
   ontology-merge needs no awareness of it. Path updated to match the new core
   home (was `examples/novel/data/`).
3. **`jsonschema` dependency.** *Re-settled 2026-05-31 — add as a CAPABILITY
   dependency.* With novel now in core, the question becomes: is `jsonschema` a
   core-level hard dep alongside `fastmcp` + `graphqlite` + `httpx`, or a
   capability-scoped optional dep? Resolution: **capability-scoped** — declared
   as an `optional-dependencies` extra (`novel` or `[novel]`) in `pyproject.toml`
   so `pip install -e ".[novel]"` opts in. The core engine never imports
   `jsonschema`; `_ncp.py` does the lazy import inside `ncp_validate`. This keeps
   core dep-purity intact while letting novel use the real Draft 7 validator
   instead of hand-rolling one (which would be a fidelity regression per Source
   fidelity §3). `requirements-examples.txt` stays as the music-capability seam
   (still in `examples/`), and a new line `jsonschema` lands under the novel
   `[novel]` extra OR a dedicated `requirements-novel.txt` — both pyproject and
   requirements-* files are accepted seams in the agency repo.
4. **v1 scope cut.** *Settled (see scope cut below).* v1 = scaffold + conceptualize +
   `work-concept` gated skill + `dramatica_lookup` + `ncp_validate` + the decidable
   `coherence_check` subset + `pre_drafting_gate` (with override audit).
5. **Disk vs graph source of truth.** *Settled:* graph canonical, `apply=True` is an
   optional disk export `effect`. This is the correct Agency re-architecture (the
   source is disk-first; Agency is graph-first).
6. **Skill walker vs `gate` composition for the 6-gate.** *Settled:* the
   `work-concept` skill's pre-drafting phase DELEGATES to `pre_drafting_gate`
   (one source of truth — verb = programmatic/composable, skill = walkable UI),
   matching the source shipping both a gate tool and a skill.
7. **Reviving the deferred coherence checks.** Open: which (if any) of the
   non-decidable checks can be rebuilt as genuinely-decidable `transform`s once the
   quad reverse-index + signpost-permutation table are constructed from the bundled
   ontology, vs which stay judgement-skills permanently?

### v1 scope cut

**v1 (one capability, prove the contract at fidelity):** `scaffold` (effect,
graph-canonical, `apply=True` export) · `conceptualize` (act) + the `work-concept`
gated skill (hard confirm) · `dramatica_lookup` (transform, navigator port, real
303-entry dataset) · `ncp_validate` (transform, real `jsonschema`, draft-07) ·
`coherence_check` (transform, decidable subset only) · `pre_drafting_gate` (act,
composes the 6 gates, with force-override audit).

**Deferred to v2 (explicit):** `ncp_compile` and `coherence_correct` (both net-new
vs source — see §5) · the non-decidable coherence checks (heuristics → judgement
skills) · `analyze_prose` and the prose-analysis depth · `build_scene_prompt` + the
other 9 prompt-builders · `promote_premise` with `status`/`promoted_to` bookkeeping ·
entity status-transition tables · the `manuscript-revision` + `scene-bridge-audit`
skills · promo authoring · the 32-skill prose catalogue.

This keeps v1 to **two jules sessions** (capability + ontology + data vendoring; then
the gated skill + example + tests), proves the two novelties the spec claims
(vendored dataset through `OntologyExtension`; a real schema-validation `transform`),
and ships something true to the SHIPPED source rather than to its unbuilt specs.

## Evidence

- Exemplar spec format: `/home/user/the-agency-system/Plan/108-context-mode-integration/spec.md`
- Capability catalogue: `/home/user/agency/research/capability-specs/capability-catalogue.md`
  (rows 20-25). The per-capability research stub
  `/home/user/agency/research/capability-specs/specs/novel.md` describes a DIFFERENT,
  superseded `agency/capabilities/narrative.py` (`outline`/`draft`/`review_arc`) and
  is NOT the design landed here — do not follow it.
- Agency extension contract: `/home/user/agency/agency/capability.py`
  (`OntologyExtension`, `CapabilityBase`, `@verb`), `/home/user/agency/agency/ontology.py`
  (`Ontology.extend` strict-merge + enums widen), `/home/user/agency/agency/engine.py`
  (`extra_capabilities` extension point, auto-wiring), `/home/user/agency/agency/skill.py`
  (the walker: progressive disclosure + hard gate), `/home/user/agency/examples/music.py`
  (the domain-capability template this spec follows).
- Source depth — SHIPPED code (the-agency-system @ 0a6a9e71), the ground truth:
  `reference/novel/dramatica/ontology.json` (303 entries, measured),
  `state/schema/ncp.schema.json` (draft-07 `{schema_version, story}`),
  `servers/agency-mcp/src/agency_mcp/lib/dramatica/navigator.py` (the clean
  `dramatica_lookup` port reference),
  `servers/agency-mcp/src/agency_mcp/handlers/novel/coherence.py` (the 11 named
  checks — mostly heuristics) + `.../structure.py` (the PASS stub) +
  `.../gates.py:81–274` (the 6 gates + `force_overrides[]`).
- Source specs (aspirational — the spec deviates from these where the shipped code
  does): `Plan/010-novel-on-disk-layout`, `Plan/011-novel-handlers-core`,
  `Plan/012-dramatica-and-ncp-libs`, `Plan/013-novel-handlers-structural`,
  `Plan/014-novel-gates-and-revision`, `Plan/015-novel-skills-catalogue`,
  `Plan/021-novel-prompt-builder-family`.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- The spec itself was re-based on the post-Spec-016 substrate (commit `a7e9f83` "docs: Spec 010 re-base on post-Spec-016 substrate (novel → core)") — the spec document was updated but no implementation has shipped.
- Spec 016 substrate tools that 010 depends on ARE shipped: `develop.scaffold_capability` (`develop.py:249`) and `plugin.lint_capability` (`plugin.py:279`) both exist and support block-mode linting. Spec 029/030 onboarding tools (`agency_welcome`, `agency_install`, `intent_bootstrap`) also exist.
- `examples/music.py` (the structural template this spec follows) is fully functional as a reference.

### Still to implement
- `agency/capabilities/novel/` directory does not exist at all — no `__init__.py`, `_main.py`, `_layout.py`, `_dramatica.py`, `_ncp.py`, `_coherence.py`.
- `agency/capabilities/novel/data/dramatica_ontology.json` and `ncp.schema.json` — vendored datasets not present.
- All six v1 verbs: `scaffold`, `conceptualize`, `dramatica_lookup`, `ncp_validate`, `coherence_check`, `pre_drafting_gate`.
- `NovelCapability` `OntologyExtension` with 7 node types (`Work`, `Chapter`, `Scene`, `Character`, `Premise`, `Storyform`, `Coherence`), 2 enums, 2 edges (`COHERES_WITH`, `OVERRIDDEN_BY`), 4 artefact schemas.
- `work-concept` conceptualizer skill (7-phase gated).
- `docs/examples/author_a_novel.py` — end-to-end runnable example.
- `tests/test_novel_capability.py`, `tests/test_novel_coherence.py`, `tests/test_novel_skills.py`.
- `requirements-examples.txt` / `[novel]` extra for `jsonschema` dep.

### Refinement needed (given later specs)
- The 2026-05-31 re-base already incorporated Spec 016 (scaffold-first, block-mode lint, `# agency-scaffold: v1` marker) and Spec 029/030 (onboarding surface). No further spec-level refinements are needed before implementation can start — the spec is current.
- The "Where it lives" question is now definitively resolved to `agency/capabilities/novel/` (core, auto-discovered via folder-form `discover()`, Spec 016 Phase 3 commit `8a5a45d`). Music remains the `examples/` proof point.
- Spec 020 (central `.agency/session.db`) is already shipped (`aa345ab`). The graph-canonical storage model the spec requires is therefore available.
- Open Question 7 (which deferred coherence checks can be revived as genuinely-decidable transforms) remains open for v2 work.

### Evidence
- code: `ls agency/capabilities/` — no `novel/` directory; `agency/capabilities/develop.py:249` + `agency/capabilities/plugin.py:279` (Spec 016 substrate ready); `examples/music.py` (template reference)
- tests: none for novel capability
- commits/notes: `a7e9f83` (spec re-base only — doc update, no code); `Plan/000-overview.md` classifies 010 as "Wave-1 backlog"
