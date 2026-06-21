---
spec_id: "312"
slug: research-grounded-intent
status: draft
state: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 8]
depends_on: ["040", "044", "307", "308"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 312 — Research-grounded intent (`discover.ground`)

> Child of the intent-pillar deep program (Spec 307), the **research-agents**
> layer. It dispatches the existing `research` pipeline (Spec 044:
> `research.lead` → fan-out specialists → `research.verify`) over a draft Intent
> so the WHY is born grounded, not guessed — every verified `Citation` gets a
> `GROUNDS` edge to the Intent (Spec 307 ontology).
>
> **Folds in the former Spec 313 (trim 19→17, panel-driven 2026-06-18).** The
> intent-discovery research scouts — *the "Research agents" the owner asked for*
> — were their own spec; the spec-panel + business-panel both found 313↔312 too
> tightly coupled (a literal `depends_on` cycle) to stand apart. The scout set
> now lives here, as a §"intent-discovery scouts" section of the verb that
> dispatches them. No behaviour lost — the scouts are the same profiled
> compositions over `research/_specialist.py`.
>
> **★ EXTENDED by Spec 307 §Refinement (2026-06-18).** `ground` also absorbs
> `feasibility` (314) as `ground(decide=True)` — same scouts, plus a verdict — and
> two efficiency rules become mandatory: (1) **reuse** a verified grounding
> `Research` that already `SERVES` the Intent this session (never re-fan the same
> scouts — the largest waste the efficiency pass found); (2) specialist fan-out
> runs **concurrently** (inherit the `research` Spec 044 model).

## Why (evidence + doctrine)

Spec 307 §"The thesis" names two exploration engines; this is the **first**:
*"Research agents — to ground the intent in evidence: does this already exist in
the repo? has a prior reflection solved it? is it feasible? what's the prior
art? Grounding turns 'I want X' into 'I want X, and here is what reality says
about X.'"* Today an Intent is minted shallow (Spec 307 §"Why" — a one-sentence
`{purpose, deliverable, acceptance}` node) and work begins; the provenance moat
(Goal 2) then records *what was done* against a WHY that was never sharpened.

The doctrine win is twofold. **Goal 2 (provenance moat):** grounding evidence
becomes a first-class, replayable part of the Intent's birth — `GROUNDS` edges
make "here is what reality said about this intent at capture time" queryable
forever, surviving the session. **Goal 8 (harness-in-harness):** `ground` does
not re-implement search — it **dispatches the existing multi-agent research
harness** (lead-planner → bounded specialist scouts → adversarial verifier)
from inside the discovery harness, chaining tools in the sandbox and returning
only a summary. The substrate already has the research pipeline; the discovery
pillar composes it (CLAUDE.md "don't write code that bypasses the substrate";
the dormant-surface and derivability audits — reuse, never reinvent).

Grounding is also what makes the **clarify loop (Spec 311) sharp**: research
narrows the option space, so the next AskUser question is derived from evidence
(the Spec 307 §"interleaving" rule), never invented. Ground BEFORE clarify.

## Design

### Verb (cluster `agency/capabilities/discover/clusters/ground.py`)

```python
@verb(role="effect")
def ground(self, intent_id: str = "", depth: str = "standard") -> dict:
    """Ground a draft Intent in research evidence (Spec 312).

    Dispatches the research pipeline (research.lead → specialists →
    research.verify) using the Intent's purpose/deliverable as the
    question; links each verified Citation GROUNDS the Intent.

    Inputs: intent_id (str — defaults to ctx.intent_id, the Spec 091
            ambient pattern), depth (str — brief|standard|deep).
    Returns: ``{citations, already_exists, prior_art, recommendation}``.
    chain_next: discover.clarify (311) — sharp questions over narrowed
                options; or discover.feasibility (314) for a go/no-go.
    """
```

`role="effect"` per the Spec 307 verb table — `ground` mutates (it writes
`GROUNDS` edges and dispatches a pipeline that records `Research`/`Citation`
nodes), placing it with `interview`/`clarify`/`scope` on the write side of the
Spec 307 §"Cross-spec coherence" rule 3.

### Composition — how it dispatches the `research` pipeline

`ground` builds the **research question from the Intent**, then drives the Spec
044 surface through `ctx.registry.invoke` (the same in-registry dispatch the
research specialists already use — `_specialist.run_prior_reflections` calls
`ctx.registry.invoke(..., "reflect", "recall_semantic", ...)`):

1. **Recall** the Intent via the `_base.DiscoverCluster._recall_intent(intent_id)`
   helper (Spec 308). Compose the research question from `purpose` +
   `deliverable` (e.g. `"{purpose} — deliverable: {deliverable}"`). Empty intent
   → `{error: "UNKNOWN_INTENT", intent_id}` (no pipeline dispatched).
