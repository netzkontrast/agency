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

**`AdrTheme`** — the file-level Document for one architecture layer/theme (the
ported *Master ADR*). Required fields: `id` (`ADR-<slug>`, e.g. `ADR-datalayer`),
`title`, `layer` (the architecture layer), `scope` (the Master-ADR *scope
boundary*). A theme is bound to a `Document` (Spec 292) so it round-trips to
`docs/adr/<id>.md`. Aggregate status is **derived**, never stored (rule 8).

**`Decision`** — one architectural decision in WH(Y) form, `PART_OF` exactly one
`AdrTheme`. Required fields (the six WH(Y) elements are first-class, not prose):

| Field | Source (SPEC-001-A) | Tunable max (documented, overridable — rule 8) |
|---|---|---|
| `id` | `ADR-NNN` (monotonic) | — |
| `context` | *In the context of …* | 200 |
| `facing` | *facing …* (non-functional concern) | 250 |
| `decision` | *we decided for …* | 150 |
| `neglected` | *and neglected …* (≥1 alternative) | 200 |
| `benefits` | *to achieve …* | 250 |
| `tradeoffs` | *accepting that …* | 300 |
| `status` | `decision_status` enum | — |
| `proposed_by`, `date` | governance header | — |

Optional governance fields (SPEC-001-A/E): `review_board`, `review_cadence`,
`next_review`, `status_history` (an append-only list — but the *real* history is
the bi-temporal node chain, so `status_history` is a rendered convenience, not a
second source). Optional `references` — but references are better as **edges**
(`REFINES`/`RELATES_TO` to a Spec/Document), per the dormant-edge heuristic.

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

- [ ] `adr.link` enforces DEP-001 (no cycles) and DEP-003 (no deps on rejected).
- [ ] `adr.supersede` performs all three SPEC-001-C automatic actions and the
      old node remains queryable as history (`as_of`).
- [ ] `adr.theme_status` reproduces the SPEC-001-D aggregate table from children.
- [ ] `adr.render` writes a Document containing only live decisions; re-render is
      idempotent (Goal 9 round-trip).
- [ ] Substrate-set tests (`test_naming_audit`) green with `adr` added; full suite
      (not just the slice) run before declaring done.

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

## Followup — Implementation Status (2026-06-20)

### Done
- Spec authored (design depth).

### Still
- Implement Slice 1 (ontology + author/validate) via TDD, then Slice 2.
- Update the documented substrate set + `scripts/check-drift` when the cap lands.
