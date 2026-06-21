# Spec-panel review — ADR × agency port (353–359)

> **Mode:** critique · **Date:** 2026-06-20 · **Scope:** master 353 + children 355–360.
> **Panel:** Fowler (architecture/boundaries) · Newman (evolution/versioning) ·
> Nygard (failure modes/operations) · Wiegers (requirement quality) · Adzic
> (testable examples) · Cockburn (actors/goals) · Crispin (test/edge cases).
> **Focus:** conceptual integrity with the four concepts · the ADR-approval
> hinge · the thematic-living-ADR reconciliation · workflow-vs-develop coherence.

## Quality assessment (initial → after fold)

| Spec | Clarity | Completeness | Conceptual integrity | Verdict |
|---|---|---|---|---|
| 353 master | 8.5 | 8.0 | 7.5 → 8.5 | refine (theme-creation rule) |
| 360 ADR ontology | 8.0 | 7.5 | 6.5 → 8.0 | **refine (B1, B3, B5)** |
| 355 DoD gate | 8.0 | 7.0 → 8.0 | 8.0 | refine (B2 approver) |
| 356 extraction | 8.0 | 7.0 → 8.0 | 8.0 | refine (B2 zero-decision) |
| 357 spec-state | 8.5 | 8.5 | 8.5 | accept |
| 358 workflow | 7.5 | 7.5 | 6.5 → 8.0 | **refine (B1, B2 gate, M2 stale)** |
| 359 Brooks-lint | 8.0 | 8.0 | 8.0 | accept (M3 note) |

## Blockers (folded)

### B1 — Conceptual integrity: two new constructs the substrate may already cover (Fowler)
> *"`AdrTheme` is described as 'the file-level Document'. You have introduced a new
> node type AND bound it to a `Document` — that is two nodes for one thing. And
> `workflow` is a new capability whose `develop-spec` skill mostly re-binds
> `develop`'s own disciplines (brainstorm/plan/spec-panel/tdd already live in
> `develop`). Run Spec 359's own Brooks-lint on this set: is the new structure
> essential, or accidental?"*

- **AdrTheme → a `Document` with `kind="adr-theme"` + a `layer` tag**, not a new
  node type. The theme has no behaviour a Document lacks; it round-trips, it
  `CONFORMS_TO` a Schema, decisions edge to it. Keep `Decision` (genuinely new —
  see B5); drop `AdrTheme` as a distinct label. **Folded into 360.**
- **`develop-spec` should be a `develop` discipline, not a new capability** — it
  joins brainstorm/plan/tdd/spec-panel/review/execute/plan-execute as a peer
  Lifecycle template (where it coheres). Only the genuinely-new **spec-state
  surface** (`move_spec`/`index`/`board`) needs a home — and that is closer to
  `manage`/`develop` than a standalone cap. **Recommendation folded into 358 as
  the primary open decision**; owner framed this as "the workflow capability
  thing", so the spec now presents *discipline-in-`develop`* as the recommended
  shape with the new-cap option preserved for the owner to pick at implementation.

### B2 — The ADR hinge has three under-specified failure paths (Nygard, Cockburn, Crispin)
> *"Who approves an ADR in an autonomous remote-async session? What happens when a
> spec has no architectural decisions? And what, precisely, makes the improve-loop
> 'design good'? Each is a place the loop stalls or silently skips its own gate."*

1. **Approver identity (355).** Normal approver = the **intent owner** (`Intent`
   is human-owned, CORE.md §Intent). In an async session with no owner present,
   the gate pauses at `input-required` and the `SpecLifecycle` stays in `/open`
   — it does **not** auto-approve. The provenance-stamped override is the *owner's*
   escape, never the agent's. **Folded into 355.**
2. **Zero-decision specs (356).** `spec_decisions_ready` returns `ready=true`
   *only* when ≥1 decision was extracted and all are approved; a spec from which
   extraction surfaced **no** decisions returns `ready=false, reason="no-decisions"`
   — a docs-only/trivial spec is moved with an explicit owner ack, never a vacuous
   pass. **Folded into 356.**
3. **Improve-gate exit criterion (358).** "Design good" is now decidable: panel
   findings folded **and** `brooks_lint` returns no `block` finding **and** owner
   confirm. Not a vibe. **Folded into 358.**

### B3 — Thematic-living ADR loses the audit trail the file reader expects (Newman)
> *"An ADR's classic value is that the *file* shows 'decided X, later superseded by
> Y'. If `render` shows only LIVE decisions, the human reading the file loses the
> history — it is in the graph, but the file now lies by omission about the past."*

- `adr.render` emits **current decisions + a collapsed 'Superseded / history'
  appendix** (id, title, superseded-by, date), so the file is honest about the
  past without re-inflating. The MIN line-budget (B-adjacent) applies to the
  **active** section only; the appendix is a one-line-per-decision index, and the
  full superseded body stays in the graph (`as_of`). Resolves the
  living-file-vs-MIN-001 conflict. **Folded into 360.**

### B5 — `Decision` vs `Reflection`: justify the new node (Fowler)
- A `Reflection` is an observation/lesson (scope-tagged memory); a `Decision` is a
  *chosen course with neglected alternatives + accepted trade-offs*, gate-able and
  status-bearing. Distinct enough to warrant a node — but the spec must say so, or
  a future audit collapses them. **One-line justification folded into 360.**

## Majors (folded / noted)

- **M1 — "super strict schemas" must be registered `Schema` nodes, not prose
  (Wiegers/Adzic).** The owner explicitly asked for strict schemas. Each verb's
  input/output (extraction candidate, hint block, `dod_check` result) is now
  specified as a `Schema` the artefact `CONFORMS_TO` (CORE.md generate/validate
  pair), enforced on `record`, not merely documented. **Folded into 360/356.**
- **M2 — stale `discover` reference (358).** `discover.interview` **shipped**
  (Spec 309); 358's failure-mode note calling it "still a scaffold" is outdated.
  **Fixed in 358.**
- **M3 — Brooks-lint home (359).** Primary home = an `intent` method (the 9th);
  `panel` only *surfaces* it. Noted in 359 (no change needed — already stated).
- **theme-creation rule (353).** When does a decision append vs spawn a new theme?
  Rule: a theme = an architecture **layer** (the reserved five); a new theme needs
  an owner decision, not an extraction default — extraction routes to an existing
  theme or flags `theme=unrouted` for the owner. **Folded into 353.**

## Consensus

1. The port-as-binding thesis is sound and the substrate mapping holds (all experts).
2. The two simplifications (B1) make the set *more* canon-faithful, not less — the
   spec set passing its own Brooks-lint is the strongest validation.
3. The hinge is the load-bearing novelty; its three failure paths (B2) had to be
   pinned before implementation, and now are.

## Disagreement (recorded, not resolved here)

- **Fowler vs the owner's framing on B1's `workflow` capability.** Fowler: fold the
  skill into `develop`. Owner: "the workflow capability thing." The spec now leads
  with the discipline-in-`develop` recommendation but preserves the new-cap option
  as an owner decision at implementation — this panel does not overrule the owner's
  stated framing, it surfaces the cheaper coherent alternative.
