---
spec_id: "312"
slug: research-grounded-intent
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 8]
depends_on: ["044", "307", "308", "313"]
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
   with the discovery profile, Spec 313's intent-discovery scouts join the set
   (this spec passes the profile through; 313 defines selection).
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

## Acceptance

Calling `discover.ground(intent_id)` runs the full research harness over the
draft Intent and returns `{citations, already_exists, prior_art, recommendation}`
— with every verified Citation carrying a `GROUNDS` edge to the Intent, the
`Research` node SERVING it, and zero re-implemented search. A reviewer can
replay the grounding (Spec 325) from the `GROUNDS`/`CITES`/`SERVES` edges alone.
Grounding leaves the Intent measurably narrower (evidence the clarify loop and
feasibility probe consume), and nothing outside `discover/` changed.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Research-agents core of the Spec 307 program; the first of
  the three research children (312 grounds, 313 scouts, 314 probes). Build
  AFTER 308 (scaffold) and 309/310 (AskUser core), since grounding feeds the
  clarify loop. Depends on 313 for the intent-discovery scout profile but
  degrades gracefully to research's default depth sets if 313 lands later
  (the `depth` mapping is the floor; the discovery profile is the enrichment).
- **Slice plan:** Slice 1 — typed dispatch + `GROUNDS` edges over research's
  default specialist sets (no scout profile yet); the verify gate and the
  derived summary land here. Slice 2 — pass the `purpose=intent-discovery` lead
  profile (Spec 313) through `depth`. Slice 3 — `recommendation` tuning from
  dogfooded grounding reflections (`analyze.graph`).
- **Open question (resolve at build):** the `already_exists` confidence floor —
  a documented tunable budget (CLAUDE.md #8), not a magic number; default to
  the research codebase-citation confidence (1.0) requiring a deliverable-token
  overlap, overridable per call.
