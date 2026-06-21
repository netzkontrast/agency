---
spec_id: "354"
slug: adr-ontology-capability
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["353", "293", "292", "339"]
vision_goals: [4, 7, 9]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/adr/__init__.py
  - agency/capabilities/adr/_main.py
  - agency/ontology.py
  - tests/acceptance/features/adr.feature
  - tests/acceptance/test_adr.py
---

# Spec 354 — ADR ontology + `adr` capability

> Child of **353**. The foundation: the strict ontology for architecture
> decisions (the ported WH(Y) format) and the dedicated `adr` capability that
> authors, validates, links, supersedes, and renders them. 355 (DoD gate) and 356
> (extraction/hints) bind onto what this lands.

## Why

The `adr` repo (`/adr/specs/SPEC-001-A..E`) defines the *enhanced WH(Y) ADR* on
paper. Ported faithfully onto agency's substrate it becomes a strict, enforced,
queryable node type plus a handful of verbs — no parallel store, no bespoke
parser. This spec lands the **decision-record primitive** the rest of the
initiative needs: a thematic, bi-temporal, WH(Y)-typed `Decision` whose
dependencies are real graph edges (353's reconciliation #1 and #2).

Without this, "extract decisions from a spec" (356) and "approve before
`/inprogress`" (355) have nothing to write to.

## Design

### Node types (`ontology.py`, contributed via `AdrCapability.ontology`)

**`AdrTheme` — a `Document` with `kind="adr-theme"`, NOT a new node label**
(panel B1, 2026-06-20). The theme is the file-level container for one
architecture layer/theme (the ported *Master ADR*); it has no behaviour a
`Document` lacks (it round-trips to `docs/adr/<id>.md`, `CONFORMS_TO` a Schema,
decisions edge to it). So a theme is a `Document` carrying `id` (`ADR-<slug>`,
e.g. `ADR-datalayer`), `title`, `layer` (the architecture layer), `scope` (the
Master-ADR *scope boundary*). Introducing a separate `AdrTheme` label would be
two nodes for one thing — the substrate already has the primitive. Aggregate
status is **derived**, never stored (rule 8).

**`Decision`** — one architectural decision in WH(Y) form, `PART_OF` exactly one
theme. **Two layers, deliberately separated** (the think-hard-about-ontology-and-Schema
correction, 2026-06-20):

- **Node-required (STORAGE — Memory enforces on `record`):** minimal —
  `["decision", "status"]`. You must state *what* was decided (the record's
  identity) and its state; the rest of the WH(Y) justification is recordable
  **empty**, so a `proposed` skeleton from `extract_decisions` (356) persists and
  is completed incrementally. WHY-001 is an *approval*-gating validation rule, not
  a storage constraint — conflating them would make incremental drafting
  impossible.
- **The `decision` Schema (the typed COMPLETENESS contract — powers `validate`):**
  a **draft-07 schema** whose `required` is the full six WH(Y) elements + `status`
  and whose `properties` carry the per-element `maxLength` budgets (SPEC-001-A;
  tunable — rule 8). `validate` *derives* WHY-001 (required) + WHY-LEN (maxLength)
  from this ONE Schema (rule 2 — no second list). `title: "Decision"` covers the
  node label for the Spec 153 schema-coverage audit.

| WH(Y) element | Source (SPEC-001-A) | Schema `maxLength` (tunable) |
|---|---|---|
| `context` | *In the context of …* | 200 |
| `facing` | *facing …* (non-functional concern) | 250 |
| `decision` | *we decided for …* (also node-required) | 150 |
| `neglected` | *and neglected …* (≥1 alternative) | 200 |
| `benefits` | *to achieve …* | 250 |
| `tradeoffs` | *accepting that …* | 300 |

`status` is the `decision_status` enum. Optional fields: `proposed_by`, `date`,
governance (`review_board`, `review_cadence`, `next_review`). `status_history` is
a *rendered convenience* — the real history is the bi-temporal node chain.
References are **edges** (`REFINES`/`RELATES_TO` to a Spec/Document), not a field.

### Edges

`PART_OF` (Decision→AdrTheme, Spec→AdrTheme), `DEPENDS_ON`, `RELATES_TO`,
`REFINES` (Decision↔Decision, Decision→Spec). `SUPERSEDES` is the **existing**
core edge — reused for decision revision and the ported *supersede* semantics.
Each new edge is declared **and traversed** (`ctx.neighbors(id, edge)`), never a
foreign-key scan (dormant-surface heuristic).

### Enums

`decision_status`: `proposed · under-review · approved · implemented ·
superseded · rejected · retired · expired` (SPEC-001-A status set).
`dependency_type`: `DEPENDS_ON · SUPERSEDES · RELATES_TO · REFINES · PART_OF`
(SPEC-001-C), with the semantics ported verbatim.

### Verbs (class-form `AdrCapability`, `home = "memory"`)

| Verb | Role | Does |
|---|---|---|
| `theme(layer, title, scope)` | act | Create/get an `AdrTheme` + its bound Document. |
| `draft(theme_id, context, facing, decision, neglected, benefits, tradeoffs)` | act | Create a `Decision` (status `proposed`) `PART_OF` the theme, `SERVES` the intent. Validates WH(Y) on write. |
| `validate(decision_id)` | transform | Run **WHY-001..006** + **MIN-001..005** + **DEP-001..005** rules; return `{findings:[{rule, severity, msg}], ok}`. Decidable (length, ≥1 neglected, cycle check, ref-resolves); never an LLM gate. |
| `link(source_id, dependency_type, target_id, note)` | act | Add a typed dependency edge (rejects `DEP-001` cycles, `DEP-003` deps-on-rejected). |
| `supersede(old_id, new_decision_fields…)` | act | Mint the replacement, add `SUPERSEDES`, flip `old → superseded`, write the forward reference (SPEC-001-C automatic actions). |
| `theme_status(theme_id)` | transform | The ported **aggregate-status** calculation over `PART_OF` children (Proposed→In-Progress→Approved→Partially-Implemented→Completed→Blocked). Derived. |
| `impact(decision_id, depth)` | transform | What `DEPENDS_ON`/`REFINES`/`PART_OF` this, to `depth` (SPEC-001-C `adr impact`). |
| `render(theme_id)` | act | Project the theme's **live** decisions → the `docs/adr/<id>.md` Document (`document.render`; rule 2). Only currently-valid decisions appear → the file stays a handful, history stays in the graph. |
| `list(status, layer)` | transform | The "handful of ADRs" index — themes + their decision counts by status. |

`dod_check`, `extract_decisions`, `hints` are deferred to 355/356 (same
capability, separate specs).

### Minimalism enforced, not hoped (SPEC-001-B)

`validate` ports MIN-001..005 as live findings: a theme-render line budget
(MIN-001 "ADR should not exceed N lines" — tunable), "code blocks are examples
not implementations" (MIN-002), "≥1 referenced spec" (MIN-005 → at least one
`REFINES`/`RELATES_TO` edge to a Spec/Document). Implementation detail belongs in
the Spec the decision `REFINES`, never inline (the decision/spec separation is the
whole point of the WH(Y) format).

