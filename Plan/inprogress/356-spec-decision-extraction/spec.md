---
spec_id: "356"
slug: spec-decision-extraction
status: draft
state: inprogress
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["354", "355", "292", "290"]
vision_goals: [2, 6, 9]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/adr/_main.py
  - tests/acceptance/features/adr_extract.feature
  - tests/acceptance/test_adr_extract.py
---

# Spec 356 — spec→decision extraction + architecture-hint loading

> Child of **353**, builds on **354/355**. The hinge the owner asked for: when a
> spec lands in `/open`, an MCP tool **extracts its key decisions into an ADR
> draft**; the spec may not advance to `/inprogress` until that draft is
> approved (355). And the payoff — at the start of implementation, the approved
> decisions' **code + architecture hints** are loaded into context.

## Why

Owner directive: *"ADRs play a central role — sobald specs in `/open` liegen,
sollen automatisch die wichtigsten Entscheidungen aus der Spec herausgefiltert
und in eine ADR-Draft übertragen werden; erst wenn diese freigegeben wird, kann
die Spec in `/inprogress`. … ADRs existieren primär, um daraus Code- und
Architektur-Hints zu extrahieren und diese beim Beginn der Umsetzung in den
Kontext zu laden."*

A spec already contains its decisions — buried in prose under `## Why`,
`## Design`, and the spec-panel/Brooks-lint findings. Today that signal is lost
the moment implementation starts; the implementer re-derives intent from scratch.
This spec turns those decisions into **first-class, approved, queryable
`Decision` nodes** (354) and then **re-projects** them — distilled to code +
architecture hints — into the implementer's context. That closes Goal 6 (the
loop ends in an approved decision, not just a Reflection) and Goal 2 (the
decisions are provenance, traversable from the intent).

## Design

### Verb: `extract_decisions(spec_id, theme_id="", apply=False)` — role `transform` (preview) / `act` (apply)

1. **Ingest the spec as a Document** (Spec 292 `document.ingest`) if not already —
   the body is the source.
2. **Surface decision candidates** from the structured sections. The extractor is
   **decidable-first, LLM-optional** (barbell, like Spec 352):
   - *Decidable signals* (no key): the `## Design` subsections; sentences matching
     decision cues (*"we decided / chose / will use / neglected / instead of /
     trade-off / accepting that"*); the ported WH(Y) skeleton is partly pre-filled
     from `## Why` (context/facing) and `## Design` (decision/neglected) and
     `## Failure modes` (tradeoffs).
   - *LLM refinement (optional)*: when `OPENROUTER_API_KEY` is present, `ctx.sample`
     sharpens each candidate into a clean 6-part WH(Y) statement. Without a key the
     decidable skeleton is emitted for the human to complete (never a silent gap).
3. **Theme routing.** `theme_id` may be given; else infer the architecture
   layer/theme from the spec's `domain`/`wave`/`affects` paths (e.g. paths under
   `agency/memory*` → *Datalayer*; `capabilities/` → *Capabilities*). One spec's
   decisions may span themes (each candidate routed independently).
4. **`apply=False`** (default) returns a preview: `{spec_id, candidates:[{theme,
   context, facing, decision, neglected, benefits, tradeoffs, evidence_span}]}` —
   token-budgeted (rule 9: never truncate the *stored* record, but a *preview* may
   be budgeted, like `manage.project`). **`apply=True`** drafts each candidate as a
   `Decision` (354 `adr.draft`, status `proposed`) `PART_OF` its theme and
   `REFINES` ← the spec, recording provenance.

The verb is **chainable**: `apply=False` → human edits the candidates →
`apply=True` → `adr.approve` (355). Each is its own MCP tool, composable in one
`execute` block.

### The `/open → /inprogress` predicate (enforced by 358)

A spec in `/open` carries `REFINES`-linked draft Decisions. The workflow's
`move_spec(spec, "inprogress")` (357/358) calls a predicate here:

`adr.spec_decisions_ready(spec_id)` — role `transform` → `{ready: bool,
decisions:[{id, status}], blocking:[ids not yet approved]}`.

