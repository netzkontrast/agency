---
spec_id: "355"
slug: adr-definition-of-done-gate
status: draft
state: inprogress
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["354", "339"]
vision_goals: [3, 6]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/adr/_main.py
  - tests/acceptance/features/adr_dod.feature
  - tests/acceptance/test_adr_dod.py
---

# Spec 355 — ADR Definition-of-Done gate + governance lifecycle

> Child of **353**, builds on **354**. Ports SPEC-001-E (the extended Definition
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
| **C** Criteria | DOD-C01 | auto | ≥2 alternatives in `neglected` (reuses 354 `validate` WHY-003+) |
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
        (any approved) → superseded   (via adr.supersede, 354)
        (cadence lapsed) → expired     (automated review-cadence sweep)
```

`expired` is set by a cadence sweep (`adr.review_sweep()` — checks `next_review <
today`), reusing the same Lifecycle move. This makes governance *live*, not a
table that rots.

## Done When

### Slice 1 — dod_check + approve gate

- [x] `adr.dod_check` returns the eight ported criteria with correct mode and
      severity; the DOCUMENTATION check reuses 354 `validate` (no duplicated rule
      logic). `auto_passed` gates on `error`-severity auto/partial checks; `score`
      is surfaced, not gating (rule 8).
- [x] `adr.approve` blocks when an automated criterion fails (`{blocked, failing}`,
      no approval), pauses at the human criteria via `ctx.elicit` (falling back to
      `{input_required, pending}` with no host bound), recording a `Gate` node
      (`GATED_BY` the Decision) either way.
- [x] On owner confirmation the decision advances to `approved` (via `ctx.update`
      in Slice 1 — see the deferral note); the `Gate` is queryable provenance.
- [x] Owner override path records who/what (`dod-override` Gate); an agent
      self-approve / agent override is rejected (panel B2.1). Tested.

### Slice 2 — governance lifecycle + cadence (SHIPPED 2026-06-21, TDD)

- [x] Decision status is governed by the `decision` MACHINE (machines.json —
      `proposed→under-review→approved→implemented→retired`, +rejected/superseded/
      expired); illegal transitions are rejected (`DEC-001`) in `adr`'s own
      writers (`update`/`approve`/`supersede`).
- [x] `adr.review_sweep` flips overdue (`next_review < today`) approved/implemented
      decisions to `expired` (a legal transition); `next_review`/`review_cadence`
      are settable via `adr.update`.
- [x] Acceptance scenarios cover the illegal-transition rejection + the expiry
      sweep (behaviour, rule 7); the Slice-1 approval scenarios still green.

> **Design note (deviation from the literal spec, justified):** "status IS a
> Lifecycle" is honoured via the `decision` machine's transition TABLE enforced
> in the domain writers — NOT a separate Lifecycle node per Decision. A Decision
> already IS the bi-temporally-versioned tracked entity; a second tracking node
> would be the parallel-system smell `intent.brooks_lint` (Spec 359) flags. The
> machine is the single source of legal transitions; the decision's node history
> is the audit trail. (The generic-`manage` raw-write bypass stays possible but
> discouraged — the domain mutator `adr.update` is the enforced path.)

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

- **354** — reuses `validate`; same `adr` capability.
- **339 (lifecycle pillar)** — decision status IS a Lifecycle.
- **356/358** — the workflow's `/open → /inprogress` transition predicate is
  "all decisions extracted from this spec are `approved`" → this gate.
- **gate capability / CORE.md §elicit** — the human approval step.

## Followup — Implementation Status (2026-06-21)

### Done — Slice 1 (TDD, shipped)
- `adr.dod_check` — the eight SPEC-001-E criteria as decidable findings
  (E·C·A·D·D·R·Dp·Rf·M → DOD-E01/C01/A01/D01/D02/R01/DP01/DP02/RF01/M01), each
  tagged `auto` / `partial` / `human` with an `error`/`warn` severity. The
  DOCUMENTATION check **reuses 354 `validate`** (calls `self.validate(id).data.ok`
  — no duplicated WH(Y) rule logic, rule 2). `auto_passed` = every `error`-severity
  auto/partial check passes; `human_pending` = the partial/human ids; `score` is
  the SPEC-001-E fraction, surfaced not gating (rule 8).
- `adr.approve` — the hinge. Blocks on a failed automated `error` criterion
  (`{blocked, failing}`, status untouched); on automated pass with no `approver`
  tries `ctx.host.elicit` and falls back to `{input_required, pending}` when no
  host is bound (the deterministic test + remote-async path); an OWNER `approver`
  advances the decision to `approved`. Records a `Gate` node (`GATED_BY` the
  Decision, SERVES the intent) on every path. **Panel B2.1 enforced:** an agent
  (`approver="agent"` / empty identity on override) may NOT self-approve or
  self-override — only a human owner identity clears the gate; the provenance-
  stamped owner `override` is the escape hatch (records who + which `failing`).
- New edge `GATED_BY` (Decision→Gate) added to the adr ontology + traversed.
- **6 acceptance scenarios** (`tests/acceptance/features/adr_dod.feature`): auto
  pass + human-pending listed · blocked-on-auto-fail · owner confirm · owner
  override · agent-override rejected · no-approver input-required pause. adr+dod
  21 green; schema-coverage 44 green; check-drift clean (after install regen).

### Deferred to Slice 2 (deliberate scoping)
- **Status-as-a-Lifecycle (`ctx.lifecycle.move`) + the raw-`status=` write guard.**
  Slice 1 advances status via `ctx.update`, consistent with the already-shipped
  `adr.update`/`adr.supersede` (354 Slice 2) which also write `status` directly.
  Modelling a Decision's status as a Lifecycle machine and adding a guard that
  rejects raw `status=` writes is **architecturally significant** — it touches all
  three writers at once — so it belongs in one coherent Slice 2 change, not a
  half-done split. The DoD gate's *value* (decidable checks + owner-only approval
  + provenance) lands fully in Slice 1 regardless of the status-write mechanism.

### Still — Slice 2
- The full status Lifecycle (proposed→…→retired, +rejected/superseded/expired) as
  a walkable machine via `ctx.lifecycle.move`; the raw-write guard; reconcile
  `update`/`supersede`/`approve` onto the one state writer.
- `adr.review_sweep` (cadence → `expired`).
