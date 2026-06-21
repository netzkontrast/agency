---
spec_id: "353"
slug: adr-agency-port
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["290", "292", "293", "307", "091", "092", "018", "339", "047"]
vision_goals: [2, 6, 7, 9]
domain: core
wave: adr-workflow
affects:
  - Plan/360-adr-ontology-capability/spec.md
  - Plan/355-adr-definition-of-done-gate/spec.md
  - Plan/356-spec-decision-extraction/spec.md
  - Plan/357-spec-state-lifecycle/spec.md
  - Plan/358-workflow-capability/spec.md
  - Plan/359-brooks-lint/spec.md
---

# Spec 353 — ADR × agency port (master)

> **Master spec.** Decomposes the port of the `adr` repository (the *enhanced
> WH(Y) ADR format*) into agency, and the new repo-development **workflow** that
> puts ADRs at its centre. Children: **360** (ADR ontology + capability),
> **355** (Definition-of-Done gate + governance lifecycle), **356** (spec→decision
> extraction + architecture-hint loading), **357** (spec-state lifecycle: physical
> folders + graph mirror), **358** (the `workflow` capability), **359**
> (Brooks-lint). This master owns the mapping, the doctrine reconciliations, the
> reserved ontology, and the sequencing; each child owns its slice.

## Why

Owner directive (2026-06-20): *"Completely port the `adr` repo into agency —
deeply interwoven with every agency function. Then go beyond it: build a
**lifecycle for working on the repo itself** — intent capture → interview/triage
→ brainstorm → research (incl. CodeGraph over what already exists) → acceptance
criteria → spec → spec-panel → (new) deeper **Brooks-lint** → improve, looped
until the design is good → then implementation. Specs move through physical
**Plan/ state folders** (`/draft /open /inprogress /superseded /done`). ADRs play
a **central** role: when a spec lands in `/open`, an MCP tool extracts its key
decisions into an **ADR draft**; only once that draft is approved may the spec
move to `/inprogress`. ADRs are organised by **theme / architecture layer** and
**extended inline** — only a handful exist, indexed, with correct frontmatter,
existing primarily to **extract code + architecture hints loaded into context at
the start of implementation.** Strict schemas; a dedicated MCP tool per workflow
step, chainable."*

The `adr` repo (`/adr`) is a paper spec: an enhanced ADR mode (WH(Y) 6-part
decision statement, ADR-minimalism, typed dependencies, Master ADRs, an extended
Definition of Done). It defines a CLI (`adr new …`) and a YAML mode flag, but no
implementation. agency already owns the substrate that makes all of it *free*:

| `adr` concept | agency substrate it lands on |
|---|---|
| WH(Y) 6-part statement, status enum, governance fields | a **strict ontology node schema** (enforced on `record`/`update`, Spec 293 / `ontology.py`) |
| Dependency types `DEPENDS_ON · SUPERSEDES · RELATES_TO · REFINES · PART_OF` | **graph edges** — `SUPERSEDES` already exists in the core edge set |
| Extended Definition of Done (ECADR + Dp/Rf/M) | a **Gate** (`gate` cap + `ctx.elicit`, CORE.md §"Gates are elicit steps") |
| ADR / spec markdown files | **Documents** — keep-both, bi-temporal round-trip (Spec 292) |
| Master-ADR aggregate status | a **derived read** over `PART_OF` (Spec 290 read-API style) |
| WHY/MIN/DEP/MADR/DOD validation rules | `validate` / `check` **transform** verbs |
| `adr new` / `adr link` / `adr supersede` CLI | **capability verbs**, auto-exposed over MCP + bash CLI (Goal 5) |
| status transitions (Proposed→Approved→…→Retired) | a **Lifecycle** (`open · move · close`, Spec 339) |