`ready` is true iff **≥1** `Decision` `REFINES` the spec AND every such decision
is `approved` (355 gate). This is the mechanism behind "erst wenn freigegeben →
`/inprogress`".

**Zero-decision specs (panel B2.2).** A docs-only or trivial spec from which
extraction surfaced **no** decisions returns `{ready: false, reason:
"no-decisions"}` — it does **not** vacuously pass the gate. The owner clears it
with an explicit ack (a provenance-stamped `move_spec` override, 357), so a spec
can never skip the hinge by simply having nothing extracted. "No decisions" is a
decision the owner makes, not a default the system makes for them.

### Verb: `hints(spec_id, budget=2000)` — role `transform` (the payoff)

At implementation start, gather the **approved** decisions linked to the spec
(and the transitive `DEPENDS_ON`/`REFINES` neighbours, to `depth=1`) and project a
compact **architecture-hint block**:

```
{spec_id, themes:[…], hints:[
   {decision_id, theme, decision, why: <facing→benefits>,
    constraints: <tradeoffs>, touches: <affects/CONFORMS_TO targets>,
    related: [decision_ids]}],
 returned_tokens, truncated}
```

It reuses the `manage.project(query, budget)` ranking + token-budget split
(Spec 290) so the block is a **bounded delta**, never a dump — this is what
`workflow.develop-spec` loads into the implementer's context at the build phase
(358). The hints are *decisions and their consequences*, not the spec re-stated:
the minimum an implementer needs to not contradict an approved decision.

## Done When

### Slice 1 — extract + ready-predicate

- [x] `adr.extract_decisions(spec_id, apply=False)` returns WH(Y) candidates with
      an `evidence_span` pointing back into the spec body; decidable path works
      with **no API key** (canonical WH(Y) statement parsed verbatim — Layer 1; LLM
      sharpening deferred to Slice 2). `spec_id` accepts a Document id OR a
      frontmatter `spec_id` (owner directive).
- [x] `apply=True` drafts `Decision` nodes `REFINES`→spec, `PART_OF`→theme, status
      `proposed`; idempotent re-run does not duplicate (keyed on evidence_span).
- [x] `adr.spec_decisions_ready(spec_id)` returns `ready=false` while any linked
      decision is unapproved, `true` once all are `approved` (355); zero-decision
      spec → `{ready:false, reason:"no-decisions"}` (no vacuous pass).
- [x] Acceptance: a fixture spec → candidates → drafts → blocked-ready → approve →
      ready (behaviour, rule 7).

### Slice 2 — hints / context loading

- [x] `adr.hints(spec_id, budget)` returns a token-bounded hint block over approved
      decisions + depth-1 `DEPENDS_ON` neighbours; the block fits the budget
      (`returned_tokens ≤ budget`, via the shared `budget_take` split) and sets
      `truncated` honestly — the underlying `Decision` nodes stay **full** (rule 9;
      the budget governs only the projection). Only `approved` decisions appear.
- [x] Theme inference from the spec's `domain` frontmatter (newline-agnostic regex,
      since the graph store flattens the DocRevision body) — `extract_decisions`
      with no `theme_id` files decisions under the inferred-layer theme.
- [ ] Per-candidate multi-theme routing (one spec's decisions spanning several
      themes) — needs a classifier; deferred.

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| Extraction hallucinates decisions the spec never made | Decidable path is evidence-anchored (`evidence_span`); LLM output is a *candidate* a human approves via 355, never auto-approved |
| No API key → extraction silently empty | Decidable skeleton always emits; missing fields are marked for the human, never dropped (rule 9) |
| `hints` re-states the whole spec, blowing the context budget | `hints` projects *decisions + consequences* via `manage.project` budget split; asserted `returned_tokens ≤ budget` |
| Re-running extraction duplicates drafts | Idempotency key (evidence_span + theme); re-run updates, never re-creates |
| Predicate blocks `/inprogress` forever if a theme is mis-routed | `spec_decisions_ready` lists `blocking` ids so the human sees exactly what to approve or re-route |

## Interconnects