## Done When

### Slice 1 — ontology + author/validate

- [ ] `AdrCapability` self-registers from `agency/capabilities/adr/`; the
      drop-in bar holds (no edit outside the folder except the documented
      substrate-set update + `# AGENCY-DRIFT` tag — rule 6).
- [ ] `adr.theme` + `adr.draft` create well-formed nodes; the ontology **rejects**
      a Decision missing a WH(Y) field, an unknown `decision_status`, or an
      out-of-enum `dependency_type` (enforced in Memory, CORE.md §schemas).
- [ ] `adr.validate` returns the ported WHY/MIN/DEP findings with correct
      severities; tested against a valid and three invalid fixtures (missing
      element → WHY-001 Error; zero neglected → WHY-003 Error; dependency cycle →
      DEP-001 Error).
- [ ] Acceptance scenarios in `tests/acceptance/features/adr.feature`
      (behaviour, not internals — rule 7).

### Slice 2 — link / supersede / render / aggregate

- [x] `adr.link` enforces DEP-001 (no cycles) and DEP-003 (no deps on rejected).
- [x] `adr.supersede` performs the SPEC-001-C automatic actions (mint replacement,
      flip old → `superseded`, write the `SUPERSEDED_BY` forward reference); the
      old node remains queryable (status `superseded`; the render appendix lists it).
- [x] `adr.theme_status` reproduces the SPEC-001-D aggregate table from children.
- [x] `adr.render` projects only live decisions (+ a collapsed superseded appendix,
      panel B3); re-render is idempotent (stable `content_sha` — Goal 9 round-trip).
- [x] `adr.read` + `adr.update` — the domain read + in-place mutator (the owner's
      "this should be adr.update — manage is a different tool" directive): an ADR's
      status/WH(Y) edits never reach into the generic `manage` capability.
