---
spec_id: "328"
slug: typed-intent-fulfilment-gate
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["322", "326", "327"]
domain: intent
wave: program-master
parent_spec: "326"
---

# Spec 328 — Typed Intent fulfilment: the Intent-owned Gate + AcceptanceCriterion

> Slice 2 of Spec 326. Lands `Gate` and `AcceptanceCriterion` as **Intent-owned**
> tables — the typed home of *"is this intent fulfilled?"* (owner directive: the
> Gate lives in Intent because it captures fulfilment).

## Why

Spec 326 places the `Gate` under Intent, not Lifecycle: a gate is a recorded
verdict on *whether the intent is met* — at capture (the **clarity** gate we
already ship on `Intent.confirm`, Spec 322) and at done-time (the
**acceptance/completion** gate over the deliverable's criteria). The
`AcceptanceCriterion`s are the *definition* of fulfilled (the Spec 317 VALIDATES
checks). Giving both a typed, Intent-keyed home turns "are we there yet?" — the
question CORE.md's Intent row asks — into a typed row with a FK to its Intent and
a history of checks, rather than a transient score.

## Design

### Tables (`agency/_entities.py`, `table=True`; cite Spec 326)

```python
class AcceptanceCriterion(SQLModel, table=True):
    __tablename__ = "agency_acceptance_criterion"
    id: str = Field(primary_key=True)
    intent_id: str = Field(foreign_key="agency_intent.id", index=True)
    text: str
    gherkin: str | None = None
    measurable: bool = False                     # Spec 317 hard contract
    vfrom: int = 0
    vto: int = OPEN

class Gate(SQLModel, table=True):
    __tablename__ = "agency_gate"
    id: str = Field(primary_key=True)
    intent_id: str = Field(foreign_key="agency_intent.id", index=True)   # owned by Intent
    kind: str                                    # clarity | acceptance | completion
    status: str                                  # pending | passed | failed
    score: float | None = None                   # the clarity/fulfilment score at the check
    threshold: float | None = None
    checked_at: int = 0                           # the logical tick of the verdict
    vfrom: int = 0
    vto: int = OPEN
```

`kind`/`status` are ontology-sourced enums (rule 2; Spec 326 enum note). A `Gate`
row is **append-on-check**: each fulfilment check records a verdict, so the table
is the gate's *history* (when it was checked, the score, the verdict) — not a
single mutable flag.

### Wiring the gate we already ship (Spec 322)

`Intent.confirm(require_clarity=…)` (shipped) computes `clarity_score` via
`agency/_clarity.py` and gates. This slice has `confirm` (and the future
acceptance/completion checks) **record a `Gate` node** in the graph — which the
mirror (Spec 327 router, extended for these labels) projects to the typed `Gate`
table. So the gate verdict becomes durable + queryable: *"show every fulfilment
check for intent Q and how its clarity rose to pass."* No second source — the
score still comes from `_clarity.clarity_score` (rule 4); the `Gate` row is its
recorded outcome.

### Fulfilment as a join

"Is intent Q fulfilled?" is now a typed query: its latest `acceptance`/`completion`
`Gate.status == passed`, AND every `AcceptanceCriterion` with `measurable=True`
is satisfied. The `AcceptanceCriterion` rows make *what fulfilled means* explicit
and FK-linked, so the read API (Spec 330) answers fulfilment without Cypher.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Gate is Intent-owned:** every `Gate` row has a non-null `intent_id` resolving
  to a real `Intent` — no gate floats free of an intent (the directive).
- **Confirm records a clarity Gate:** confirming an Intent writes a `Gate` row
  with `kind="clarity"` whose `score` equals `_clarity.clarity_score` for that
  Intent (the shipped scorer is the single source — rule 4).
- **Gate history accrues:** re-checking an Intent after resolving a signal adds a
  new `Gate` row with a higher `score` and a `passed` verdict — monotone in the
  resolved signals, computed live (not a pinned score).
- **AcceptanceCriterion VALIDATES parity:** each `AcceptanceCriterion` row's
  `intent_id` equals the target of its graph `VALIDATES` edge (Spec 317) — typed
  column and edge agree.
- **Fulfilment join:** an Intent with a `passed` acceptance `Gate` and all
  `measurable` criteria satisfied reads "fulfilled" via the join; remove the gate
  and it flips — the verdict tracks the live rows.

## Acceptance

"Is this intent fulfilled?" is a first-class, Intent-owned, typed record: `Gate`
rows (clarity at capture, acceptance/completion at done-time) keyed to their
`Intent`, plus the `AcceptanceCriterion`s that define fulfilment — all mirrored
one-way from the authoritative graph, the clarity score still sourced from
`agency/_clarity.py`.

## Followup — Implementation Status (2026-06-19)

- **Status: draft.** Slice 2 — the fulfilment layer. Depends on Slice 327's
  `Intent` table + mirror router. Reuses the shipped Spec 322 `_clarity` scorer
  (no second source).
- **Open question (resolve at build):** whether the `acceptance`/`completion`
  gate fires automatically (e.g. on a Lifecycle `completed` transition, Spec 329)
  or only on an explicit check. Default: explicit check now; auto-fire on the
  `completed` transition is a follow-up once Lifecycle states are typed (329).
