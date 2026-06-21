---
spec_id: "314"
slug: feasibility-prior-art-probe
status: draft
state: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["307", "308", "312", "320"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 314 — Feasibility + prior-art go/no-go probe (`discover.feasibility`)

> Child of the intent-pillar deep program (Spec 307), the **research-agents**
> layer. It is the research-backed **GO / NO-GO / REFINE** probe run BEFORE an
> Intent is confirmed — it weighs the feasibility-scout + prior-art-scout
> Citations (Spec 312) and records a `FeasibilitySignal` node (Spec 307
> ontology) carrying the verdict.
>
> **★ FOLDED by Spec 307 §Refinement (2026-06-18).** `feasibility` collapses into
> `ground(decide=True)` — it is grounding + a verdict over the *same* scouts, so a
> separate verb re-fans the pipeline (the efficiency pass's largest waste). The
> `FeasibilitySignal` node is dropped (a verdict-tagged finding on the existing
> Citations). This spec stays as the verdict-derivation mechanism record.

## Why (evidence + doctrine)

Spec 307 §"Why" names the missing pieces of a discovered intent — *"no
research-backed grounding, no … feasibility probe — before the intent is
confirmed."* Spec 312 grounds the Intent in evidence; Spec 312 supplies the
intent-discovery scouts. But grounding produces *citations*, not a *decision*.
Before the orchestrator spends effort against an Intent, it needs a sharp
verdict: **is this worth doing as stated?** A prior-art-scout that finds an
already-shipped solution should stop the work; a feasibility-scout that finds a
blocking missing dependency should send it back to refinement — both *before*
the clarity gate (Spec 322) clears the Intent for `confirm`.

The doctrine win (**Goal 2, provenance moat**): the verdict is not a transient
chat judgement — it is a `FeasibilitySignal` node linked to the Intent, with its
`rationale` and the Citations that drove it. "We decided this was a no-go because
the repo already ships it at `<path>`" becomes a permanent, replayable graph fact
(Spec 325). The moat records not just *what was built* but *what was decided not
to build, and why* — the highest-leverage provenance, because it is the decision
the next agent would otherwise re-litigate. This is the
"provenance-or-it-didn't-happen" rule (Spec 307 §coherence rule 6) applied to a
*negative* decision.

## Design

### Verb (cluster `agency/capabilities/discover/clusters/ground.py`)

```python
@verb(role="act")
def feasibility(self, intent_id: str = "") -> dict:
    """Research-backed GO / NO-GO / REFINE probe on a draft Intent (Spec 314).

    Runs the feasibility-scout + prior-art-scout (Spec 312) over the
    Intent, weighs the Citations, records a FeasibilitySignal, and
    recommends the next move.

    Inputs: intent_id (str — defaults to ctx.intent_id).
    Returns: ``{verdict, rationale, citations, recommendation,
                signal_id}``.
    chain_next: no-go → discover.refine (320) or abandon; refine →
                discover.clarify (311); go → discover.clarity (322).
    """
```

`role="act"` per the Spec 307 verb table (a writing verb — it records a
`FeasibilitySignal`, on the write side of §coherence rule 3). It lands in the
same `clusters/ground.py` module as `discover.ground` (Spec 307 §architecture:
*"ground.py — Spec 312/314 — research dispatch + grounding + feasibility"*).

### How it composes the research pipeline (via Spec 312)

`feasibility` runs a **focused** dispatch — only the two decision-relevant
scouts, not the full grounding fan-out:

1. Recall the Intent (`_base.DiscoverCluster._recall_intent`, Spec 308); empty →
   `{error: "UNKNOWN_INTENT", intent_id}`.
2. `invoke("research", "lead", question=…, depth="standard",
   purpose="intent-discovery")` — Spec 312's `standard` discovery profile is
   exactly `[prior-art-scout, feasibility-scout]`, the two scouts this probe
   needs. (If `discover.ground` already ran for this Intent, `feasibility` MAY
   reuse the existing `Research`'s verified Citations rather than re-fan — the
   grounding evidence is the same evidence; no second source of truth, Spec 307
   §coherence rule 4.)
3. Fan out + `invoke("research", "verify", …)` so only verified Citations weigh
   into the verdict (an unverified "it already exists" must not trigger a no-go).

### The verdict-derivation rule (`feasibility_verdict` enum, Spec 307)

The verdict ∈ `{go, no-go, refine}` (Spec 307 §enums `feasibility_verdict`) is
**derived from the verified Citations** — never asserted by the verb:

| Evidence (verified Citations) | Verdict | Rationale shape |
|---|---|---|
| prior-art-scout found an **existing shipped solution** matching the deliverable (codebase Citation, high confidence) | `no-go` | *"already exists at `<path>` — narrow, supersede, or abandon"* |
| prior-art-scout found a **near-miss** (prior spec/reflection on the same area, not a complete solution) | `refine` | *"prior art at `<id>` — clarify the delta before building"* |
| feasibility-scout found a **blocking missing dependency / unsupported stack** | `refine` | *"missing `<dep>` — refine to add it or pick a supported path"* |
| neither scout found a blocker and the evidence is thin | `go` | *"no blocking prior art or dependency gap — clear to proceed"* |

The rule is a **monotone weighing** of evidence: a no-go signal (existing
solution) dominates a refine signal, which dominates a go. The `rationale`
quotes the driving Citation's `source_url_or_path` — derived, not invented
(derivability audit).

### Ontology write (Spec 307, BY NAME)

Records a `FeasibilitySignal` node `{verdict, rationale}` (Spec 307 §nodes,
*"recorded by: feasibility"*) linked to the Intent. The edge follows the Spec 307
pattern — the signal is anchored to the Intent it judges (the natural read is
`ctx.neighbors(intent_id, …)` to surface "what did the feasibility probe say
about this intent"); the `FeasibilitySignal → Intent` linkage carries the
`feasibility_verdict` enum. No new edge type beyond the Spec 307 surface; the
driving Citations keep their `GROUNDS` edges from Spec 312 when grounding was
reused.

### The recommendation (routes the next move)

`recommendation` maps the verdict to the next discovery verb — so `feasibility`
is a router, not a dead end:

- `no-go` → recommend **`discover.refine` (Spec 320)** to supersede the Intent
  with the found-solution finding, or abandon.
- `refine` → recommend **`discover.clarify` (Spec 311)** to ask the sharp
  question the blocker raises (e.g. "add the missing dep, or pick path B?").
- `go` → clear to proceed to **`discover.clarity` (Spec 322)** — the gate the
  `confirm` verb reads.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

1. **Verdict is derived from live Citations (Goal 2):** seed a `Research` whose
   prior-art-scout has a high-confidence codebase Citation matching the
   deliverable → `verdict == "no-go"`; remove that Citation → the verdict flips
   off `no-go` — assert the verdict is a function of the live evidence, never a
   constant.
2. **`FeasibilitySignal` is recorded with the verdict:** after `feasibility`,
   exactly one `FeasibilitySignal` node links the Intent and its `verdict`
   equals the returned verdict — read from the graph, the moat invariant
   (Spec 307 §coherence rule 6).
3. **Verdict ∈ the Spec 307 enum:** the returned `verdict` is a member of the
   live `feasibility_verdict` enum parsed from `discover`'s ontology — assert
   membership against the registered enum, not a hardcoded `{go, no-go, refine}`.
4. **Only verified Citations weigh in:** an unverified "already exists" Citation
   (verifier `fail`) does NOT produce a `no-go` — assert the verdict ignores
   failed Citations (the verify gate is load-bearing, mirroring Spec 312 test 5).
5. **No second source of truth (Spec 307 rule 4):** when `discover.ground` has
   already grounded the Intent, `feasibility` reuses that `Research`'s verified
   Citations — assert no duplicate `Research` node is minted for the same Intent
   within the probe (it composes, never re-fans needlessly).
6. **Recommendation routes by verdict:** `no-go`→`refine`(320), `refine`→
   `clarify`(311), `go`→`clarity`(322) — assert the recommendation is the
   verdict→verb mapping evaluated on the live verdict, not a fixed string.

## Acceptance

`discover.feasibility(intent_id)` runs the feasibility + prior-art scouts over a
draft Intent, weighs only the verified Citations, returns
`{verdict, rationale, citations, recommendation, signal_id}`, and records a
`FeasibilitySignal` linked to the Intent. A prior-art hit on a shipped solution
yields `no-go`; a missing dependency yields `refine`; a clear field yields `go`
— each routing to the right next discovery verb. The decision survives as a
replayable graph fact (Spec 325): a reviewer can answer "why was this intent not
built?" from the `FeasibilitySignal` + its driving Citations alone. Nothing
outside `discover/` (and the Spec 312 research composition) changed.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** The decision layer over Spec 312 (grounding + the
  intent-discovery scouts, folded in) — the probe that turns evidence into a
  go/no-go/refine verdict before the clarity gate. Build AFTER 312 and alongside
  320 (its no-go target); the `standard` discovery profile (`[prior-art-scout,
  feasibility-scout]`) is the exact set it needs, so it ships once 312's two
  `standard` scouts land.
- **Slice plan:** Slice 1 — verdict derivation + `FeasibilitySignal` recording
  over a freshly-fanned `Research` (the monotone weighing rule). Slice 2 — reuse
  an existing grounding `Research` when present (no second source of truth).
  Slice 3 — `recommendation` routing wired to the live 320/311/322 verbs once
  those land.
- **Open question (resolve at build):** the no-go confidence floor — a documented
  tunable budget (CLAUDE.md #8), not a magic number; default to a high-confidence
  codebase Citation (≥ research's 1.0 deterministic floor) requiring a
  deliverable-token overlap, overridable per call. Pair it with Spec 312's
  `already_exists` floor so the two probes agree on "exists".