- [x] Substrate-set invariants green with the 7 new verbs added (`scripts/check-drift`
      surface_size / bare-name / skill-parity / token-budget); full suite run before
      declaring done.

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| WH(Y) max-lengths frozen as magic numbers; every legit long decision fails | Lengths are **documented tunable budgets** in config, asserted as `≤ budget`, not `== snapshot` (rule 8) |
| A declared edge (`REFINES`) is written but never traversed → dormant surface | `impact`/`render`/`validate(MIN-005)` all traverse via `ctx.neighbors`; a test asserts traversal |
| `render` overwrites a human-edited ADR file | keep-both: render emits a `DocRevision`; human edits re-ingest, latest `recorded_at` wins, nothing lost (Spec 292) |
| Aggregate status stored, then drifts from children | derived on read, never persisted (rule 8) |

## Interconnects

- **353** master (mapping, reserved ontology, reconciliations).
- **293 (manage)** — generic create/read used under the hood; `adr` adds only
  domain verbs.
- **292 (Document)** — theme files round-trip; `render` is `document.render`.
- **339 (lifecycle)** — decision `status` is advanced via `ctx.lifecycle` in 355.
- **355** consumes `validate` to build the DoD gate; **356** adds
  `extract_decisions`/`hints` to this same capability.

## Spec-panel findings folded in (panel 2026-06-20)

- **B1 (Fowler — conceptual integrity):** `AdrTheme` is **not** a new node label —
  it is a `Document` with `kind="adr-theme"` + a `layer` tag (folded into §Node
  types above). Only `Decision` is a genuinely new label.
- **B5 (Fowler — `Decision` vs `Reflection`):** kept as a distinct label, justified:
  a `Reflection` is an observation/lesson; a `Decision` is a *chosen course with
  neglected alternatives + accepted trade-offs*, gate-able (355) and status-bearing.
  A future audit must not collapse the two.
- **B3 (Newman — audit trail):** `adr.render` emits **current decisions + a
  collapsed "Superseded / history" appendix** (one line per superseded decision:
  id · title · superseded-by · date), so the file is honest about the past without
  re-inflating. The MIN-001 line budget applies to the **active** section only; the
  appendix is an index, the full superseded body stays in the graph (`as_of`). This
  resolves the living-file-vs-minimalism conflict.
- **M1 (Wiegers/Adzic — strict schemas):** each verb's input/output is a registered
  `Schema` node the produced artefact `CONFORMS_TO` (CORE.md generate/validate
  pair), enforced on `record` — not merely documented prose. The owner's
  "super strict schemas" directive is met at the substrate, not on paper.

## Followup — Implementation Status (2026-06-20)

### Done — Slice 1 (TDD, shipped)
- `agency/capabilities/adr/` self-registers (drop-in bar held — only the cap
  folder + `tests/acceptance/{features/adr.feature,test_adr.py}` were hand-written;
  the CLI mirrors, `skills/adr/`, the command, and `plugin.json`/`marketplace.json`
  were auto-generated by `python -m agency.install`).
