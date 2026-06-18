---
spec_id: "313"
slug: intent-discovery-research-specialists
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [4, 8]
depends_on: ["040", "044", "307", "312"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 313 — Intent-discovery research specialists (scouts)

> Child of the intent-pillar deep program (Spec 307), the **research-agents**
> layer. It adds NO new top-level verb — it **extends `research`'s specialist
> set** (`research/_specialist.py`, Spec 044) with intent-discovery-tuned scouts,
> selected when `research.lead` is invoked for a discovery question. **These are
> the "Research agents" the owner asked for** (Spec 307 §"The thesis", engine 1).

## Why (evidence + doctrine)

Spec 312 dispatches the research pipeline to ground an Intent, but research's
v1 specialist roles (`codebase`, `prior-reflections`, `doc-corpus`, `web` —
Spec 044 `_specialist.py`) answer *generic* questions: "where does this string
appear", "what reflections are semantically near". An Intent needs **sharper
questions**: *can the repo support this? has it already been built/specced? what
hard constraints bound it? who does it affect?* Those are the four axes Spec 307
§"The thesis" names (*"does this already exist… is it feasible… what's the prior
art"*) plus the SERVES-tree stakeholder axis the provenance moat makes uniquely
answerable.

The doctrine win. **Goal 4 (open-set capabilities):** the scout set extends an
existing open set — research's specialist roles — **without a new verb or a new
capability**; adding a scout is adding a role-handler + a registry row, the same
"drop-in" bar applied one level down (CLAUDE.md "drop-in bar"; Spec 307 §"One
capability, one folder" — 313 touches `research/`, a documented composition
seam, not `discover/`). **Goal 8 (harness-in-harness):** each scout is a
**bounded sub-search** returning Citations with the *existing* confidence rules
(Spec 044 §confidence) — no new evidence model, no new verifier. The research
harness already adversarially checks them (`research.verify`); the scouts just
aim the harness at intent-discovery questions.

This honours the **derivability + dormant-surface audits** (CLAUDE.md): scouts
reuse the codebase/reflection/doc walkers already in `_specialist.py` (a
scout is a *profiled composition* of existing walkers + a tuned query), so they
add aim, not a parallel search engine.

## Design

### The four scouts (new roles in `research/_specialist.py`)

Each is a `run_<scout>(memory, ctx, research_id, query, …) -> {citations, summary}`
matching the existing `run_codebase` / `run_prior_reflections` signature, and
each records `Citation` nodes with `CITES` edges and Spec 044 confidence rules.
They are **profiled compositions** over the existing walkers, not new engines:

| Scout role | Question it answers | Scans (reuses) | Citation source_kind |
|---|---|---|---|
| `feasibility-scout` | Can the repo/stack support this? | deps (`pyproject.toml`/`extras`) + architecture (`run_codebase` over `agency/`) | `codebase` |
| `prior-art-scout` | Has this been built / specced / reflected-on already? | `Plan/` specs + `run_prior_reflections` (reflections) + `run_codebase` (shipped code) | `codebase` + `reflection` |
| `constraint-scout` | What hard constraints bound this? | `CLAUDE.md` + `docs/` (`run_doc_corpus`) + config | `doc-corpus` |
| `stakeholder-scout` | Who / what does this affect? | the Intent's `SERVES` subtree + owners (graph walk via `ctx.neighbors`) | `codebase` (graph-anchored) |

Confidence follows the source it reuses (Spec 044 §confidence): codebase
matches → 1.0; reflection/doc matches → the ranker/cosine score. **No new
confidence model** — the scouts inherit the rule so `research.verify` checks
them unchanged.

### Wiring the roles (the `research.specialist` dispatch)

`research/_main.py::ResearchCapability.specialist` already routes `role` to a
handler (`if role == "codebase": …`). This spec adds four arms
(`feasibility-scout`, `prior-art-scout`, `constraint-scout`, `stakeholder-scout`)
delegating to the new `run_*` functions. The role enum that error-gates an
unknown role extends from the v1 four to the discovery scouts —
`# AGENCY-DRIFT: research specialist roles` tags the set so the drift audit
(CLAUDE.md rule 6) sees it.

### The lead-planner discovery profile (how the set is selected)

`research/_lead.py::plan(question, depth)` today picks specialists purely from
`depth`. This spec adds a **profile arg** — `plan(question, depth,
purpose="")` — and when `purpose == "intent-discovery"` the planner returns the
**scout set** instead of (or alongside) the generic depth set:

```python
_DISCOVERY_SCOUTS = {
    "brief":    ["prior-art-scout"],
    "standard": ["prior-art-scout", "feasibility-scout"],
    "deep":     ["prior-art-scout", "feasibility-scout",
                 "constraint-scout", "stakeholder-scout"],
}
```

`discover.ground` (Spec 312) passes `purpose="intent-discovery"` through its
`research.lead` call; a plain research question (no profile) keeps the v1 sets
untouched. The depth→scout mapping mirrors research's depth→specialist contract
so `ground`'s `depth` arg means the same thing for both surfaces.

### Spec 040 dispatch-decision composition (heavy scouts)

A scout that crosses the Spec 040 eleven-signal threshold — e.g.
`stakeholder-scout` walking a large `SERVES` subtree (S2 ≥ 4 unfamiliar files,
S3 repeated exploration, S7 read-only amplifies) — is a candidate for **subagent
isolation**, not an inline scan. Before fanning a heavy scout, the planner walks
the `dispatch-decision` skill (Spec 040 / `delegate.ontology.skills`): read-only
scouts amplify toward dispatch (S7), the mutation disqualifier (S6) never fires
(scouts only record Citations through the verified pipeline). Light scouts
(`prior-art-scout` over a known `Plan/` tree) stay inline. This keeps the
research fan-out token-economical (Goal 1 follows, though Goal 8 is the named
win) — the decision is *computed* per scout, never hardcoded to "always
dispatch".

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

1. **The scout set extends the open role set (Goal 4):** the live
   `research.specialist` role set after this spec is a **superset** of the v1
   four — assert `v1_roles <= live_roles` and the four scouts ∈ `live_roles`,
   computed from the dispatch handler, never a pinned count.
2. **Profile selects scouts, plain stays generic (Goal 8):** `plan(q, depth,
   purpose="intent-discovery")` returns the scout set for that depth, while
   `plan(q, depth)` returns the unchanged v1 set — assert the two differ exactly
   by the scout/generic swap, both read from the live planner.
3. **Scouts cite with the existing confidence rules:** every Citation a scout
   records carries a `confidence ∈ [0, 1]` matching its `source_kind`'s Spec 044
   rule (codebase == 1.0; reflection/doc == its score) — assert the relationship,
   not a literal score.
4. **The verifier checks scouts unchanged:** a `Research` fanned out with scouts
   passes through `research.verify` and produces a `Verification` node — assert
   the scout citations are in the verifier's `n_checked`, so no scout bypasses
   the adversarial gate.
5. **Stakeholder-scout reads the SERVES tree:** for an Intent with a known
   `SERVES` subtree, the stakeholder-scout's citation count tracks the live
   subtree size (grows when a child is added) — derived from the graph, never
   frozen.
6. **Dispatch-decision is consulted for heavy scouts:** a scout flagged heavy
   records a dispatch-decision walk (the Spec 040 signals are evaluated) rather
   than always-inline — assert the decision is a function of the live signal bag,
   not a constant `True`/`False`.

## Acceptance

Invoking `research.lead(question, depth, purpose="intent-discovery")` plans the
intent-discovery scout set; fanning out runs `feasibility-scout`,
`prior-art-scout`, `constraint-scout`, `stakeholder-scout` as bounded
sub-searches that record verifiable Citations with the existing confidence
rules; `research.verify` checks them unchanged. `discover.ground` (Spec 312)
consumes the set transparently. The only files touched are under `research/`
(a documented composition seam) — no new top-level verb, no new capability, the
open role set simply grew (Goal 4).

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** The "Research agents" the owner directive named, realised as
  an extension of research's open specialist set rather than a parallel engine.
  Build alongside / just after Spec 312 (which dispatches them); 314 weighs their
  Citations into a go/no-go probe.
- **Slice plan:** Slice 1 — `prior-art-scout` + `feasibility-scout` (the two
  `standard`-depth scouts, the highest-value pair for "exists already?" +
  "feasible?") + the `purpose` arg on `plan`. Slice 2 — `constraint-scout` +
  `stakeholder-scout` (the `deep` set). Slice 3 — the Spec 040 dispatch hook for
  heavy scouts (default inline; dispatch only when the signals fire).
- **Open question (resolve at build):** whether the discovery profile *replaces*
  or *augments* the depth set. Default: replace (scouts are tuned supersets of
  the generic walkers, so running both double-counts); revisit if dogfooding
  shows the generic `codebase` walker catches hits the scouts miss.
- **Drift note:** adding the four roles touches the `research.specialist` role
  enum (`# AGENCY-DRIFT: research specialist roles`) and the naming-audit
  substrate set — run `scripts/check-drift` before commit (CLAUDE.md rule 6;
  "full suite on a migration").
