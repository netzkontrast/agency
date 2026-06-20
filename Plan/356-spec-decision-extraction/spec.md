---
spec_id: "356"
slug: spec-decision-extraction
status: draft
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

- [ ] `adr.extract_decisions(spec_id, apply=False)` returns WH(Y) candidates with
      an `evidence_span` pointing back into the spec body; decidable path works
      with **no API key** (LLM only sharpens when keyed).
- [ ] `apply=True` drafts `Decision` nodes `REFINES`→spec, `PART_OF`→theme, status
      `proposed`; idempotent re-run does not duplicate (keyed on evidence_span +
      theme).
- [ ] `adr.spec_decisions_ready(spec_id)` returns `ready=false` while any linked
      decision is unapproved, `true` once all are `approved` (355).
- [ ] Acceptance: a fixture spec → candidates → drafts → blocked-ready → approve →
      ready (behaviour, rule 7).

### Slice 2 — hints / context loading

- [ ] `adr.hints(spec_id, budget)` returns a token-bounded hint block over approved
      decisions + depth-1 neighbours; the block fits the budget (`returned_tokens
      ≤ budget`) and sets `truncated` honestly — but the underlying `Decision`
      nodes are stored in **full** (rule 9; the budget governs the *projection*).
- [ ] Theme inference from `affects`/`domain` is covered; multi-theme specs route
      candidates independently.

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

## Followup — Implementation Status (2026-06-20)

### Done
- Spec authored (design depth).

### Still
- Implement Slice 1 (extract + ready predicate), then Slice 2 (hints) via TDD.
