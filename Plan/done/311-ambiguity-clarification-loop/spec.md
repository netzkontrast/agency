---
spec_id: "311"
slug: ambiguity-clarification-loop
status: draft
state: done
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2]
depends_on: ["147", "307", "308", "310", "312"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 311 — Ambiguity detection + clarification loop (`discover.clarify`)

> Child of the intent-pillar deep program (Spec 307), the **guided-exploration**
> layer. This is the ambiguity-resolution loop the flow runs after grounding
> (`… ──► ground ──► clarify ──► frame`): it finds what is still vague in the
> draft Intent and asks the user targeted questions until it is sharp.
>
> **★ CONSOLIDATED by Spec 307 §Refinement (2026-06-18).** `clarify` merges with
> `interview` (309) + `scope` (318) into one **`elicit(mode=clarify)`** AskUser loop
> — the ambiguity-signal candidate source is the `mode`'s only distinction.
> Retained as the ambiguity-detection mechanism record.

## Why

**The gap (Spec 307 §"Why").** The interview (309) produces a *draft* Intent, and
`ground` (312) backs it in evidence — but a draft can still be **underspecified,
internally conflicting, vague in scope, missing acceptance, or resting on an
unstated assumption**. Nothing today detects that and resolves it. Spec 307
§thesis names this the second engine: when the captured intent is ambiguous, the
engine asks a *well-formed* question and folds the answer back. This child
**builds that loop** and is the named exerciser of the **AskUser tool-call chain**
+ **Driver seam** for ambiguity (Spec 307 coverage matrix).

**Why research must come first (the sharpness argument).** Spec 307 §thesis: the
two engines *interleave* — research narrows the option space so AskUser asks
*sharp* questions, with options **derived from evidence, never invented**. That
is why this spec `depends_on` 312 (`discover.ground`): grounding NARROWS the
option space before `clarify` runs, so each clarification question's options
come from real evidence (what the repo/prior reflections actually say) rather
than the verb's imagination. A clarification asked *before* grounding is a guess;
asked *after* it is a choice between grounded alternatives. This is the
derivability audit (CLAUDE.md, Spec 307 rule 2) applied at the loop level.

**Doctrine (Goal 2).** Every ambiguity resolved is recorded — a
`ClarificationQuestion` with a `CLARIFIES` edge to the Intent, and the Intent
itself superseded (bi-temporal) so *both* the vague and the sharpened versions
survive. The moat captures not just the final Intent but the **trail of how each
ambiguity was retired** (replayable, Spec 325).

## Design

**Cluster module:** `agency/capabilities/discover/clusters/clarify.py`
(`ClarifyCluster` mixin; shared helpers from `clusters/_base.py`).

**Verb:** `discover.clarify(intent_id: str = "")` — `role="act"` (writes; per
Spec 307 rule 3 `clarify` is a writer). `intent_id` defaults to `ctx.intent_id`
(the Spec 091 ambient pattern, via `_recall_intent`).

```python
class ClarifyOutcome(TypedDict):
    intent_id: str             # the (now superseded) Intent's stable id
    rounds: list[ClarifyRound] # one per ambiguity resolved
    residual_ambiguity: float  # final score; below threshold => loop exited clean
    exited_by: str             # "below_threshold" | "max_rounds"

class ClarifyRound(TypedDict):
    ambiguity_kind: str        # turn enum (Spec 307: underspecified·conflicting·…)
    score: float               # the heuristic score that flagged it
    question_id: str           # the ClarificationQuestion node (from discover.ask)
    answer: str                # the user's verbatim pick
    amended_to: str            # the new Intent revision id (intent.amend)
```

**The loop.**

1. **Score the draft Intent.** Read the Intent (`_recall_intent`) and score it
   against `data/ambiguity-signals.json` — the heuristic registry (CLAUDE.md #8:
   a definable registry, not frozen code), one entry per **`ambiguity_kind`**
   (Spec 307 enum): `underspecified · conflicting · vague-scope ·
   missing-acceptance · unstated-assumption`. Each signal yields a score and a
   pointer to the offending field.
2. **For each unresolved ambiguity above threshold:** generate a **targeted**
   question. The next-question generation runs through the **Driver seam**
   (Spec 147 structured-output) **behind a typed shape** (`ClarifySpec`
   TypedDict); the Driver, given the ambiguity kind + the grounding evidence
   (from 312, read via the Intent's `GROUNDS` citations), returns the question
   context. **Deterministic heuristic fallback** when no Driver: the
   `ambiguity-signals.json` entry carries a template question per kind, filled
   from the offending field. Either way the actual payload is built by
   **`discover.ask`** (Spec 310) — `clarify` never hand-rolls a question; it
   composes the primitive, passing the detected `ambiguity_kind`.
3. **Fold the answer in.** The user's verbatim answer is folded into the Intent
   via the substrate **`intent.amend`** (supersede — bi-temporal; the prior
   revision is retained, not overwritten). This is the `REFINES`/`SUPERSEDES`
   pairing Spec 307's ontology describes (the supersession spine is the
   substrate's; `clarify` triggers it).
4. **Record the edge.** Record the `ClarificationQuestion` (via `ask`) and write
   the **`CLARIFIES`** edge `ClarificationQuestion → Intent` (Spec 307 ontology —
   declared edges get traversed: `state`/`replay` read clarifications via
   `ctx.neighbors(intent_id, "CLARIFIES")`).
5. **Loop** until residual ambiguity is **below threshold** OR a **max-rounds
   budget** is hit (a named, tunable budget — CLAUDE.md #8 — not a magic number).

**Composition.** `clarify` READS the Intent's `GROUNDS` citations (from 312) to
make options sharp, COMPOSES `discover.ask` (310) for every question and
`intent.amend` (substrate) for every fold-back, and WRITES `ClarificationQuestion`
nodes + `CLARIFIES` edges + Intent supersessions. It reimplements no query that
exists (Spec 307 rule 4).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Monotonic resolution (the loop converges):** residual ambiguity is
  **non-increasing** across rounds, and each answered question strictly lowers it
  for its kind — assert `score[round n+1] <= score[round n]` over the live run,
  never a pinned final value (Spec 307 rule 5: clarity monotonic in answered
  questions).
- **One CLARIFIES edge per resolved ambiguity:** the count of `CLARIFIES` edges
  to the Intent **equals** `len(outcome["rounds"])` — computed from the live
  graph census, not a constant.
- **Bi-temporal keep-both:** after a fold-back, **both** the pre-amend and
  post-amend Intent revisions are recallable (the old one is not deleted) and the
  latest `recorded_at` wins on read — asserted against the substrate's revision
  history, proving supersession not overwrite.
- **Sharpness depends on grounding:** a clarify run on a *grounded* Intent
  produces options traceable to its `GROUNDS` citations, whereas an ungrounded
  Intent falls back to template options — assert the grounded run's option
  descriptions overlap the citation evidence (the derive-from-evidence contract,
  shared with 310).
- **Termination both ways:** an Intent that clears threshold exits with
  `exited_by == "below_threshold"` and `len(rounds) < max_rounds`; a stubbornly
  vague one exits `exited_by == "max_rounds"` with exactly `max_rounds` rounds —
  both computed.
- **Driver seam optional:** the loop runs to a clean exit with `driver=None`
  (heuristic templates) and with a stub Driver returning a typed `ClarifySpec`;
  both record the same node/edge surface.

## Acceptance

An agent points `discover.clarify` at a draft, grounded Intent and the loop
**finds what is still vague**, asks the user one targeted, evidence-grounded
question per ambiguity (via `discover.ask`), folds each answer back into the
Intent bi-temporally (via `intent.amend`), and records a `CLARIFIES` trail — until
the Intent's ambiguity drops below threshold. The WHY is no longer a guess with
gaps; it is a sharpened, evidence-narrowed statement whose every clarification is
replayable.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Guided-exploration ambiguity loop of the Spec 307 program;
  **Slice-1-typed-shape-first** — land `ClarifyOutcome` / `ClarifyRound` /
  `ClarifySpec` as the typed contract with the **deterministic `ambiguity-signals.json`
  heuristic + template-question fallback** wired and fully tested (monotonic
  convergence, CLARIFIES-per-round invariant, bi-temporal keep-both), and the
  **AskUser render + LLM next-question Driver seam (Spec 147) behind the typed
  shape**. No live LLM in the acceptance suite.
- **Next step:** build after 310 (`ask`) and 312 (`ground`) — `clarify` composes
  the first and depends on the second to keep its questions sharp. `state` (324)
  and `replay` (325) later read the `CLARIFIES` edges this verb writes.