- Ontology — **two layers** (the think-hard correction): `Decision` node-required
  is minimal `["decision","status"]` (a `proposed` skeleton is recordable); the
  `decision` **draft-07 Schema** carries the completeness contract (all six WH(Y)
  `required` + per-element `maxLength`). `decision_status` enum +
  `PART_OF`/`DEPENDS_ON`/`RELATES_TO` edges (`REFINES` unioned with `discover`'s).
  `AdrTheme` = `Document(kind="adr-theme")` per panel B1.
- Verbs: `adr.theme` (get-or-create the themed Document), `adr.draft` (WH(Y)
  `Decision` `PART_OF` the theme — only `decision` required, rest fillable later),
  `adr.validate` (WHY-001 + WHY-LEN **derived from the Schema**, plus WHY-003).
- **The correction that mattered (owner directive — reread concept + think hard
  about the ontology AND Schema):** an earlier cut made all six WH(Y) elements
  *node-required*; since Memory treats empty == missing, that would have made a
  `proposed` skeleton impossible to record — breaking the incremental
  draft→complete→approve lifecycle Spec 356 needs. Fixed by separating the
  **node storage contract** (minimal) from the **`decision` Schema completeness
  contract** (the full WH(Y), powering `validate`), per CORE.md §Schemas. WHY-001
  + WHY-LEN derive from the one Schema (rules 2 + 8); the DoD gate (355) enforces
  completeness at approval.
- 8 acceptance scenarios green; schema-coverage stays 1.0 (the `decision` Schema
  covers the `Decision` label); install regenerated; drift clean; `spec_id`
  collision with the brooks-port `354-decay` resolved (that leaf renumbered → 360).

### Done — Slice 2 (TDD, shipped)
- `adr.link` — typed SPEC-001-C dependency edges (`DEPENDS_ON` · `RELATES_TO` ·
  `REFINES` · `PART_OF`), enforced at write time: **DEP-001** (no cycle in the
  acyclic edges, via a `ctx.neighbors`-out reachability probe — declared edge ⇒
  traversed) and **DEP-003** (no `DEPENDS_ON` a `rejected` decision). A rejected
  edge is never created; the finding returns `{error, rule}`.
- `adr.supersede` — the SPEC-001-C automatic actions: mint the replacement
  `Decision` (`proposed`) `PART_OF` the same theme, flip the old to `superseded`,
  write the core `SUPERSEDED_BY` forward reference. Old node stays queryable.
- `adr.theme_status` — the SPEC-001-D aggregate (`blocked` / `completed` /
  `partially-implemented` / `approved` / `in-progress` / `proposed`) ported
  verbatim, DERIVED over `PART_OF` children (never stored — rule 8).
- `adr.impact` — incoming `DEPENDS_ON`/`REFINES`/`PART_OF` dependents to `depth`.
- `adr.render` — live decisions → the theme `Document` body + `content_sha`
  stamp; superseded decisions collapse to a one-line history appendix (panel B3);
  deterministic ⇒ idempotent re-render. (Graph-side projection; the file
  round-trip stays `document.sync`'s job — keep-both, Spec 292.)
- **`adr.read` + `adr.update`** (owner directive mid-Slice-2: *"this should be
  adr.update — manage is a different tool"*): the capability owns its read +
  in-place mutator, so an ADR's status/WH(Y) edits never reach into the generic
  `manage` tool. `update` writes only non-empty args (incremental completion);
  status is `param_enums`-hinted on the wire (strict-schema directive).
- 7 new verbs; **15 acceptance scenarios green** (8 Slice 1 + 7 Slice 2);
  `scripts/check-drift` clean after `python -m agency.install` regenerated the
  `bin/` mirrors + `skills/adr/references/*` for the new verbs.

### Done — Slice 3 (TDD, shipped 2026-06-21)
- `adr.catalogue(status="", layer="")` — the "handful of ADRs" index (SPEC-001-B
  minimalism): every theme + its `PART_OF` decision counts grouped by status,
  filterable by layer/status. (Named `catalogue` not `list` — Spec 074 bare-name
  collision discipline; the collision-with-`music` count is auto-accepted.)
- `validate` deepened with two more ported decidable rules (grounded in the ADR
  reread): **WHY-005** (warn — tradeoffs must be substantive, not an empty
  acknowledgement; fires on non-empty-but-flimsy, since empty is already WHY-001)
  and **MIN-005** (info — a decision should `REFINES`/`RELATES_TO` ≥1 spec
  Document; traversed, not a foreign-key scan). Both additive (warn/info — never
  flip `ok`), so existing scenarios stay green.
- 3 acceptance scenarios; adr+dod+extract 30 green; schema-coverage 44 green;
  check-drift clean (regen committed).

### Slice 4 — panel M1 (per-verb Schema nodes): RESOLVED as already-satisfied (2026-06-21)
Reviewed against the frugal floor + `intent.brooks_lint` (Spec 359) under the
owner's "all slices" directive. **Decision: do NOT mint a registered `Schema`
node per verb's return dict.** M1's intent — "strict schemas at the substrate,
not on paper" — is already met:
- the **`decision` draft-07 Schema** is the typed contract for the one durable
  artefact (the `Decision`), powering `validate` (WHY-001/LEN);
- the **ontology node-required + enums** enforce the storage contract on `record`;
- **`param_enums`** (status, dependency_type, to_state) surface the closed sets on
  the wire (`get_schema`), and code-mode `get_schema` already exposes every verb's
  I/O signature.
A registered Schema node per verb *return* would be **dead surface** — nothing
consumes it (no `CONFORMS_TO` reader for a transient dict) — i.e. the
essential-vs-accidental / second-system smell the Brooks-lint we just shipped
flags. The strict-schema directive is honoured by the data contracts, not by
ceremony. (The remaining MIN-001..004 + WHY-002/004/006 rules need render/LLM and
stay out of the decidable validate set.)
