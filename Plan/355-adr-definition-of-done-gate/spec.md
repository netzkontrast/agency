---
spec_id: "355"
slug: adr-definition-of-done-gate
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["360", "339"]
vision_goals: [3, 6]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/adr/_main.py
  - tests/acceptance/features/adr_dod.feature
  - tests/acceptance/test_adr_dod.py
---

# Spec 355 — ADR Definition-of-Done gate + governance lifecycle

> Child of **353**, builds on **360**. Ports SPEC-001-E (the extended Definition
> of Done — ECADR + Dp/Rf/M) as a real **Gate**, and models a decision's status
> progression as a **Lifecycle**. This is the gate 356/358 require before a spec
> may leave `/open`.

## Why

SPEC-001-E defines a *pre-approval gate*: an ADR cannot become **Approved** until
the Definition of Done is satisfied (`adr approve` runs automated checks and
blocks on failure). agency already has the right primitive — a **Gate is an
`elicit` step** (CORE.md §"Gates / human-in-the-loop are elicit steps"): the
automated checks decide what they can decide, and a human confirms the rest. This
spec makes "approved" *mean something* — it is the hinge of the whole workflow:
no spec advances to `/inprogress` until its decisions clear this gate (356/358).

## Design

### The DoD checklist, ported (SPEC-001-E)

Eight criteria. Each maps to a check that is **automated**, **partial**, or
**human** — exactly as SPEC-001-E classifies them:

| Criterion | Check id | Mode | How agency decides it |
|---|---|---|---|
| **E** Evidence | DOD-E01 | partial | context/`facing` references a PoC/prior-art (heuristic) + human confirm |
| **C** Criteria | DOD-C01 | auto | ≥2 alternatives in `neglected` (reuses 360 `validate` WHY-003+) |
| **A** Agreement | DOD-A01 | partial | governance fields populated + human confirm |
| **D** Documentation | DOD-D01/02 | auto | WH(Y) `validate` passes; theme Document exists & published |
| **R** Realization/Review | DOD-R01 | auto | `review_cadence` set; `next_review` computed |
| **Dp** Dependencies | DOD-DP01/02 | auto | has dependency edges; no `DEP-001` cycle |
| **Rf** References | DOD-RF01/02 | auto | every `REFINES`/`RELATES_TO` target resolves to a live node |
| **M** Master | DOD-M01 | auto | `PART_OF` an `AdrTheme` (always true in our thematic model) |

### Verb: `dod_check(decision_id)` — role `transform`

Runs every automated + partial check, returns:

```
{decision_id, criteria: [{id, criterion, mode, passed, severity, msg}],
 auto_passed: bool, human_pending: [DOD-E01, DOD-A01], score: 0.0-1.0}
```

`score` is the **optional** SPEC-001-E scoring model (weighted), surfaced but not
gating by default (Approved ≥ 0.8 is documented config, not hardcoded — rule 8).
This verb is pure compute; it never flips status.

### Verb: `approve(decision_id, confirm_token="")` — role `act` (the Gate)

1. Calls `dod_check`. If `auto_passed` is false → return `input-required` with the
   failing criteria (the decision **cannot** be approved; SPEC-001-E pre-approval
   gate). No silent pass.
2. If automated checks pass but `human_pending` is non-empty → `ctx.elicit` the
   human approver (Evidence/Agreement). The Lifecycle pauses at `input-required`;
   the answer resumes it. Records a **`Gate`** node (passed/failed + approver +
   the pending criteria answered) `SERVES` the intent.
3. On confirmation → advance the decision Lifecycle `proposed/under-review →
   approved` via `ctx.lifecycle.move` (Spec 339), append `status_history`,
   record provenance.

A provenance-stamped **owner override** is permitted (records *who* overrode and
*which* criteria) — fragility response: the gate must never become an immovable
wall (353 failure-mode table).

### Status as a Lifecycle (SPEC-001-A status set)

A `Decision`'s `status` is not a free field that verbs poke — it is a Lifecycle
the `adr` verbs drive through `ctx.lifecycle`:

```
proposed → under-review → approved → implemented → retired
                       ↘ rejected
        (any approved) → superseded   (via adr.supersede, 360)
        (cadence lapsed) → expired     (automated review-cadence sweep)
```

`expired` is set by a cadence sweep (`adr.review_sweep()` — checks `next_review <
today`), reusing the same Lifecycle move. This makes governance *live*, not a
table that rots.

## Done When

### Slice 1 — dod_check + approve gate

- [ ] `adr.dod_check` returns the eight ported criteria with correct mode and
      severity; auto checks reuse 360 `validate` (no duplicated rule logic).
- [ ] `adr.approve` blocks when an automated criterion fails (returns
      `input-required` naming the failure), and pauses at the human criteria via
      `ctx.elicit`, recording a `Gate` node either way.
- [ ] On confirm, the decision advances to `approved` through `ctx.lifecycle.move`;
      the transition is queryable provenance.
- [ ] Owner override path records who/what; tested.

### Slice 2 — governance lifecycle + cadence

- [ ] The full status Lifecycle (proposed→…→retired, +rejected/superseded/expired)
      is walkable; illegal transitions are rejected.
- [ ] `adr.review_sweep` flips overdue decisions to `expired` and records it.
- [ ] Acceptance scenarios cover a green approval, a blocked approval, a
      human-pending approval, and an expiry sweep (behaviour, rule 7).

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| DoD gate needs an LLM/API key → unusable offline | All gating checks are **decidable**; the only human step is `ctx.elicit` (no key) |
| Scoring threshold frozen as a magic number | Threshold is documented config (`adr.dod.approve_score`), default 0.8, overridable (rule 8) |
| Gate too strict → no spec ever reaches `/inprogress` | Provenance-stamped owner override; gate predicate is "decisions approved", not "perfect" |
| `status` mutated directly, bypassing the Lifecycle | Status writes only via `ctx.lifecycle.move`; a guard rejects raw `status=` updates on `Decision` |

## Spec-panel findings folded in (panel 2026-06-20)

- **B2.1 (Cockburn/Nygard — approver identity):** the normal approver is the
  **intent owner** (`Intent` is human-owned, CORE.md §Intent). In an autonomous
  remote-async session with no owner present, `adr.approve` pauses at
  `input-required` and the decision (and the spec's `SpecLifecycle`) **stays in
  place** — it never auto-approves, and the **agent may not self-approve**. The
  provenance-stamped override is the *owner's* escape hatch only; an override
  records the owner identity, so an agent-issued override is detectable and
  rejected. This keeps the hinge a real gate, not a rubber stamp, while never
  silently deadlocking (the owner sees the pending approval via `manage`/`board`).

## Interconnects

- **360** — reuses `validate`; same `adr` capability.
- **339 (lifecycle pillar)** — decision status IS a Lifecycle.
- **356/358** — the workflow's `/open → /inprogress` transition predicate is
  "all decisions extracted from this spec are `approved`" → this gate.
- **gate capability / CORE.md §elicit** — the human approval step.

## Followup — Implementation Status (2026-06-20)

### Done
- Spec authored (design depth).

### Still
- Implement Slice 1 (dod_check + approve) then Slice 2 (lifecycle + cadence) via TDD.