2. **Lead** — `invoke("research", "lead", question=…, depth=depth)`. `depth`
   maps straight through to research's specialist sets (Spec 044 `_lead.plan` /
   `_DEPTH_SPECIALISTS`): `brief` → `[codebase]`; `standard` →
   `[codebase, prior-reflections]`; `deep` →
   `[codebase, prior-reflections, doc-corpus, web]`. When the lead is invoked
   with `purpose="intent-discovery"`, the intent-discovery scouts (§"The
   intent-discovery scouts" below) join/replace the set.
3. **Fan out** — for each planned role, `invoke("research", "specialist",
   research_id=rid, role=role, query=…)`. Each runs ONE bounded sub-search and
   records `Citation` nodes (`CITES` from the `Research` node), per Spec 044's
   confidence rules (codebase → 1.0; reflection/doc-corpus → ranker score;
   web → 0.9). `ground` does NOT touch citation internals — it reuses them.
4. **Verify** — `invoke("research", "verify", research_id=rid)`. The adversarial
   verifier (`evidence-supports-claim`, `contradiction-cluster`,
   `web-reachability`) gates which citations are trustworthy. Only citations on
   a `Research` whose `Verification.status != "fail"` are grounded onto the
   Intent — unverified evidence does not earn a `GROUNDS` edge.

### The intent-discovery scouts (folded from Spec 313)

Research's v1 specialist roles (`codebase`, `prior-reflections`, `doc-corpus`,
`web`) answer *generic* questions. An Intent needs **sharper** ones — *can the
repo support this? has it already been built/specced? what hard constraints
bound it? who does it affect?* So `ground` selects an **intent-discovery scout
set** when it leads the research (the Spec 307 §"thesis" axes). Each scout is a
new role-handler in `research/_specialist.py` — a **profiled composition** over
the *existing* walkers (aim, not a parallel engine), recording `Citation` nodes
with the unchanged Spec 044 confidence rules so `research.verify` checks them as-is:

| Scout role | Question | Reuses | source_kind |
|---|---|---|---|
| `feasibility-scout` | Can the repo/stack support this? | deps (`pyproject`/extras) + `run_codebase` over `agency/` | `codebase` |
| `prior-art-scout` | Built / specced / reflected-on already? | `Plan/` + `run_prior_reflections` + `run_codebase` | `codebase`+`reflection` |
| `constraint-scout` | What hard constraints bound this? | `CLAUDE.md` + `docs/` (`run_doc_corpus`) | `doc-corpus` |
| `stakeholder-scout` | Who/what does this affect? | the Intent's `SERVES` subtree via `ctx.neighbors` | `codebase` (graph-anchored) |