So the port is not a re-implementation — it is a **binding** of a documented
format onto primitives agency already ships. That is exactly the CORE.md claim
("this is how a real capability ports: its verbs + its schemas/templates + its
pipeline") proven on a third-party paper standard.

**Beyond the port (the owner's larger goal):** the WH(Y) decision record is the
*missing artefact* between a spec and its code. agency records provenance
(`Invocation SERVES intent`) and round-trips Documents, but it has never captured
**"what did we decide, and why, and what did we neglect"** as a first-class,
queryable, gate-able node — the thing whose **code + architecture hints** should
be re-loaded into context the moment implementation begins. This initiative makes
that decision-record the spine of the repo's own development loop (Goal 6 —
doctrine evolves through dogfooding; the loop now *closes* through an approved
decision, not just a Reflection).

## Design

### Doctrine reconciliations (the four decisions, owner-confirmed 2026-06-20)

1. **ADR lives in a dedicated `adr` capability** (`agency/capabilities/adr/`), not
   in `manage`. `manage` is deliberately capability-**agnostic** generic CRUD
   (Spec 293); ADR-specific verbs (WH(Y)-validate, extract-decisions,
   supersede-with-forward-ref, aggregate-status, DoD-gate, hint-extraction) would
   break that charter. ADR nodes are still *created/read* through the generic
   `manage` surface where that suffices; `adr` adds only the domain verbs. This
   honours the drop-in-capability bar (Goal 4).

2. **Thematic, living ADRs — extended inline, not one-immutable-file-per-decision.**
   Classic ADR (and the ported WH(Y) spec) says *one decision per file, immutable
   once approved*. The owner wants a **handful** of ADRs organised by architecture
   **layer/theme**, each grown inline. We reconcile via the bi-temporal substrate:
   an **`AdrTheme`** is the file-level Document (e.g. *Datalayer*, *Substrate*,
   *Capabilities*, *Lifecycle*, *Workflow*); each individual decision is a
   **`Decision`** node (full WH(Y)) `PART_OF` the theme. "Extended inline" =
   appending a new `Decision`; "immutable" is preserved at the *node* grain
   (a revised decision `SUPERSEDES` its predecessor, history retained — keep-both,
   Spec 292). The ADR **file** renders the theme's currently-live decisions
   (`document.render`), so there stay only a handful of files while full decision
   history lives in the graph. The theme is the ported **Master ADR** machinery
   (aggregate status over its children).

3. **Spec-state = physical folders + graph mirror, grandfathering the legacy 339.**
   New specs flow through physical `Plan/<state>/NNN-slug/` folders
   (`draft · open · inprogress · superseded · done`); a `SpecLifecycle` node
   mirrors the state in the graph (keep-both — the folder is the human surface,
   the node is the queryable spine). The 339 existing flat `Plan/NNN-slug/` are
   **not** mass-moved (a high-risk link/history churn); they are indexed in place
   with a `state:` frontmatter field, and an *optional* later migration may move
   them. (Spec 357.)

4. **This master + all six children are authored at design depth this cycle**, with
   TODO.md rows; implementation is sequenced as follow-up TDD per child.

### Decomposition & sequencing

```
353 (this master)
 ├─ 360  ADR ontology + `adr` capability      ← foundation; everything binds here
 ├─ 355  Definition-of-Done gate + governance ← depends on 360
 ├─ 356  spec→decision extraction + hints     ← depends on 360, 355
 ├─ 357  spec-state lifecycle (folders+graph)  ← independent of 360; needed by 358
 ├─ 358  `workflow` capability (orchestration) ← depends on 355–357, 360, 359
 └─ 359  Brooks-lint critical-thinking pass    ← extends 091/092; used by 358
```

**Build order:** 360 → 355 → (357 ‖ 359) → 356 → 358. 357 and 359 have no
dependency on the ADR core and can land in parallel; 358 is the capstone that
chains all of them into one walkable lifecycle.

### Two new capabilities + one new critical-thinking method

- **`adr`** (355, 356, 360) — the decision-record craft: draft · validate · link ·
  supersede · theme_status · render · impact · dod_check · extract_decisions ·
  hints.
- **`workflow`** (357–358) — the repo-development lifecycle: the spec-state verbs
  (`move_spec`, `index`) + the walkable `develop-spec` skill that chains
  discover → develop → panel → brooks-lint → adr → develop.
- **`intent.brooks_lint`** (359) — a 9th critical-thinking method
  (conceptual integrity, essential vs accidental complexity, second-system
  effect), surfaced as a panel/lint pass in the improve-loop.

Adding two capabilities changes the **documented substrate set** — the children
must update the naming-audit substrate list, `scripts/check-drift`, and the
generated capability docs (CLAUDE.md rules 5, 6); this master flags it so no
child forgets (the "full suite on a migration" heuristic).

### Reserved ontology (children bind it; reserved here to avoid collision)

- **Nodes:** `Decision`, `SpecLifecycle` (+ reuse `Gate`, `Document`, `Intent`,
  `Lifecycle`, `Reflection`). **`AdrTheme` is NOT a new label** — it is a
  `Document` with `kind="adr-theme"` + a `layer` tag (panel B1, 2026-06-20); the
  theme has no behaviour a `Document` lacks.
- **Edges:** `PART_OF` (Decision→AdrTheme; Spec→AdrTheme), `DEPENDS_ON`,
  `RELATES_TO`, `REFINES` (Decision↔Decision, Decision↔Spec); reuse existing
  `SUPERSEDES`, `SERVES`, `PRODUCES`, `CONFORMS_TO`.
- **Enums:** `decision_status` (proposed · under-review · approved · implemented ·
  superseded · rejected · retired · expired), `spec_state` (draft · open ·
  inprogress · superseded · done), `dependency_type` (the five above).
- **Skills:** `develop-spec` (the workflow Lifecycle template).

## Done When

### Slice 1 — the spec set is authored (this cycle)

- [ ] Children 355–360 exist as `Plan/NNN-…/spec.md` with valid frontmatter and
      the standard sections (Why / Design / Done When / Failure modes /
      Interconnects / Followup).
- [ ] This master's mapping table, reconciliations, sequencing, and reserved
      ontology are stable enough that a child can be implemented without
      re-litigating a cross-cutting decision.
- [ ] `TODO.md` carries a row per new spec (353–359), all `Not started`/`draft`.
- [ ] `Plan/000-overview.md` lists the `adr-workflow` wave.

### Slice 2 — the children ship (follow-up, tracked per child)

- [ ] 360 → 355 → 357 ‖ 359 → 356 → 358 land green per their own acceptance.
- [ ] An end-to-end dogfood proves the loop: a fresh intent walked through
      `workflow.develop-spec` produces a spec in `/draft`, panel+Brooks-lint
      findings folded, the spec moved to `/open`, decisions extracted into a
      theme ADR draft, the DoD gate approved, the spec moved to `/inprogress`
      with architecture hints loaded — every step recorded as provenance under
      the one intent.

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| Two new caps (`adr`, `workflow`) drift the substrate set; naming-audit/`check-drift` go red on merge | Each child updates the documented set + `# AGENCY-DRIFT` tags in the same commit; this master names the obligation (rule 6) |
| Thematic ADRs become a dumping ground — one giant file, the minimalism win lost | 360 ports MIN-001..005 as live `validate` rules (theme line budget, "decisions not implementations"); the file renders *live* decisions only |
| The ADR-approval gate (356) blocks all spec progress if it is too strict or unkeyed | Gate is a `ctx.elicit` human step (no API key needed); the predicate is "drafted decisions approved", not "perfect" — and `workflow` can record an explicit owner override (provenance-stamped) |
| The port reimplements the `adr` CLI surface verbatim and bloats | Bind, don't reimplement: verbs over the substrate; the bash CLI mirror is auto-generated (Goal 5), so `adr new`-style ergonomics come free |
| Master + 6 specs over-scope a single review | Design depth only this cycle; implementation is per-child TDD with its own PR-sized acceptance |

## Interconnects

- **292 (Document)** — ADRs/specs are Documents; render/ingest/sync is the
  graph↔file bridge the thematic-ADR model rides on.
- **293 (manage)** — generic CRUD the `adr` verbs lean on; the boundary this
  master draws (agnostic CRUD vs domain verbs) is the rationale for a dedicated cap.
- **290 (read-API / manage rollups)** — aggregate theme status & "what's blocked"
  reuse the read-projection style.
- **307/308 (discover)** — the interview/triage step of the workflow (358) is the
  discover capability finally driven end to end.
- **091/092 (critical-thinking methods)** — Brooks-lint (359) is the 9th method.
- **018 (skill walker)** — `develop-spec` is a Lifecycle template walked one phase
  at a time, each phase recorded.
- **339 (lifecycle pillar)** — decision-status and spec-state are Lifecycles via
  `ctx.lifecycle.open/move/close`.
- **047 (cluster-integration)** — the workflow spans the *plan/spec/review/build*
  clusters; this initiative is their coherent through-line.

## Spec-panel findings folded in (panel 2026-06-20)

Full review: [`spec-panel-review.md`](spec-panel-review.md). Resolutions folded
into the children:

- **B1 — conceptual integrity (two constructs the substrate already covers):**
  `AdrTheme` → a `Document` kind (above + 360); `develop-spec` recommended as a
  `develop` discipline rather than a new `workflow` capability (358, owner decides
  the home). The set passing its own Spec 359 Brooks-lint is the validation.
- **B2 — the ADR hinge's three failure paths:** approver = intent owner, no
  agent self-approve (355); zero-decision specs return `ready=false`, never a
  vacuous pass (356); the improve-gate has a decidable exit criterion (358).
- **B3 — audit trail:** `adr.render` keeps a collapsed superseded-history
  appendix (360).
- **M1 — strict schemas:** verb I/O are registered `Schema` nodes, not prose
  (360/356), satisfying the owner's "super strict schemas" directive.
- **Theme-creation rule:** a theme == an architecture **layer** (the reserved
  set: Datalayer · Substrate · Capabilities · Lifecycle · Workflow). A new theme
  is an **owner decision**, never an extraction default — `extract_decisions`
  (356) routes to an existing theme or flags `theme=unrouted` for the owner. This
  is what keeps "only a handful of ADRs" true.

## Followup — Implementation Status (2026-06-20)

### Done — Slice 1
- Master + children 355–360 authored at design depth + spec-panel reviewed
  (critique mode) and findings folded (this branch).

### Still — Slice 2
- Implement children in build order (360 first). Each is its own TDD PR.
- End-to-end dogfood of `workflow.develop-spec` (the Slice-2 acceptance above).
