---
spec_id: "309"
slug: elicitation-interview-engine
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 8]
depends_on: ["029", "147", "262", "307", "308", "310"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 309 — Elicitation interview engine (`discover.interview`)

> Child of the intent-pillar deep program (Spec 307), the **guided-exploration**
> layer. This is the adaptive AskUser beat-chain that turns a one-line seed into
> a grounded *draft* Intent — the engine Spec 307's flow opens with
> (`seed ──► interview ──► [draft Intent]`).

## Why

**The gap (Spec 307 §"Why").** An Intent is born shallow: a user types one
sentence, `intent_bootstrap` (Spec 029) or the `/agency-onboard` 4-beat script
(Spec 262) mints a `{purpose, deliverable, acceptance}` node, and work begins.
There is **no guided exploration** before the WHY is recorded. Spec 262 saw the
shape — wrapping the managed-agents `describe → configure → environment →
session` pattern as a capability — but stayed a **fixed 4-beat interview**: the
same four questions regardless of what the user already said. A fixed script
asks beat 3 even when beat 2's answer made it moot, and never asks the sharp
follow-up the answer implied.

**This spec generalizes 262's insight into the adaptive engine** Spec 307
§"thesis" calls for: each beat asks ONE well-formed question, captures the
verbatim answer, and **derives the next beat's question from the prior
answers**. The adaptivity is the whole point — it is the difference between a
guess and a discovery (Spec 307 §"thesis"). Per the coverage matrix (Spec 307),
this child exercises the **AskUser tool-call chain** and the **Driver seam**
(Spec 147) and is the primary writer of `DiscoverySession` / `ElicitationTurn`.

**Doctrine.** CORE.md names Intent the **human-owned root** that everything
edges back to via `SERVES`. If the root is vague, every downstream `SERVES` edge
inherits the vagueness. The interview is where the human stays creative and the
engine captures everything (Goal 8, harness-in-harness) — and every captured
turn is a graph node (Goal 2, the provenance moat: *how the WHY was
discovered*, not just *what was done*).

**Supersession note.** This generalizes Spec 262's `intent.managed_onboard`
4-beat into the adaptive `discover.interview`; the `/agency-onboard` command
re-routes here (262's command surface is retained as a thin alias, its 4-beat
becomes the `interview-beats.json` seed library — see Design). 262 is not
deleted; it is *absorbed* and its row in `TODO.md` flips to "superseded by 309".

## Design

**Cluster module:** `agency/capabilities/discover/clusters/interview.py`
(the `InterviewCluster` mixin `DiscoverCapability` composes, per Spec 308's
cluster-mixin pattern; shared helpers from `clusters/_base.py`).

**Verb:** `discover.interview(seed: str, max_beats: int = 6)` — `role="act"`
(writes; per Spec 307 §coherence rule 3 the act verbs are the writers).

```python
class InterviewOutcome(TypedDict):
    session_id: str            # the DiscoverySession node
    intent_id: str            # the DRAFT Intent (status="draft")
    beats: list[TurnRecord]   # the ElicitationTurns, in order
    terminated_by: str        # "complete" | "max_beats"
    clarity_inputs: dict      # the signal bag Spec 322's clarity score reads

class TurnRecord(TypedDict):
    turn_id: str              # the ElicitationTurn node id
    beat: int                 # 1-indexed
    kind: str                 # turn_kind enum (Spec 307)
    question: str             # the well-formed question shown (from discover.ask)
    answer: str               # the user's VERBATIM answer (folded back by caller)
```

**The adaptive beat-chain.** The verb runs a loop, up to `max_beats`:

1. **Open a session.** `_session(seed)` (from `_base.py`) records a
   `DiscoverySession` node (`seed`, `status="open"`, `clarity_score=0`) — the
   spine the turns hang off.
2. **Pick the beat.** Beat 1 is always a `describe` beat (drawn from
   `data/interview-beats.json`, the adaptive beat library that supersedes 262's
   fixed four). The `turn_kind` enum (Spec 307) gates progression:
   `describe → configure → constrain → ground → clarify → confirm`. The library
   maps each kind to a question *template* and the precondition that selects it.
3. **Derive the question.** The next beat's question is computed from the prior
   answers — this is the **Driver seam** (Spec 147 structured-output): given the
   session-so-far, the Driver returns the next `{kind, question_context}`. The
   call is **behind a typed shape** (`NextBeat` TypedDict); when no Driver is
   injected (`Engine(driver=None)`), a **deterministic fallback** walks the
   beat library in enum order and fills the template from the prior answers —
   the verb is fully exercised in tests with zero LLM (Spec 308 / wet-LLM
   pattern).
4. **Ask it.** The actual one-question payload is built by **`discover.ask`**
   (Spec 310) — `interview` never hand-rolls a question; it composes the
   primitive. `ask` returns the `AskUserQuestion`-shaped payload; the **harness**
   renders it; the caller folds the verbatim answer back into the next loop turn.
5. **Record the turn.** `_record_turn(session_id, beat, kind, question, answer)`
   records an `ElicitationTurn` node (`beat`, `kind`, `question`, `answer`) and
   the **`ELICITS`** edge `DiscoverySession → ElicitationTurn` (Spec 307
   ontology — declare an edge ⇒ traverse it, per the dormant-surface audit; the
   loop reads prior turns via `ctx.neighbors(session_id, "ELICITS")`).

**Termination.** The loop stops when **either** the accumulated answers yield a
complete `{purpose, deliverable, acceptance}` triple (`terminated_by="complete"`)
**or** `max_beats` is hit (`terminated_by="max_beats"`). Completeness is read
from `_clarity_inputs` — not a beat count — so a sharp user finishes in 3 beats
and a vague one runs the budget.

**Produce the draft Intent.** On termination, the verb mints a **draft** Intent
via the substrate `intent.capture` (Spec 029) with `status="draft"` — **not
confirmed**. Confirmation waits for the clarity gate (Spec 322); `interview`
deliberately never confirms (Spec 307 rule 3 / the flow diagram). It records the
**`DISCOVERED`** edge `DiscoverySession → Intent` (Spec 307 ontology) so the
session that captured this Intent is replayable (Spec 325).

**Composition.** `interview` READS nothing it can recompute and reuses every
sibling: `discover.ask` (310) for the payload, `intent.capture` (substrate) for
the node, `_base.py` helpers for recording. It WRITES `DiscoverySession`,
`ElicitationTurn`, `ELICITS`, `DISCOVERED`, and the draft Intent.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Turn-count invariant:** the number of `ElicitationTurn` nodes with an
  `ELICITS` edge from the session **equals** the number of beats the run
  reports (`len(outcome["beats"])`) — computed from the live graph census, never
  a pinned count. (Spec 307 rule 5: turn-count == beats elicited.)
- **Adaptivity (not a fixed 4):** with two different seed+answer sequences, the
  derived question of beat *n+1* differs when beat *n*'s answer differs — assert
  the beat-2 question text is a function of the beat-1 answer (deterministic
  fallback makes this reproducible without an LLM).
- **Draft, not confirmed:** the produced Intent has `status == "draft"` and is
  reachable from the session via `DISCOVERED` — assert `intent.status != "confirmed"`
  and the edge exists; the clarity gate (322) owns confirmation.
- **Termination is data-driven:** a seed whose answers complete the triple early
  terminates with `terminated_by == "complete"` and `len(beats) < max_beats`; a
  vague run terminates with `terminated_by == "max_beats"` and exactly
  `max_beats` turns — both computed, not pinned.
- **Driver seam is optional:** the verb runs to completion with `driver=None`
  (deterministic fallback) AND with a stub Driver returning a typed `NextBeat`;
  both paths record the same node/edge surface (the seam never leaks).
- **Provenance whole (Goal 2):** every turn carries a verbatim non-empty
  `answer`, and the session → turns → Intent subgraph is fully connected — the
  replay precondition Spec 325 asserts against.

## Acceptance

An agent (or the harness) hands `discover.interview` a one-line seed and a way
to render AskUser questions, and walks away with a **draft Intent grounded in a
recorded, adaptive interview**: each beat asked one sharp question derived from
the last answer, every answer captured verbatim as an `ElicitationTurn`, and the
whole session replayable from the graph. The `/agency-onboard` command now
routes here, and the fixed 4-beat (262) becomes one seed path through the
adaptive engine.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Guided-exploration core of the Spec 307 program;
  **Slice-1-typed-shape-first** — land `InterviewOutcome` / `TurnRecord` /
  `NextBeat` as the typed contract with the **deterministic beat-library
  fallback** wired and fully tested, and the **AskUser render + LLM
  next-question Driver seam (Spec 147) behind the typed shape** (the harness
  renders, the caller folds the answer; no live LLM in the acceptance suite).
- **Next step:** build after 308 (scaffold) + 310 (the `ask` primitive it
  composes). Then 311 (`clarify`) reuses the same `_record_turn` /
  `ElicitationTurn` surface for its targeted questions, and 262's
  `intent.managed_onboard` is re-pointed to this verb with its 4-beat seeded
  into `interview-beats.json`.