Selection rides a **profile arg** on the lead planner — `research/_lead.py::plan(question, depth, purpose="")`; `purpose=="intent-discovery"` returns the scout
set (`brief`→`[prior-art-scout]`; `standard`→`+feasibility-scout`; `deep`→
`+constraint-scout, stakeholder-scout`), mirroring research's depth contract.
`ground` passes `purpose="intent-discovery"` through its `research.lead` call; a
plain research question keeps the v1 sets untouched. Adding the roles touches the
`research.specialist` role enum (`# AGENCY-DRIFT: research specialist roles`) and
the naming-audit substrate set — run `scripts/check-drift` before commit
(CLAUDE.md rule 6). A scout heavy enough to cross the Spec 040 eleven-signal
threshold (e.g. `stakeholder-scout` over a large `SERVES` subtree — S2/S3/S7
amplify, the S6 mutation disqualifier never fires) walks `dispatch-decision`
before fan-out; the decision is *computed* per scout, never hardcoded. This is a
Goal-4 win: the scout set extends an existing open set (research's roles) with no
new verb and no new capability — `ground` (here, `discover/`) and the scouts
(`research/`, a documented composition seam) are the only files touched.

### Ontology read/write (Spec 307 + Spec 044, BY NAME)

- **Reads (Spec 044):** the `Research` node + its `CITES` → `Citation` neighbours
  (`ctx.neighbors(research_id, "CITES", direction="out")`) and the `Verification`
  verdict. **`Citation` is reused, never redefined** (Spec 307 §ontology note;
  Spec 308 "No `Citation` redefinition" — `"Citation" not in discover_ontology`).
- **Writes (Spec 307):** for each verified `Citation`, a `GROUNDS` edge
  `Citation → Intent` (Spec 307 edge table: *"research evidence grounding the
  Intent — reuses research's Citation"*). The `Research` node itself `SERVES` the
  Intent through research's own `record_and_serve` (Spec 044), so the grounding
  trail is double-anchored.

### The grounding summary (return shape)

`ground` interprets the verified citations into a decision-ready summary —
**derived from the evidence, never invented** (derivability audit):

| Field | Derivation |
|---|---|
| `citations` | count of `GROUNDS`-linked (verified) Citations on the Intent |
| `already_exists` | True iff a `codebase`-kind Citation matches the deliverable above a confidence floor (the repo already ships it) |
| `prior_art` | list of `reflection`/`doc-corpus` Citations — a prior reflection or doc that bears on this intent |
| `recommendation` | derived string: `already_exists` → *"narrow or supersede — this exists at <path>"*; rich prior_art → *"reuse the prior solution; clarify the delta"*; thin evidence → *"proceed; little prior art — clarify scope"* |

Grounding **narrows the option space**: `already_exists`/`prior_art` are exactly
the evidence Spec 311's clarify loop turns into sharp, derived AskUser options,
and Spec 314's feasibility probe weighs into a go/no-go verdict.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

1. **Dispatches, doesn't reinvent (Goal 8):** after `ground`, exactly one
   `Research` node exists per call SERVING the intent, and its `Citation`
   children equal those produced by the equivalent direct `research.lead` →
   `specialist` → `verify` sequence — assert the grounded citation **set** is a
   subset of the live `Research`'s `CITES` set, computed from the graph, never a
   pinned count.
2. **Every verified citation grounds (Goal 2):** the number of `GROUNDS` edges
   into the Intent equals the number of this `Research`'s Citations whose
   verification did not fail — `len(grounds_edges) == len(verified_citations)`,
   both read live.
3. **No `Citation` redefinition:** `"Citation" not in discover_ontology.nodes`
   (reuse the research node; the `GROUNDS` edge is the only new ontology touch).
4. **Depth maps to research's specialist sets:** the specialist roles fanned out
   under `depth` equal `research._lead.plan(question, depth)[0]` for the same
   depth — assert equality against the live planner, not a frozen list, so a
   change to research's depth table flows through.
5. **Unverified evidence is not grounded:** seed a `Research` with one citation
   the verifier fails; assert that citation gets NO `GROUNDS` edge while a
   passing sibling does (the verify gate is load-bearing).
6. **`already_exists` is derived, not asserted:** with a codebase citation
   matching the deliverable, `already_exists is True`; remove it and it flips
   False — the flag tracks live evidence, never a constant.
7. **Scout set extends the open role set (Goal 4, folded from 313):** after this
   spec the live `research.specialist` role set is a **superset** of the v1 four
   — assert `v1_roles <= live_roles` and the four scouts ∈ `live_roles`, computed
   from the dispatch handler, never a pinned count.
8. **Profile selects scouts, plain stays generic:** `plan(q, depth,
   purpose="intent-discovery")` returns the scout set for that depth while
   `plan(q, depth)` returns the unchanged v1 set — assert the two differ exactly
   by the scout/generic swap, both read from the live planner.
9. **Stakeholder-scout reads the SERVES tree:** for an Intent with a known
   `SERVES` subtree, the stakeholder-scout's citation count tracks the live
   subtree size (grows when a child is added) — derived from the graph, never
   frozen.

## Acceptance

Calling `discover.ground(intent_id)` runs the full research harness over the
draft Intent and returns `{citations, already_exists, prior_art, recommendation}`
— with every verified Citation carrying a `GROUNDS` edge to the Intent, the
`Research` node SERVING it, and zero re-implemented search. A reviewer can
replay the grounding (Spec 325) from the `GROUNDS`/`CITES`/`SERVES` edges alone.
Grounding leaves the Intent measurably narrower (evidence the clarify loop and
feasibility probe consume), and nothing outside `discover/` changed.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Research-agents core of the Spec 307 program (now BOTH
  research children — grounding + the scouts folded from 313; 314 probes builds
  on it). Build AFTER 308 (scaffold) and 309/310 (AskUser core), since grounding
  feeds the clarify loop.
- **Slice plan:** Slice 1 — typed dispatch + `GROUNDS` edges over research's
  default specialist sets (no scout profile yet); the verify gate and the
  derived summary land here. Slice 2 — the `purpose=intent-discovery` lead
  profile + the two `standard` scouts (`prior-art-scout` + `feasibility-scout`,
  the highest-value "exists already?"/"feasible?" pair). Slice 3 — the `deep`
  scouts (`constraint-scout` + `stakeholder-scout`) + the Spec 040 dispatch hook
  for heavy scouts (default inline) + `recommendation` tuning from dogfooded
  grounding reflections (`analyze.graph`).
- **Open question (scouts):** whether the discovery profile *replaces* or
  *augments* the depth set. Default: replace (scouts are tuned supersets, so
  running both double-counts); revisit if dogfooding shows the generic walker
  catches hits the scouts miss.
- **Open question (resolve at build):** the `already_exists` confidence floor —
  a documented tunable budget (CLAUDE.md #8), not a magic number; default to
  the research codebase-citation confidence (1.0) requiring a deliverable-token
  overlap, overridable per call.