- **354** — drafts via `adr.draft`; links via `REFINES`/`PART_OF`.
- **355** — `spec_decisions_ready` reads the approval Gate; "ready" == all approved.
- **292 (Document)** — the spec body is ingested as the extraction source.
- **290 (manage.project)** — the budgeted hint projection reuses the ranking/split.
- **358 (workflow)** — calls `extract_decisions` on entry to `/open`,
  `spec_decisions_ready` to guard `/inprogress`, and `hints` at the build phase.

## Followup — Implementation Status (2026-06-21)

### Done — Slice 1 (TDD, shipped)
- **`adr.extract_decisions(spec_id, theme_id="", apply=False)`** — decidable,
  evidence-anchored extraction (no API key), grounded in a **reread of the ADR
  source repo** (owner directive "deeply reimplement it"). **Layered fidelity:**
  - *Layer 1 (canonical):* an explicit **WH(Y) statement** (the six SPEC-001-A
    marker phrases — *In the context of / facing / we decided for / and neglected
    / to achieve / accepting that*) is parsed **verbatim** into a complete 6-part
    candidate. Fires only when ALL six markers are present (never on prose that
    merely contains "facing"). This is the format ADR-001 itself demonstrates.
  - *Layer 3 (fallback):* `## Design` decision-cue sentences (*we decided / chose
    / instead of / rather than …*) mined into candidates, with `context` from
    `## Why` and `tradeoffs` from `## Failure modes`; `neglected` split from the
    in-sentence marker. Every candidate keeps an `evidence_span` (anti-
    hallucination anchor + idempotency key).
  - `apply=True` drafts each NEW candidate as a `proposed` `Decision`
    `REFINES`→spec + `PART_OF`→theme; **idempotent** (re-apply skips spans already
    linked). `spec_id` resolves **either a Document id OR a frontmatter `spec_id`**
    (owner directive) via `_resolve_spec`.
- **`adr.spec_decisions_ready(spec_id)`** — the /open→/inprogress predicate:
  `ready` iff ≥1 `Decision` `REFINES` the spec AND every one is `approved` (355
  gate); a zero-decision spec returns `{ready:False, reason:"no-decisions"}` —
  never a vacuous pass (panel B2.2).
- **4 acceptance scenarios** (`adr_extract.feature`): evidence-anchored preview ·
  idempotent apply (exactly two) · not-ready-until-approved (owner-override path,
  since extracted skeletons fail the automated DoD) · zero-decision no-vacuous-pass.
  adr+dod+extract 25 green; schema-coverage 44 green; check-drift clean.
- **Discovered constraint (noted, out of scope):** the graph store returns a
  `DocRevision`'s `text` with newlines **flattened to spaces**, so extraction is
  newline-agnostic (substring-anchored `## ` section parsing + the marker-based
  WH(Y) parser). A faithful document round-trip may want to preserve newlines —
  tracked for a `document`/Spec 292 follow-up, not this slice.

### Done — Slice 2 (TDD, shipped 2026-06-21)
- `adr.hints(spec_id, budget=2000)` — the payoff verb (owner vision: "ADRs exist
  primarily to extract code + architecture hints loaded into context at
  implementation start"). Projects the spec's **approved** decisions (+ depth-1
  `DEPENDS_ON` neighbours) into a token-BOUNDED block `[{decision_id, theme,
  decision, why (facing→benefits), constraints (tradeoffs), touches, related}]`
  via the shared `budget_take` split (`agency/_overflow.py`) + the `count_tokens`
  boundary (`agency/_tokens.py`) — reuse, not a second ranker (rule 2). Only
  `approved` decisions appear (a `proposed` draft is not yet a constraint); the
  stored Decision nodes stay full (rule 9 — the budget governs only the
  projection). `returned_tokens ≤ budget`; `truncated` honest. 2 acceptance
  scenarios (empty-until-approved · token-bounded over approved); extract suite
  6 green; adr+dod+schema 65 green.

### Still — later
- Per-candidate multi-theme routing from `affects`/`domain` (Slice 1+2 file all
  candidates/hints under one get-or-created theme).
- Optional LLM sharpening of candidates when `OPENROUTER_API_KEY` present
  (decidable skeleton stands without a key — barbell).
- Faithful SPEC-001-E weighted scoring + the remaining WHY-002/004/005/006
  validate rules (354 refinement).
